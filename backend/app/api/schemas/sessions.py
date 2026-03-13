# Session schemas
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class SessionCreateRequest(BaseModel):
    user_id: str
    extension_id: Optional[str] = None
    extension_name: Optional[str] = None
    extension_icon: Optional[str] = None

class SessionCreateResponse(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    message: str
    extension_id: Optional[str] = None
    requires_files: bool = False
    required_file_types: Optional[List[str]] = None

class SessionResponse(BaseModel):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    extension_id: Optional[str] = None
    extension_name: Optional[str] = None
    extension_icon: Optional[str] = None
    extension_welcome_message: Optional[str] = None
    extension_input_placeholder: Optional[str] = None

class SessionsListResponse(BaseModel):
    sessions: list[SessionResponse]
    count: int

class SessionDeleteResponse(BaseModel):
    message: str
