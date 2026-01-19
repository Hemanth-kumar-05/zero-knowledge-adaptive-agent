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

class MessagesListResponse(BaseModel):
    messages: list[MessageResponse]
    count: int
