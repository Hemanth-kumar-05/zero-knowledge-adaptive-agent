"""
Authentication Schemas
Pydantic models for authentication endpoints
"""

from pydantic import BaseModel, EmailStr
from typing import Optional


class GoogleAuthRequest(BaseModel):
    """Request to initiate Google OAuth flow"""
    redirect_uri: Optional[str] = None


class GoogleCallbackRequest(BaseModel):
    """Google OAuth callback with authorization code"""
    code: str
    state: Optional[str] = None


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user: "UserInfo"


class UserInfo(BaseModel):
    """Basic user information"""
    id: str
    email: EmailStr
    name: str
    profile_picture: Optional[str] = None


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
