# Session CRUD endpoints
from fastapi import APIRouter, HTTPException, Query
from app.api.schemas.sessions import (
    SessionCreateRequest,
    SessionCreateResponse,
    SessionResponse,
    SessionsListResponse
)
from app.services.session_service import session_service
from typing import Optional

sessions_router = APIRouter(prefix="/sessions", tags=["sessions"])

@sessions_router.post("/", response_model=SessionCreateResponse)
async def create_session(request: SessionCreateRequest):
    """Create a new chat session."""
    result = await session_service.create_session(request.user_id)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result if isinstance(result, str) else "Internal Server Error")
    
    return result

@sessions_router.get("/", response_model=SessionsListResponse)
async def get_all_sessions():
    """Get all sessions, optionally filtered by user_id."""
    result = await session_service.get_all_sessions()
    
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
