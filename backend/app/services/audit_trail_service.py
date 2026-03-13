"""
Audit Trail Writer Service (Phase 3)
Writes audit records for all policy changes
"""

from typing import List, Optional, Dict
import logging
from config import config

logger = logging.getLogger(__name__)


class AuditTrailWriter:
    """
    Service to write audit trail records for policy changes
    Provides full traceability and rollback capability
    """
    
    def __init__(self, audit_repo=None):
        """
        Initialize Audit Trail Writer
        
        Args:
            audit_repo: PolicyChangeAuditRepository instance
        """
        self.audit_repo = audit_repo
        self.enabled = config.ENABLE_POLICY_UNLEARNING
    
    async def write_change_audit(
        self,
        ticket_id: str,
        change_type: str,
        old_chunk_ids: List[str],
        new_chunk_ids: List[str],
        affected_doc_ids: List[str],
        executed_by: str,
        reason: str,
        source_reference: Optional[str] = None,
        embedding_job_id: Optional[str] = None,
        rollback_pointer: Optional[str] = None
    ) -> Optional[str]:
        """
        Write a new audit record
        
        Args:
            ticket_id: Associated policy update ticket ID
            change_type: "deprecate", "add", "update", "rollback"
            old_chunk_ids: List of deprecated chunk IDs
            new_chunk_ids: List of new chunk IDs
            affected_doc_ids: List of affected document IDs
            executed_by: User ID who executed the change
            reason: Reason for the change
            source_reference: Optional policy source reference
            embedding_job_id: Optional background job ID
            rollback_pointer: Previous audit_id for rollback capability
            
        Returns:
            audit_id if successful, None otherwise
        """
        if not self.enabled:
            logger.warning("Audit trail writing disabled (feature flag off)")
            return None
        
        if not self.audit_repo:
            logger.error("Audit repository not available")
            return None
        
        try:
            audit_id = await self.audit_repo.write_audit_record(
                ticket_id=ticket_id,
                change_type=change_type,
                old_chunk_ids=old_chunk_ids,
                new_chunk_ids=new_chunk_ids,
                affected_doc_ids=affected_doc_ids,
                executed_by=executed_by,
                reason=reason,
                source_reference=source_reference,
                embedding_job_id=embedding_job_id,
                rollback_pointer=rollback_pointer
            )
            
            logger.info(f"Audit record created: {audit_id}")
            return audit_id
            
        except Exception as e:
            logger.error(f"Failed to write audit record: {e}")
            return None
    
    async def write_deprecation_audit(
        self,
        ticket_id: str,
        deprecated_chunk_ids: List[str],
        doc_ids: List[str],
        executed_by: str,
        reason: str
    ) -> Optional[str]:
        """
        Convenience method for deprecation audit
        
        Args:
            ticket_id: Ticket ID
            deprecated_chunk_ids: Chunks that were deprecated
            doc_ids: Affected document IDs
            executed_by: User ID
            reason: Deprecation reason
            
        Returns:
            audit_id if successful
        """
        return await self.write_change_audit(
            ticket_id=ticket_id,
            change_type="deprecate",
            old_chunk_ids=deprecated_chunk_ids,
            new_chunk_ids=[],
            affected_doc_ids=doc_ids,
            executed_by=executed_by,
            reason=reason
        )
    
    async def write_addition_audit(
        self,
        ticket_id: str,
        new_chunk_ids: List[str],
        doc_ids: List[str],
        executed_by: str,
        reason: str,
        embedding_job_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Convenience method for addition audit
        
        Args:
            ticket_id: Ticket ID
            new_chunk_ids: Newly added chunks
            doc_ids: Affected document IDs
            executed_by: User ID
            reason: Addition reason
            embedding_job_id: Re-embedding job ID
            
        Returns:
            audit_id if successful
        """
        return await self.write_change_audit(
            ticket_id=ticket_id,
            change_type="add",
            old_chunk_ids=[],
            new_chunk_ids=new_chunk_ids,
            affected_doc_ids=doc_ids,
            executed_by=executed_by,
            reason=reason,
            embedding_job_id=embedding_job_id
        )
    
    async def write_update_audit(
        self,
        ticket_id: str,
        old_chunk_ids: List[str],
        new_chunk_ids: List[str],
        doc_ids: List[str],
        executed_by: str,
        reason: str,
        source_reference: Optional[str] = None,
        embedding_job_id: Optional[str] = None,
        rollback_pointer: Optional[str] = None
    ) -> Optional[str]:
        """
        Convenience method for full update audit (deprecate + add)
        
        Args:
            ticket_id: Ticket ID
            old_chunk_ids: Deprecated chunks
            new_chunk_ids: New chunks
            doc_ids: Affected document IDs
            executed_by: User ID
            reason: Update reason
            source_reference: Policy source reference
            embedding_job_id: Re-embedding job ID
            rollback_pointer: Previous audit ID for rollback
            
        Returns:
            audit_id if successful
        """
        return await self.write_change_audit(
            ticket_id=ticket_id,
            change_type="update",
            old_chunk_ids=old_chunk_ids,
            new_chunk_ids=new_chunk_ids,
            affected_doc_ids=doc_ids,
            executed_by=executed_by,
            reason=reason,
            source_reference=source_reference,
            embedding_job_id=embedding_job_id,
            rollback_pointer=rollback_pointer
        )
    
    async def write_rollback_audit(
        self,
        original_audit_id: str,
        ticket_id: str,
        reactivated_chunk_ids: List[str],
        deprecated_chunk_ids: List[str],
        doc_ids: List[str],
        executed_by: str,
        reason: str
    ) -> Optional[str]:
        """
        Convenience method for rollback audit
        
        Args:
            original_audit_id: Audit ID being rolled back
            ticket_id: Associated ticket ID
            reactivated_chunk_ids: Chunks being reactivated
            deprecated_chunk_ids: Chunks being deprecated in rollback
            doc_ids: Affected document IDs
            executed_by: User ID
            reason: Rollback reason
            
        Returns:
            audit_id if successful
        """
        return await self.write_change_audit(
            ticket_id=ticket_id,
            change_type="rollback",
            old_chunk_ids=deprecated_chunk_ids,  # New chunks being deprecated
            new_chunk_ids=reactivated_chunk_ids,  # Old chunks being reactivated
            affected_doc_ids=doc_ids,
            executed_by=executed_by,
            reason=f"Rollback of audit {original_audit_id}: {reason}",
            rollback_pointer=original_audit_id
        )
    
    async def verify_audit_record(
        self,
        audit_id: str,
        verification_status: str,
        notes: Optional[str] = None
    ) -> bool:
        """
        Update verification status of an audit record
        
        Args:
            audit_id: Audit record ID
            verification_status: "verified", "failed"
            notes: Optional verification notes
            
        Returns:
            True if updated successfully
        """
        if not self.enabled or not self.audit_repo:
            return False
        
        try:
            success = await self.audit_repo.update_verification_status(
                audit_id=audit_id,
                status=verification_status,
                notes=notes
            )
            
            if success:
                logger.info(f"Audit {audit_id} verification updated: {verification_status}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to verify audit record: {e}")
            return False


# Singleton instance (will be initialized with actual audit_repo)
audit_trail_writer = AuditTrailWriter()
