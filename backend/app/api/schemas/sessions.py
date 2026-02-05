# Session schemas
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SessionCreateRequest(BaseModel):
    user_id: str

class SessionCreateResponse(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    message: str

class SessionResponse(BaseModel):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

class SessionsListResponse(BaseModel):
    sessions: list[SessionResponse]
    count: int

class SessionDeleteResponse(BaseModel):
    message: str
