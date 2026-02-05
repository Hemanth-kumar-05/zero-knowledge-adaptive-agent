# Session CRUD endpoints
from fastapi import APIRouter, HTTPException, Query, Depends
from app.api.schemas.sessions import (
    SessionCreateRequest,
    SessionCreateResponse,
    SessionResponse,
    SessionsListResponse
)
from app.services.session_service import session_service
from app.core.auth_middleware import get_optional_user, get_current_user
from typing import Optional, Dict

sessions_router = APIRouter(prefix="/sessions", tags=["sessions"])

@sessions_router.post("/", response_model=SessionCreateResponse)
async def create_session(current_user: Dict = Depends(get_current_user)):
    """Create a new chat session for the authenticated user."""
    user_id = current_user.get("user_id")
    result = await session_service.create_session(user_id)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result if isinstance(result, str) else "Internal Server Error")
    
    return result

@sessions_router.get("/", response_model=SessionsListResponse)
async def get_all_sessions(current_user: Dict = Depends(get_current_user)):
    """Get all sessions for the authenticated user."""
    user_id = current_user.get("user_id")
    result = await session_service.get_all_sessions(user_id=user_id)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result if isinstance(result, str) else "Internal Server Error")
    
    return result

@sessions_router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get a specific session by ID."""
    result = await session_service.get_session(session_id)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result if isinstance(result, str) else "Session not found")
    
    return result

@sessions_router.delete("/{session_id}")
async def delete_session(session_id: str, current_user: Dict = Depends(get_current_user)):
    """Delete a session and all its related data."""
    result = await session_service.delete_session(session_id)
    
    if isinstance(result, str):
        status_code = 404 if "not found" in result.lower() else 500
        raise HTTPException(status_code=status_code, detail=result)
    
    return result
