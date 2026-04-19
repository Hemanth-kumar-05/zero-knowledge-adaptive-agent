# Query request/response models
from pydantic import BaseModel, Field
from typing import List, Optional

class QueryRequest(BaseModel):
    question: str
    session_id: str

class CodeRepairRequest(BaseModel):
    question: str
    code: str
    error: str
    traceback: Optional[str] = None
    dataset_preview: str
    file_name: Optional[str] = None
    extension_name: Optional[str] = None

class CodeRepairResponse(BaseModel):
    fixed_code: str

class Source(BaseModel):
    id: Optional[str] = None
    doc_id: str
    section: str
    similarity: float
    confidence: float
    text: Optional[str] = None
    metadata: Optional[dict] = None

class RiskAlert(BaseModel):
    """Risk alert detected from conversation patterns"""
    risk_type: str  # 'attendance', 'deadline', 'policy_confusion'
    severity: str  # 'low', 'medium', 'high'
    confidence: float  # 0.0 to 1.0
    message: str
    indicators: List[str]
    detected_at: str  # ISO format datetime

class PolicyClaimDetected(BaseModel):
    """Policy change claim detected in user message"""
    claim_detected: bool
    ticket_id_pending: str
    claim_text: str
    claim_type: str
    confidence_level: str
    trust_score: float
    requires_proof: bool
    message_to_user: str

class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: Optional[List[Source]]
    refused: bool = Field(default=False)
    generation_error: Optional[dict] = Field(default=None)
    session_id: str
    user_message_id: Optional[str] = Field(default=None)
    assistant_message_id: Optional[str] = Field(default=None)
    confidence: Optional[str]
    risk_alerts: Optional[List[RiskAlert]] = Field(default=None)  # NEW: Risk alerts
    session_limit_warning: Optional[dict] = Field(default=None)  # NEW: Session limit suggestion
    policy_claim_detected: Optional[PolicyClaimDetected] = Field(default=None)  # Phase 3: Policy update claim
