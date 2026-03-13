"""
Policy Update Executor Service (Phase 3)
Orchestrates the full policy update workflow after approval
"""

from typing import Dict, Optional
import logging
from datetime import datetime
from config import config

logger = logging.getLogger(__name__)


class PolicyUpdateExecutor:
    """
    Orchestrates the complete policy update workflow
    
    Workflow:
    1. Fetch approved ticket details
    2. Deprecate old chunks in ChromaDB
    3. Re-embed new policy text
    4. Update policy_documents collection
    5. Write audit trail
    6. Mark ticket as implemented
    """
    
    def __init__(
        self,
        tickets_repo=None,
        policy_docs_repo=None,
        chunk_deprecation_service=None,
        policy_reembedding_service=None,
        audit_trail_writer=None
    ):
        """
        Initialize Policy Update Executor
        
        Args:
            tickets_repo: PolicyUpdateTicketsRepository
            policy_docs_repo: PolicyDocumentsRepository
            chunk_deprecation_service: ChunkDeprecationService
            policy_reembedding_service: PolicyReembeddingService
            audit_trail_writer: AuditTrailWriter
        """
        self.tickets_repo = tickets_repo
        self.policy_docs_repo = policy_docs_repo
        self.chunk_deprecation_service = chunk_deprecation_service
        self.policy_reembedding_service = policy_reembedding_service
        self.audit_trail_writer = audit_trail_writer
        self.enabled = config.ENABLE_POLICY_UNLEARNING
    
    async def execute_approved_update(
        self,
        ticket_id: str,
        reviewer_id: str,
        new_policy_text: Optional[str] = None,
        source_reference: Optional[str] = None
    ) -> Dict:
        """
        Execute an approved policy update
        
        Args:
            ticket_id: Approved ticket ID
            reviewer_id: User ID of reviewer/executor
            new_policy_text: New policy text (if applicable)
            source_reference: Policy source reference (circular, memo, etc.)
            
        Returns:
            {
                "success": bool,
                "audit_id": str | None,
                "new_version": int | None,
                "message": str,
                "details": dict
            }
        """
        if not self.enabled:
            logger.warning("Policy update executor disabled (feature flag off)")
            return {
                "success": False,
                "audit_id": None,
                "new_version": None,
                "message": "Feature disabled",
                "details": {}
            }
        
        # Validate dependencies
        if not all([
            self.tickets_repo,
            self.policy_docs_repo,
            self.chunk_deprecation_service,
            self.audit_trail_writer
        ]):
            return {
                "success": False,
                "audit_id": None,
                "new_version": None,
                "message": "Required services not available",
                "details": {}
            }
        
        details = {
            "deprecated_chunks": 0,
            "new_chunks": 0,
            "affected_docs": []
        }
        
        try:
            logger.info(f"Starting policy update execution for ticket {ticket_id}")
            
            # Step 1: Fetch ticket details
            ticket = await self.tickets_repo.get_ticket_by_id(ticket_id)
            
            if not ticket:
                return {
                    "success": False,
                    "audit_id": None,
                    "new_version": None,
                    "message": f"Ticket {ticket_id} not found",
                    "details": details
                }
            
            if ticket.get("status") != "approved":
                return {
                    "success": False,
                    "audit_id": None,
                    "new_version": None,
                    "message": f"Ticket must be approved (current status: {ticket.get('status')})",
                    "details": details
                }
            
            # Extract affected chunks and documents
            affected_chunks = ticket.get("affected_chunks", [])
            old_chunk_ids = [chunk.get("chunk_id") for chunk in affected_chunks if chunk.get("chunk_id")]
            affected_doc_ids = list(set([chunk.get("doc_id") for chunk in affected_chunks if chunk.get("doc_id")]))
            
            details["affected_docs"] = affected_doc_ids
            
            # Step 2: Deprecate old chunks
            logger.info(f"Deprecating {len(old_chunk_ids)} old chunks")
            
            deprecation_result = await self.chunk_deprecation_service.deprecate_chunks(
                chunk_ids=old_chunk_ids,
                reason=f"Policy update from ticket {ticket_id}",
                audit_id=f"PENDING-{ticket_id}",
                deprecated_by=reviewer_id
            )
            
            if not deprecation_result.get("success"):
                logger.error(f"Deprecation failed: {deprecation_result.get('message')}")
                return {
                    "success": False,
                    "audit_id": None,
                    "new_version": None,
                    "message": f"Failed to deprecate old chunks: {deprecation_result.get('message')}",
                    "details": details
                }
            
            details["deprecated_chunks"] = deprecation_result.get("deprecated_count", 0)
            logger.info(f"Deprecated {details['deprecated_chunks']} chunks")
            
            # Step 3: Re-embed new policy text (if provided)
            new_chunk_ids = []
            embedding_job_id = None
            new_version = None
            
            if new_policy_text and self.policy_reembedding_service:
                logger.info("Starting re-embedding of new policy text")
                
                # Determine new version number
                for doc_id in affected_doc_ids:
                    latest_version = await self.policy_docs_repo.get_latest_version_number(doc_id)
                    new_version = latest_version + 1
                    
                    # Re-embed
                    reembed_result = await self.policy_reembedding_service.reingest_policy(
                        new_policy_text=new_policy_text,
                        doc_id=doc_id,
                        version=new_version,
                        metadata={
                            "section": ticket.get("extracted_fields", {}).get("policy_reference", "Updated Section"),
                            "ticket_id": ticket_id
                        },
                        source_reference=source_reference
                    )
                    
                    if reembed_result.get("status") == "completed":
                        new_chunk_ids.extend(reembed_result.get("new_chunk_ids", []))
                        embedding_job_id = reembed_result.get("job_id")
                        details["new_chunks"] = len(new_chunk_ids)
                        logger.info(f"Re-embedded {details['new_chunks']} new chunks")
                    else:
                        logger.warning(f"Re-embedding partially failed: {reembed_result.get('message')}")
            
            # Step 4: Update policy_documents collection
            if new_version and affected_doc_ids:
                for doc_id in affected_doc_ids:
                    try:
                        # Create new policy document version
                        await self.policy_docs_repo.create_policy_document({
                            "doc_id": doc_id,
                            "version": new_version,
                            "status": "active",
                            "effective_date": datetime.utcnow(),
                            "supersedes": await self._get_previous_version_id(doc_id),
                            "source_reference": source_reference or ticket.get("extracted_fields", {}).get("circular_number", "N/A"),
                            "created_by": reviewer_id,
                            "chunk_ids": new_chunk_ids,
                            "metadata": {
                                "ticket_id": ticket_id,
                                "claim_text": ticket.get("claim_text", ""),
                                "updated_reason": ticket.get("extracted_fields", {}).get("specific_claim", "Policy update")
                            }
                        })
                        
                        logger.info(f"Created policy document {doc_id} v{new_version}")
                        
                    except Exception as e:
                        logger.error(f"Error creating policy document: {e}")
            
            # Step 5: Write audit trail
            logger.info("Writing audit trail")
            
            audit_id = await self.audit_trail_writer.write_update_audit(
                ticket_id=ticket_id,
                old_chunk_ids=old_chunk_ids,
                new_chunk_ids=new_chunk_ids,
                doc_ids=affected_doc_ids,
                executed_by=reviewer_id,
                reason=f"Policy update: {ticket.get('claim_text', 'N/A')}",
                source_reference=source_reference,
                embedding_job_id=embedding_job_id,
                rollback_pointer=await self._get_previous_audit_id(affected_doc_ids)
            )
            
            if not audit_id:
                logger.error("Failed to write audit trail")
                # Note: Changes are already applied, so we continue
            
            # Step 6: Mark ticket as implemented
            logger.info("Marking ticket as implemented")
            
            await self.tickets_repo.mark_implemented(
                ticket_id=ticket_id,
                audit_trail_id=audit_id
            )
            
            logger.info(f"Policy update execution completed: {ticket_id}")
            
            return {
                "success": True,
                "audit_id": audit_id,
                "new_version": new_version,
                "message": f"Policy update successfully executed. Audit: {audit_id}",
                "details": details
            }
            
        except Exception as e:
            logger.error(f"Error executing policy update: {e}")
            return {
                "success": False,
                "audit_id": None,
                "new_version": None,
                "message": f"Execution failed: {str(e)}",
                "details": details
            }
    
    async def _get_previous_version_id(self, doc_id: str) -> Optional[str]:
        """Get the previous version's document ID for supersedes field"""
        try:
            active_version = await self.policy_docs_repo.get_active_version(doc_id)
            return active_version.get("_id") if active_version else None
        except Exception:
            return None
    
    async def _get_previous_audit_id(self, doc_ids: list) -> Optional[str]:
        """Get the most recent audit ID for rollback pointer"""
        try:
            if not self.audit_trail_writer or not self.audit_trail_writer.audit_repo:
                return None
            
            for doc_id in doc_ids:
                audits = await self.audit_trail_writer.audit_repo.get_audit_history(
                    doc_id=doc_id,
                    limit=1
                )
                if audits:
                    return audits[0].get("audit_id")
            
            return None
        except Exception:
            return None


# Singleton instance (will be initialized with actual dependencies)
policy_update_executor = PolicyUpdateExecutor()
