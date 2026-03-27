# Message schemas
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal

class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime
    metadata: Optional[dict] = None
    extracted_preferences: Optional[list] = None  # For user messages that triggered preference extraction
    applied_preferences: Optional[list] = None  # For assistant messages that used preferences

class MessagesListResponse(BaseModel):
    messages: list[MessageResponse]
    count: int


class ExecutionCacheUpdateRequest(BaseModel):
    execution_cache: dict
