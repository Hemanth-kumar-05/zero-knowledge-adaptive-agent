# Query request/response models
from pydantic import BaseModel, Field
from typing import List, Optional

class QueryRequest(BaseModel):
    question: str
    session_id: str

class Source(BaseModel):
    doc_id: str
    section: str
    similarity: float
    confidence: float

class RiskAlert(BaseModel):
    """Risk alert detected from conversation patterns"""
    risk_type: str  # 'attendance', 'deadline', 'policy_confusion'
    severity: str  # 'low', 'medium', 'high'
    confidence: float  # 0.0 to 1.0
    message: str
    indicators: List[str]
    detected_at: str  # ISO format datetime

class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: Optional[List[Source]]
    refused: bool = Field(default=False)
    session_id: str
    confidence: Optional[str]
    risk_alerts: Optional[List[RiskAlert]] = Field(default=None)  # NEW: Risk alerts
    session_limit_warning: Optional[dict] = Field(default=None)  # NEW: Session limit suggestion