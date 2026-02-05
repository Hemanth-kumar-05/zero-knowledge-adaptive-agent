# Message retrieval endpoints
from fastapi import APIRouter, HTTPException, Query, Path
from app.api.schemas.messages import MessagesListResponse, MessageResponse
from app.services.message_service import message_service

messages_router = APIRouter(prefix="/sessions", tags=["messages"])

@messages_router.get("/{session_id}/messages", response_model=MessagesListResponse)
async def get_session_messages(session_id: str):
    """Get all messages for a specific session."""
    result = await message_service.get_session_messages(session_id)
    result = [MessageResponse(
        id=msg["_id"],
        session_id=msg["session_id"],
        role=msg["role"],
        content=msg["content"],
        timestamp=msg["timestamp"],
        metadata=msg.get("metadata", None),
        extracted_preferences=msg.get("extracted_preferences", None),
        applied_preferences=msg.get("applied_preferences", None)
        ) for msg in result["messages"]
    ]
    result = {
        "messages": result,
        "count": len(result)
    }
    
    if "error" in result:
        status_code = 404 if "not found" in result["error"].lower() else 500
        raise HTTPException(status_code=status_code, detail=result["error"])
    
    return result
