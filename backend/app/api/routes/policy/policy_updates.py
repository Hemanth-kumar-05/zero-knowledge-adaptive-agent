"""
Policy Updates API Routes (Phase 3)
Endpoints for managing policy update tickets and review workflow
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import logging
from datetime import datetime

from app.api.schemas.policy_update import (
    PolicyUpdateTicketCreate,
    PolicyUpdateTicketResponse,
    PolicyUpdateTicketListResponse,
    ApprovalRequest,
    RejectionRequest,
    ReviewDecisionResponse,
    RollbackRequest,
    RollbackResponse,
    AuditHistoryResponse,
    TicketStatsResponse,
    ErrorResponse,
    PolicyDeprecationRequest,
    PolicyDeprecationResponse
)
from app.db.mongo import MongoDB
from app.db.repositories.policy_update_tickets_repo import PolicyUpdateTicketsRepository
from app.db.repositories.policy_change_audit_repo import PolicyChangeAuditRepository
from app.core.auth_middleware import get_current_user
from config import config

logger = logging.getLogger(__name__)

router = APIRouter(tags=["policy-updates"])

# ============================================
# Dependency Injections
# ============================================

def get_tickets_repo():
    """Get policy update tickets repository"""
    db = MongoDB.get_db()
    return PolicyUpdateTicketsRepository(db)


def get_audit_repo():
    """Get policy change audit repository"""
    db = MongoDB.get_db()
    return PolicyChangeAuditRepository(db)


def get_audit_service():
    """Get audit trail writer service"""
    from app.services.audit_trail_service import audit_trail_writer
    audit_repo = get_audit_repo()
    audit_trail_writer.audit_repo = audit_repo
    return audit_trail_writer


def get_chunk_service():
    """Get chunk deprecation service"""
    from app.services.chunk_deprecation_service import chunk_deprecation_service
    from rag.pipeline import rag_pipeline
    # Initialize with retriever from RAG pipeline (which has the collection)
    if hasattr(rag_pipeline, 'retriever'):
        chunk_deprecation_service.vector_index = rag_pipeline.retriever
    return chunk_deprecation_service


# ============================================
# Ticket Management Endpoints
# ============================================

@router.post(
    "/tickets",
    response_model=PolicyUpdateTicketResponse,
    status_code=201,
    summary="Create policy update ticket (Internal)"
)
async def create_policy_update_ticket(
    ticket_data: PolicyUpdateTicketCreate,
    tickets_repo: PolicyUpdateTicketsRepository = Depends(get_tickets_repo)
):
    """
    Create a new policy update ticket
    
    **Internal endpoint** - typically called by claim detection system,
    not directly by users.
    
    Creates a ticket that requires admin/faculty review before implementation.
    """
    if not config.ENABLE_POLICY_UNLEARNING:
        raise HTTPException(
            status_code=503,
            detail="Policy unlearning feature is currently disabled"
        )
    
    try:
        # Convert Pydantic models to dicts for repository
        ticket_dict = ticket_data.dict()
        ticket_dict["extracted_fields"] = ticket_dict["extracted_fields"]
        ticket_dict["affected_chunks"] = ticket_dict["affected_chunks"]
        
        # Create ticket
        ticket_id = await tickets_repo.create_ticket(ticket_dict)
        
        # Fetch created ticket
        ticket = await tickets_repo.get_ticket_by_id(ticket_id)
        
        if not ticket:
            raise HTTPException(status_code=500, detail="Failed to create ticket")
        
        return PolicyUpdateTicketResponse(**ticket)
        
    except Exception as e:
        logger.error(f"Error creating policy update ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/tickets",
    response_model=PolicyUpdateTicketListResponse,
    summary="List policy update tickets"
)
async def list_policy_update_tickets(
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    tickets_repo: PolicyUpdateTicketsRepository = Depends(get_tickets_repo)
):
    """
    List policy update tickets with optional filtering
    
    **Requires authentication** - Admin/Faculty only
    
    Query parameters:
    - status: Filter by status (pending, approved, rejected, implemented)
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    """
    if not config.ENABLE_POLICY_UNLEARNING:
        raise HTTPException(
            status_code=503,
            detail="Policy unlearning feature is currently disabled"
        )
    
    try:
        offset = (page - 1) * page_size
        
        # Fetch tickets
        tickets = await tickets_repo.list_tickets(
            status=status,
            limit=page_size,
            offset=offset
        )
        
        # Get total count
        if status:
            total = await tickets_repo.count_by_status(status)
        else:
            total = await tickets_repo.count_by_status("pending") + \
                    await tickets_repo.count_by_status("approved") + \
                    await tickets_repo.count_by_status("rejected") + \
                    await tickets_repo.count_by_status("implemented")
        
        # Convert to response models
        ticket_responses = [PolicyUpdateTicketResponse(**ticket) for ticket in tickets]
        
        return PolicyUpdateTicketListResponse(
            tickets=ticket_responses,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Error listing policy update tickets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/tickets/{ticket_id}",
    response_model=PolicyUpdateTicketResponse,
    summary="Get ticket details"
)
async def get_policy_update_ticket(
    ticket_id: str,
    current_user: dict = Depends(get_current_user),
    tickets_repo: PolicyUpdateTicketsRepository = Depends(get_tickets_repo)
):
    """
    Get detailed information about a specific policy update ticket
    
    **Requires authentication** - Admin/Faculty only
    """
    if not config.ENABLE_POLICY_UNLEARNING:
        raise HTTPException(
            status_code=503,
            detail="Policy unlearning feature is currently disabled"
        )
    
    try:
        ticket = await tickets_repo.get_ticket_by_id(ticket_id)
        
        if not ticket:
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
        
        return PolicyUpdateTicketResponse(**ticket)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching ticket {ticket_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Review Decision Endpoints
# ============================================

@router.post(
    "/tickets/{ticket_id}/approve",
    response_model=ReviewDecisionResponse,
    summary="Approve policy update ticket"
)
async def approve_policy_update_ticket(
    ticket_id: str,
    approval_data: ApprovalRequest,
    current_user: dict = Depends(get_current_user),
    tickets_repo: PolicyUpdateTicketsRepository = Depends(get_tickets_repo)
):
    """
    Approve a policy update ticket
    
    **Requires authentication** - Admin/Faculty only
    
    This marks the ticket as approved and queues it for implementation.
    The actual policy update will be executed by a background process.
    """
    if not config.ENABLE_POLICY_UNLEARNING:
        raise HTTPException(
            status_code=503,
            detail="Policy unlearning feature is currently disabled"
        )
    
    try:
        # Check if ticket exists
        ticket = await tickets_repo.get_ticket_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
        
        # Check if already reviewed
        if ticket.get("status") != "pending":
            raise HTTPException(
                status_code=400,
                detail=f"Ticket already {ticket.get('status')}"
            )
        
        # Add review decision
        user_id = current_user.get("user_id", "unknown")
        success = await tickets_repo.add_review_decision(
            ticket_id=ticket_id,
            reviewer_id=user_id,
            decision="approve",
            reviewer_notes=approval_data.reviewer_notes
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to approve ticket")
        
        # Delete proofs from Cloudinary after approval
        try:
            from app.services.cloudinary_service import cloudinary_service
            deleted_count = await cloudinary_service.delete_ticket_proofs(ticket_id)
            logger.info(f"Deleted {deleted_count} proofs for approved ticket {ticket_id}")
        except Exception as e:
            logger.warning(f"Failed to delete proofs: {e}")
        
        logger.info(f"Ticket {ticket_id} approved by {user_id}")
        
        return ReviewDecisionResponse(
            ticket_id=ticket_id,
            decision="approve",
            status="approved",
            message="Ticket approved successfully. Implementation will be processed."
        )
        
    except HTTPException:raise
    except Exception as e:
        logger.error(f"Error approving ticket {ticket_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/tickets/{ticket_id}/reject",
    response_model=ReviewDecisionResponse,
    summary="Reject policy update ticket"
)
async def reject_policy_update_ticket(
    ticket_id: str,
    rejection_data: RejectionRequest,
    current_user: dict = Depends(get_current_user),
    tickets_repo: PolicyUpdateTicketsRepository = Depends(get_tickets_repo)
):
    """
    Reject a policy update ticket
    
    **Requires authentication** - Admin/Faculty only
    
    This marks the ticket as rejected. No policy changes will be made.
    """
    if not config.ENABLE_POLICY_UNLEARNING:
        raise HTTPException(
            status_code=503,
            detail="Policy unlearning feature is currently disabled"
        )
    
    try:
        # Check if ticket exists
        ticket = await tickets_repo.get_ticket_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
        
        # Check if already reviewed
        if ticket.get("status") != "pending":
            raise HTTPException(
                status_code=400,
                detail=f"Ticket already {ticket.get('status')}"
            )
        
        # Add review decision
        user_id = current_user.get("user_id", "unknown")
        combined_notes = f"Reason: {rejection_data.reason}\n\nNotes: {rejection_data.reviewer_notes}"
        
        success = await tickets_repo.add_review_decision(
            ticket_id=ticket_id,
            reviewer_id=user_id,
            decision="reject",
            reviewer_notes=combined_notes
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to reject ticket")
        
        # Delete proofs from Cloudinary after rejection
        try:
            from app.services.cloudinary_service import cloudinary_service
            deleted_count = await cloudinary_service.delete_ticket_proofs(ticket_id)
            logger.info(f"Deleted {deleted_count} proofs for rejected ticket {ticket_id}")
        except Exception as e:
            logger.warning(f"Failed to delete proofs: {e}")
        
        logger.info(f"Ticket {ticket_id} rejected by {user_id}")
        
        return ReviewDecisionResponse(
            ticket_id=ticket_id,
            decision="reject",
            status="rejected",
            message="Ticket rejected. No changes will be made to policy documents."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting ticket {ticket_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Audit Trail Endpoints
# ============================================

@router.get(
    "/audit",
    response_model=AuditHistoryResponse,
    summary="Get audit history"
)
async def get_audit_history(
    doc_id: Optional[str] = Query(None, description="Filter by document ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    audit_repo: PolicyChangeAuditRepository = Depends(get_audit_repo)
):
    """
    Get audit history of policy changes
    
    **Requires authentication** - Admin/Faculty only
    
    Query parameters:
    - doc_id: Filter by specific document ID (optional)
    - page: Page number
    - page_size: Items per page
    """
    if not config.ENABLE_POLICY_UNLEARNING:
        raise HTTPException(
            status_code=503,
            detail="Policy unlearning feature is currently disabled"
        )
    
    try:
        offset = (page - 1) * page_size
        
        # Fetch audit records
        audits = await audit_repo.get_audit_history(
            doc_id=doc_id,
            limit=page_size,
            offset=offset
        )
        
        # Get total count
        total = await audit_repo.count_audits(
            {"affected_doc_ids": doc_id} if doc_id else None
        )
        
        return AuditHistoryResponse(
            audits=audits,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Error fetching audit history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Statistics Endpoint
# ============================================

@router.get(
    "/stats",
    response_model=TicketStatsResponse,
    summary="Get ticket statistics"
)
async def get_ticket_statistics(
    current_user: dict = Depends(get_current_user),
    tickets_repo: PolicyUpdateTicketsRepository = Depends(get_tickets_repo)
):
    """
    Get statistics about policy update tickets
    
    **Requires authentication** - Admin/Faculty only
    """
    if not config.ENABLE_POLICY_UNLEARNING:
        raise HTTPException(
            status_code=503,
            detail="Policy unlearning feature is currently disabled"
        )
    
    try:
        # Count by status
        pending = await tickets_repo.count_by_status("pending")
        approved = await tickets_repo.count_by_status("approved")
        rejected = await tickets_repo.count_by_status("rejected")
        implemented = await tickets_repo.count_by_status("implemented")
        
        total = pending + approved + rejected + implemented
        
        # Count by confidence level
        low_conf = await tickets_repo.get_tickets_by_confidence_level("low", limit=1000)
        medium_conf = await tickets_repo.get_tickets_by_confidence_level("medium", limit=1000)
        high_conf = await tickets_repo.get_tickets_by_confidence_level("high", limit=1000)
        
        # Calculate average trust score
        all_tickets = await tickets_repo.list_tickets(limit=1000)
        trust_scores = [t.get("trust_score", 0) for t in all_tickets if t.get("trust_score") is not None]
        avg_trust_score = sum(trust_scores) / len(trust_scores) if trust_scores else 0.0
        
        # TODO: Count by claim type (would need a new repository method)
        
        return TicketStatsResponse(
            total_tickets=total,
            pending=pending,
            approved=approved,
            rejected=rejected,
            implemented=implemented,
            by_status={
                "pending": pending,
                "approved": approved,
                "rejected": rejected,
                "implemented": implemented
            },
            by_confidence_level={
                "low": len(low_conf),
                "medium": len(medium_conf),
                "high": len(high_conf)
            },
            by_claim_type={},  # TODO: Implement
            avg_trust_score=avg_trust_score
        )
        
    except Exception as e:
        logger.error(f"Error fetching ticket statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Semantic Policy Search & Deprecation
# ============================================

@router.post(
    "/tickets/{ticket_id}/find-affected-chunks",
    summary="Find all chunks affected by policy update"
)
async def find_affected_chunks(
    ticket_id: str,
    current_user: dict = Depends(get_current_user),
    tickets_repo: PolicyUpdateTicketsRepository = Depends(get_tickets_repo)
):
    """
    Use semantic search to find all chunks related to the policy claim
    
    Returns high confidence and possibly related chunks for admin review
    
    **Requires authentication** - Admin/Faculty only
    """
    if not config.ENABLE_POLICY_UNLEARNING:
        raise HTTPException(
            status_code=503,
            detail="Policy unlearning feature is currently disabled"
        )
    
    try:
        # Get ticket
        ticket = await tickets_repo.get_ticket_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Extract claim and proof from ticket
        user_claim = ticket.get("claim_text", "")
        proof_text = ticket.get("extracted_fields", {}).get("policy_text", "")
        
        if not user_claim:
            raise HTTPException(status_code=400, detail="Ticket has no claim text")
        
        # Use semantic search service
        from app.services.semantic_policy_search_service import semantic_policy_search
        
        result = await semantic_policy_search.find_affected_chunks(
            user_claim=user_claim,
            proof_text=proof_text
        )
        
        return {
            "ticket_id": ticket_id,
            "policy_area": result["policy_area"],
            "search_query": result["search_query"],
            "high_confidence_chunks": result["high_confidence_chunks"],
            "possibly_related_chunks": result["possibly_related_chunks"],
            "total_found": result["total_found"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding affected chunks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/tickets/{ticket_id}/apply-deprecation",
    response_model=PolicyDeprecationResponse,
    responses={
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def apply_policy_deprecation(
    ticket_id: str,
    request: PolicyDeprecationRequest,
    current_user: dict = Depends(get_current_user),
    tickets_repo: PolicyUpdateTicketsRepository = Depends(get_tickets_repo),
    audit_service = Depends(get_audit_service),
    chunk_service = Depends(get_chunk_service)
):
    """
    Apply policy deprecation by deprecating old chunks and creating new ones
    
    Workflow:
    1. Validate ticket is approved
    2. Deprecate selected chunks
    3. Create new chunks from updated policy text
    4. Update ticket status to 'implemented'
    5. Record audit trail
    
    Args:
        ticket_id: Policy update ticket ID
        request: Deprecation request with chunk IDs and new policy text
        
    Returns:
        PolicyDeprecationResponse with counts and chunk IDs
    """
    try:
        # Check feature flag
        if not config.ENABLE_POLICY_UNLEARNING:
            raise HTTPException(
                status_code=403,
                detail="Policy unlearning feature is not enabled"
            )
        
        # Check user permissions (admin or faculty only)
        print(f"User {current_user.get('email')} with role {current_user.get('role')} is attempting to apply policy deprecation for ticket {ticket_id}")
        user_role = current_user.get("role", "student")
        if user_role not in ["admin", "faculty"]:
            raise HTTPException(
                status_code=403,
                detail="Only admins and faculty can apply policy deprecation"
            )
        
        # Get ticket
        ticket = await tickets_repo.get_ticket_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Validate ticket is approved
        if ticket.get("status") != "approved":
            raise HTTPException(
                status_code=400,
                detail=f"Ticket must be approved before deprecation. Current status: {ticket.get('status')}"
            )
        
        user_id = current_user.get("user_id", "unknown")
        
        logger.info(f"Applying policy deprecation for ticket {ticket_id}")
        logger.info(f"  Chunks to update: {len(request.chunk_updates)}")
        
        # Extract chunk IDs to deprecate
        chunk_ids_to_deprecate = [update.chunk_id for update in request.chunk_updates]
        
        # Step 1: Deprecate old chunks first
        deprecation_result = await chunk_service.deprecate_chunks(
            chunk_ids=chunk_ids_to_deprecate,
            reason=request.deprecation_reason,
            audit_id=ticket_id,  # Use ticket_id as audit reference
            deprecated_by=user_id
        )
        
        if not deprecation_result.get("success"):
            logger.error(f"Chunk deprecation failed: {deprecation_result.get('message')}")
            raise HTTPException(
                status_code=500,
                detail=f"Chunk deprecation failed: {deprecation_result.get('message')}"
            )
        
        deprecated_count = deprecation_result.get("deprecated_count", 0)
        deprecated_chunk_ids = [
            cid for cid in chunk_ids_to_deprecate 
            if cid not in deprecation_result.get("failed_chunks", [])
        ]
        
        logger.info(f"✅ Deprecated {deprecated_count} chunks")
        
        # Step 2: Group chunk updates by unique text content (deduplication)
        text_to_chunks_map = {}
        for chunk_update in request.chunk_updates:
            text = chunk_update.new_text.strip()
            if text not in text_to_chunks_map:
                text_to_chunks_map[text] = []
            text_to_chunks_map[text].append(chunk_update.chunk_id)
        
        logger.info(f"Grouped {len(request.chunk_updates)} updates into {len(text_to_chunks_map)} unique text contents")
        
        # Step 3: Create one new chunk per unique text (with array of replaces IDs)
        all_new_chunk_ids = []
        total_created = 0
        
        for new_text, replaced_chunk_ids in text_to_chunks_map.items():
            creation_result = await chunk_service.create_deduplicated_policy_chunk(
                new_text=new_text,
                policy_area=request.policy_area,
                ticket_id=ticket_id,
                created_by=user_id,
                replaces_chunk_ids=replaced_chunk_ids  # Array of all chunks with same text
            )
            
            if creation_result.get("success"):
                total_created += 1
                all_new_chunk_ids.extend(creation_result.get("chunk_ids", []))
                logger.info(f"✅ Created 1 chunk replacing {len(replaced_chunk_ids)} duplicates")
            else:
                logger.warning(f"Failed to create chunk: {creation_result.get('message')}")
        
        if total_created == 0:
            logger.error("No chunks were created successfully")
            # Try to rollback deprecations
            logger.warning("Attempting to rollback deprecations...")
            await chunk_service.reactivate_chunks(
                chunk_ids=deprecated_chunk_ids,
                reason="Rollback due to creation failure",
                audit_id=ticket_id,
                reactivated_by=user_id
            )
            raise HTTPException(
                status_code=500,
                detail="Failed to create any new chunks"
            )
        
        logger.info(f"✅ Created {total_created} unique chunks (from {len(request.chunk_updates)} updates)")
        
        # Step 3: Create audit trail entry
        try:
            # Get affected doc IDs from chunk updates
            affected_doc_ids = [f"policy_update_{ticket_id}"]
            
            audit_id = await audit_service.write_change_audit(
                ticket_id=ticket_id,
                change_type="deprecate_and_create",
                old_chunk_ids=deprecated_chunk_ids,
                new_chunk_ids=all_new_chunk_ids,
                affected_doc_ids=affected_doc_ids,
                executed_by=user_id,
                reason=request.deprecation_reason
            )
            logger.info(f"✅ Created audit trail entry: {audit_id}")
        except Exception as audit_error:
            logger.error(f"Failed to create audit trail: {audit_error}")
            # Don't fail the whole operation if audit fails
        
        # Step 4: Update ticket status to 'implemented'
        dedup_note = f" ({len(request.chunk_updates) - total_created} duplicates merged)" if len(request.chunk_updates) > total_created else ""
        await tickets_repo.update_ticket_status(
            ticket_id=ticket_id,
            new_status="implemented",
            additional_fields={
                "updated_by": user_id,
                "notes": f"Deprecated {deprecated_count} chunks, created {total_created} unique chunks{dedup_note}"
            }
        )
        
        logger.info(f"✅ Updated ticket {ticket_id} to 'implemented'")
        
        # Return success response
        dedup_msg = f" (deduplicated from {len(request.chunk_updates)} updates)" if len(request.chunk_updates) > total_created else ""
        return PolicyDeprecationResponse(
            success=True,
            deprecated_count=deprecated_count,
            created_count=total_created,
            deprecated_chunk_ids=deprecated_chunk_ids,
            new_chunk_ids=all_new_chunk_ids,
            message=f"Successfully deprecated {deprecated_count} chunks and created {total_created} unique chunks{dedup_msg}",
            ticket_id=ticket_id,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying policy deprecation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
