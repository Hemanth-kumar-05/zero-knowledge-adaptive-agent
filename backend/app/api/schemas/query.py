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

class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: Optional[List[Source]]
    refused: bool = Field(default=False)
    session_id: str
    confidence: Optional[str]