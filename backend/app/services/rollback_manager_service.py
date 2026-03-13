"""
Rollback Manager Service (Phase 3)
Manages rollback of policy changes to previous versions
"""

from typing import Optional, Dict
import logging
from config import config

logger = logging.getLogger(__name__)


class RollbackManager:
    """
    Service to manage rollback of policy changes
    Restores previous policy versions by reactivating old chunks
    and deprecating new ones
    """
    
    def __init__(
        self,
        audit_repo=None,
        chunk_deprecation_service=None,
        policy_docs_repo=None
    ):
        """
        Initialize Rollback Manager
        
        Args:
            audit_repo: PolicyChangeAuditRepository instance
            chunk_deprecation_service: ChunkDeprecationService instance
            policy_docs_repo: PolicyDocumentsRepository instance
        """
        self.audit_repo = audit_repo
        self.chunk_deprecation_service = chunk_deprecation_service
        self.policy_docs_repo = policy_docs_repo
        self.enabled = config.ENABLE_POLICY_UNLEARNING
    
    async def rollback_to_version(
        self,
        audit_id: str,
        executed_by: str,
        reason: str,
        confirmation: str
    ) -> Dict:
        """
        Rollback a policy change to its previous version
        
        Args:
            audit_id: Audit ID of the change to rollback
            executed_by: User ID performing the rollback
            reason: Reason for rollback
            confirmation: Must be "CONFIRM ROLLBACK" for safety
            
        Returns:
            {
                "success": bool,
                "restored_version": int | None,
                "rollback_audit_id": str | None,
                "message": str
            }
        """
        if not self.enabled:
            logger.warning("Rollback disabled (feature flag off)")
            return {
                "success": False,
                "restored_version": None,
                "rollback_audit_id": None,
                "message": "Feature disabled"
            }
        
        # Safety check: Require explicit confirmation
        if confirmation != "CONFIRM ROLLBACK":
            return {
                "success": False,
                "restored_version": None,
                "rollback_audit_id": None,
                "message": "Rollback confirmation required. Please provide 'CONFIRM ROLLBACK'."
            }
        
        # Validate dependencies
        if not all([self.audit_repo, self.chunk_deprecation_service, self.policy_docs_repo]):
            return {
                "success": False,
                "restored_version": None,
                "rollback_audit_id": None,
                "message": "Required services not available"
            }
        
        try:
            # Step 1: Fetch the original audit record
            audit_record = await self.audit_repo.get_audit_by_id(audit_id)
            
            if not audit_record:
                return {
                    "success": False,
                    "restored_version": None,
                    "rollback_audit_id": None,
                    "message": f"Audit record {audit_id} not found"
                }
            
            logger.info(f"Starting rollback of audit {audit_id}")
            
            # Step 2: Extract change information
            old_chunk_ids = audit_record.get("old_chunk_ids", [])
            new_chunk_ids = audit_record.get("new_chunk_ids", [])
            affected_doc_ids = audit_record.get("affected_doc_ids", [])
            ticket_id = audit_record.get("ticket_id")
            
            # Step 3: Reactivate old chunks (that were deprecated)
            reactivate_result = await self.chunk_deprecation_service.reactivate_chunks(
                chunk_ids=old_chunk_ids,
                reason=f"Rollback: {reason}",
                audit_id=f"ROLLBACK-{audit_id}",
                reactivated_by=executed_by
            )
            
            if not reactivate_result.get("success"):
                return {
                    "success": False,
                    "restored_version": None,
                    "rollback_audit_id": None,
                    "message": f"Failed to reactivate old chunks: {reactivate_result.get('message')}"
                }
            
            logger.info(f"Reactivated {reactivate_result['reactivated_count']} chunks")
            
            # Step 4: Deprecate new chunks (that were added in the change)
            deprecate_result = await self.chunk_deprecation_service.deprecate_chunks(
                chunk_ids=new_chunk_ids,
                reason=f"Rollback: {reason}",
                audit_id=f"ROLLBACK-{audit_id}",
                deprecated_by=executed_by
            )
            
            if not deprecate_result.get("success"):
                logger.warning(f"Partial rollback: failed to deprecate new chunks")
            
            logger.info(f"Deprecated {deprecate_result['deprecated_count']} chunks")
            
            # Step 5: Update policy document status (mark as deprecated, reactivate previous)
            restored_version = None
            for doc_id in affected_doc_ids:
                try:
                    # Get the previous active version
                    previous_version = await self._find_previous_version(doc_id, audit_record)
                    
                    if previous_version:
                        # Reactivate previous version in policy_documents collection
                        await self.policy_docs_repo.update_policy_status(
                            document_id=previous_version["_id"],
                            new_status="active",
                            updated_by=executed_by
                        )
                        restored_version = previous_version.get("version")
                        logger.info(f"Restored {doc_id} to version {restored_version}")
                
                except Exception as e:
                    logger.error(f"Error updating policy document {doc_id}: {e}")
            
            # Step 6: Write rollback audit record
            rollback_audit_id = await self.audit_repo.write_audit_record(
                ticket_id=ticket_id or "ROLLBACK",
                change_type="rollback",
                old_chunk_ids=new_chunk_ids,  # Chunks being deprecated
                new_chunk_ids=old_chunk_ids,  # Chunks being reactivated
                affected_doc_ids=affected_doc_ids,
                executed_by=executed_by,
                reason=f"Rollback of {audit_id}: {reason}",
                rollback_pointer=audit_id
            )
            
            logger.info(f"Rollback completed: {rollback_audit_id}")
            
            return {
                "success": True,
                "restored_version": restored_version,
                "rollback_audit_id": rollback_audit_id,
                "message": f"Successfully rolled back to previous version. Audit: {rollback_audit_id}"
            }
            
        except Exception as e:
            logger.error(f"Error during rollback: {e}")
            return {
                "success": False,
                "restored_version": None,
                "rollback_audit_id": None,
                "message": f"Rollback failed: {str(e)}"
            }
    
    async def _find_previous_version(
        self,
        doc_id: str,
        current_audit: Dict
    ) -> Optional[Dict]:
        """
        Find the previous active version before the change
        
        Args:
            doc_id: Document ID
            current_audit: Current audit record
            
        Returns:
            Previous policy document version or None
        """
        try:
            # Get all versions of the document
            versions = await self.policy_docs_repo.get_all_versions(doc_id, limit=10)
            
            # Find the version that was active before this change
            change_timestamp = current_audit.get("timestamp")
            
            for version in versions:
                if version.get("created_at") < change_timestamp:
                    return version
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding previous version: {e}")
            return None
    
    async def can_rollback(self, audit_id: str) -> Dict:
        """
        Check if an audit record can be rolled back
        
        Args:
            audit_id: Audit ID to check
            
        Returns:
            {
                "can_rollback": bool,
                "reason": str
            }
        """
        if not self.enabled:
            return {
                "can_rollback": False,
                "reason": "Feature disabled"
            }
        
        try:
            # Fetch audit record
            audit_record = await self.audit_repo.get_audit_by_id(audit_id)
            
            if not audit_record:
                return {
                    "can_rollback": False,
                    "reason": "Audit record not found"
                }
            
            # Check if already rolled back
            if audit_record.get("change_type") == "rollback":
                return {
                    "can_rollback": False,
                    "reason": "Cannot rollback a rollback operation"
                }
            
            # Check if there's a subsequent rollback
            subsequent_rollbacks = await self.audit_repo.search_audits(
                {"rollback_pointer": audit_id},
                limit=1
            )
            
            if subsequent_rollbacks:
                return {
                    "can_rollback": False,
                    "reason": "This change has already been rolled back"
                }
            
            return {
                "can_rollback": True,
                "reason": "Can be rolled back"
            }
            
        except Exception as e:
            logger.error(f"Error checking rollback eligibility: {e}")
            return {
                "can_rollback": False,
                "reason": f"Error: {str(e)}"
            }


# Singleton instance (will be initialized with actual dependencies)
rollback_manager = RollbackManager()
