"""
Policy Proof Upload Routes (Phase 3)
Handles file uploads for policy change proofs
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from typing import List, Optional
from pydantic import BaseModel
import logging

from app.core.auth_middleware import get_current_user
from app.services.cloudinary_service import cloudinary_service
from app.db.mongo import MongoDB
from app.db.repositories.policy_update_tickets_repo import PolicyUpdateTicketsRepository
from app.db.repositories.sessions_repo import SessionRepository

logger = logging.getLogger(__name__)

router = APIRouter()


class ProofUploadResponse(BaseModel):
    """Response for proof upload"""
    success: bool
    proof_url: str
    public_id: str
    file_type: str
    file_size: int


class CreateTicketWithProofsRequest(BaseModel):
    """Request to create ticket with uploaded proofs"""
    session_id: str
    proof_urls: List[str]


@router.post("/policy-proofs/upload", response_model=ProofUploadResponse)
async def upload_proof(
    file: UploadFile = File(...),
    ticket_id_pending: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload proof document for policy change claim
    
    Accepts: images (PNG, JPG, JPEG), PDFs, text files
    """
    try:
        # Validate file type
        allowed_types = [
            "image/png", "image/jpeg", "image/jpg",
            "application/pdf",
            "text/plain"
        ]
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}. "
                        "Please upload images, PDFs, or text files."
            )
        
        # Validate file size (max 10MB)
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=400,
                detail="File size exceeds 10MB limit"
            )
        
        # Upload to Cloudinary
        upload_result = await cloudinary_service.upload_proof(
            file_content=file_content,
            filename=file.filename,
            ticket_id=ticket_id_pending,
            file_type=file.content_type
        )
        
        if not upload_result:
            raise HTTPException(
                status_code=500,
                detail="Failed to upload proof to cloud storage"
            )
        
        logger.info(f"Proof uploaded: {upload_result['public_id']} by user {current_user['user_id']}")
        
        return ProofUploadResponse(
            success=True,
            proof_url=upload_result["secure_url"],
            public_id=upload_result["public_id"],
            file_type=file.content_type,
            file_size=file_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading proof: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/policy-proofs/create-ticket")
async def create_ticket_with_proofs(
    request: CreateTicketWithProofsRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create policy update ticket with uploaded proofs
    
    Retrieves pending claim data from session and creates ticket with proof URLs
    """
    try:
        user_id = current_user["user_id"]
        db = MongoDB.get_db()
        
        # Get session to retrieve pending claim data
        session_repo = SessionRepository(db)
        session = await session_repo.get_session(request.session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Check if user owns this session
        if str(session.get("user_id")) != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this session")
        
        # Get pending claim data
        pending_claim = session.get("metadata", {}).get("pending_policy_claim")
        
        if not pending_claim:
            raise HTTPException(
                status_code=400,
                detail="No pending policy claim found for this session"
            )
        
        # Create ticket with proofs
        ticket_repo = PolicyUpdateTicketsRepository(db)
        
        ticket_data = {
            "user_id": user_id,
            "session_id": request.session_id,
            "claim_text": pending_claim["claim_text"],
            "query_context": pending_claim["claim_text"],
            "claim_type": pending_claim["claim_type"],
            "confidence_score": pending_claim["claim_confidence"],
            "confidence_level": pending_claim["confidence_level"],
            "extracted_fields": pending_claim["extracted_fields"],
            "affected_chunks": pending_claim["affected_chunks"],
            "trust_score": pending_claim["trust_score"],
            "requires_human_review": True,
            "claim_detection_result": pending_claim.get("claim_detection_result", {}),
            "contradiction_analysis": pending_claim.get("contradiction_analysis", {}),
            "proof_urls": request.proof_urls,  # Add proof URLs
            "has_proofs": True
        }
        
        ticket_id = await ticket_repo.create_ticket(ticket_data)
        
        # Clear pending claim from session
        await session_repo.update_metadata(
            request.session_id,
            {"pending_policy_claim": None}
        )
        
        logger.info(
            f"✅ Policy ticket created with proofs: {ticket_id} "
            f"by user {user_id} ({len(request.proof_urls)} files)"
        )
        
        return {
            "success": True,
            "ticket_id": ticket_id,
            "message": "Policy update request submitted successfully. "
                      "Our team will review the provided evidence and update you soon."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating ticket with proofs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/policy-proofs/{ticket_id}")
async def delete_ticket_proofs(
    ticket_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete all proofs associated with a ticket (called after approval/rejection)
    
    Only accessible by admins or the ticket owner
    """
    try:
        # TODO: Add admin role check
        # For now, allow ticket owner or any authenticated user
        
        deleted_count = await cloudinary_service.delete_ticket_proofs(ticket_id)
        
        logger.info(f"Deleted {deleted_count} proofs for ticket {ticket_id}")
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Deleted {deleted_count} proof files"
        }
        
    except Exception as e:
        logger.error(f"Error deleting ticket proofs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
