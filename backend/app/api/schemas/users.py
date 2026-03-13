"""
User Schemas
Pydantic models for user management endpoints
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List, Literal
from datetime import datetime


class UserProfileUpdate(BaseModel):
    """Request to update user profile"""
    name: Optional[str] = None
    profile_picture: Optional[str] = None
    role: Optional[str] = None


class Preference(BaseModel):
    """User preference item"""
    key: str
    category: Optional[str] = None
    value: str
    confidence: Optional[float] = 1.0
    source: Optional[str] = "manual"
    explanation: Optional[str] = None
    custom_instruction: Optional[str] = None  # Freeform text for manual preferences
    extracted_from_message: Optional[str] = None
    source_session_id: Optional[str] = None
    source_message_id: Optional[str] = None
    source_message_preview: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    update_count: Optional[int] = 1
    locked: Optional[bool] = False


class PreferenceCreate(BaseModel):
    """Request to create/update a preference"""
    key: str
    value: str
    confidence: Optional[float] = 1.0
    source: Optional[str] = "manual"


class PreferenceLock(BaseModel):
    """Request to lock/unlock a preference"""
    locked: bool


class ManualPreferenceInput(BaseModel):
    """Request to add preference via natural language"""
    preference_text: str


class AdminUserRoleUpdate(BaseModel):
    """Admin request to update a user's role"""
    role: Literal["student", "faculty", "admin"]


class AdminUserStatusUpdate(BaseModel):
    """Admin request to update a user's account status"""
    account_status: Literal["active", "suspended"]


class PreferencesResponse(BaseModel):
    """Response with all user preferences"""
    preferences: List[Preference]
    total_count: int
    auto_extraction_enabled: bool


class PreferenceResponse(BaseModel):
    """Response for preference operations"""
    message: str
    preference: Optional[Preference] = None
    key: Optional[str] = None
    locked: Optional[bool] = None


class UserProfile(BaseModel):
    """Complete user profile"""
    id: str
    google_id: str
    email: EmailStr
    name: str
    profile_picture: Optional[str]
    role: str
    created_at: datetime
    last_login: datetime
    account_status: str
    preferences: List[Preference]
    personalization_metadata: dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "google_id": "123456789",
                "email": "user@example.com",
                "name": "John Doe",
                "profile_picture": "https://example.com/photo.jpg",
                "role": "student",
                "created_at": "2026-01-28T10:00:00",
                "last_login": "2026-01-28T15:30:00",
                "account_status": "active",
                "preferences": [],
                "personalization_metadata": {
                    "total_interactions": 0,
                    "preference_updates_count": 0,
                    "last_preference_update": None,
                    "total_preferences": 0
                }
            }
        }
