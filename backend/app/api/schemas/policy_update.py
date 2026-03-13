"""
Policy Update API Schemas (Phase 3)
Pydantic models for policy update ticket requests and responses
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


# ============================================
# Ticket Creation Schemas
# ============================================

class AffectedChunkSchema(BaseModel):
    """Schema for affected chunk information"""
    chunk_id: str
    doc_id: str
    current_text: str
    contradiction_score: float = Field(ge=0.0, le=1.0)


class ExtractedFieldsSchema(BaseModel):
    """Schema for extracted evidence fields"""
    circular_number: Optional[str] = None
    date_mentioned: Optional[str] = None
    policy_reference: Optional[str] = None
    specific_claim: str


class PolicyUpdateTicketCreate(BaseModel):
    """Schema for creating a policy update ticket"""
    user_id: str
    session_id: str
    claim_text: str
    query_context: str
    claim_type: str  # "policy_outdated", "contradiction", "missing_info"
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_level: str  # "low", "medium", "high"
    extracted_fields: ExtractedFieldsSchema
    affected_chunks: List[AffectedChunkSchema]


# ============================================
# Ticket Response Schemas
# ============================================

class PolicyUpdateTicketResponse(BaseModel):
    """Schema for policy update ticket response"""
    ticket_id: str
    status: str  # "pending", "approved", "rejected", "implemented"
    created_at: datetime
    updated_at: datetime
    
    # Claim information
    user_id: str
    session_id: str
    claim_text: str
    query_context: str
    claim_type: str
    confidence_score: float
    confidence_level: str
    
    # Evidence
    extracted_fields: ExtractedFieldsSchema
    affected_chunks: List[AffectedChunkSchema]
    trust_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # Proof uploads
    proof_urls: Optional[List[str]] = None
    has_proofs: Optional[bool] = False
    
    # Review information
    reviewer_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    decision: Optional[str] = None
    reviewer_notes: Optional[str] = None
    
    # Implementation
    implemented_at: Optional[datetime] = None
    audit_trail_id: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PolicyUpdateTicketListResponse(BaseModel):
    """Schema for list of tickets"""
    tickets: List[PolicyUpdateTicketResponse]
    total: int
    page: int
    page_size: int


# ============================================
# Review Decision Schemas
# ============================================

class ApprovalRequest(BaseModel):
    """Schema for approving a ticket"""
    reviewer_notes: Optional[str] = Field(None, max_length=1000)
    source_reference: Optional[str] = Field(None, max_length=200)


class RejectionRequest(BaseModel):
    """Schema for rejecting a ticket"""
    reviewer_notes: str = Field(..., min_length=10, max_length=1000)
    reason: str = Field(..., min_length=5, max_length=500)


class ReviewDecisionResponse(BaseModel):
    """Schema for review decision response"""
    ticket_id: str
    decision: str  # "approve" or "reject"
    status: str
    message: str


# ============================================
# Rollback Schemas
# ============================================

class RollbackRequest(BaseModel):
    """Schema for rollback request"""
    reason: str = Field(..., min_length=10, max_length=500)
    confirmation: str = Field(..., description="Must be 'CONFIRM ROLLBACK'")


class RollbackResponse(BaseModel):
    """Schema for rollback response"""
    success: bool
    restored_version: Optional[int] = None
    rollback_audit_id: Optional[str] = None
    message: str


# ============================================
# Audit Trail Schemas
# ============================================

class AuditRecordResponse(BaseModel):
    """Schema for audit record response"""
    audit_id: str
    ticket_id: str
    timestamp: datetime
    change_type: str  # "deprecate", "add", "update", "rollback"
    old_chunk_ids: List[str]
    new_chunk_ids: List[str]
    affected_doc_ids: List[str]
    executed_by: str
    reason: str
    source_reference: Optional[str] = None
    embedding_job_id: Optional[str] = None
    rollback_pointer: Optional[str] = None
    verification_status: str
    verification_notes: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AuditHistoryResponse(BaseModel):
    """Schema for audit history list"""
    audits: List[AuditRecordResponse]
    total: int
    page: int
    page_size: int


# ============================================
# Statistics Schemas
# ============================================

class TicketStatsResponse(BaseModel):
    """Schema for ticket statistics"""
    total_tickets: int
    pending: int
    approved: int
    rejected: int
    implemented: int
    by_status: Dict[str, int]  # Status breakdown
    by_confidence_level: Dict[str, int]
    by_claim_type: Dict[str, int]
    avg_trust_score: float  # Average trust score across all tickets


# ============================================
# Error Response Schema
# ============================================

class ErrorResponse(BaseModel):
    """Schema for error responses"""
    error: str
    detail: Optional[str] = None
    ticket_id: Optional[str] = None


# ============================================
# Policy Deprecation Schemas (Phase 3.1)
# ============================================

class ChunkUpdate(BaseModel):
    """Schema for individual chunk update"""
    chunk_id: str = Field(..., description="ID of chunk to update")
    new_text: str = Field(..., min_length=20, description="New text for this chunk")

class PolicyDeprecationRequest(BaseModel):
    """Schema for applying policy deprecation with individual chunk edits"""
    chunk_updates: List[ChunkUpdate] = Field(
        ...,
        description="List of chunk updates with individual edited text"
    )
    policy_area: str = Field(
        ...,
        description="Policy area being updated"
    )
    deprecation_reason: str = Field(
        default="Policy updated based on new circular/regulation",
        description="Reason for deprecating old chunks"
    )


class PolicyDeprecationResponse(BaseModel):
    """Schema for deprecation response"""
    success: bool
    deprecated_count: int
    created_count: int
    deprecated_chunk_ids: List[str]
    new_chunk_ids: List[str]
    message: str
    ticket_id: str
    timestamp: str
