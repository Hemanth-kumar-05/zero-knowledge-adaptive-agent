# Message retrieval endpoints
from fastapi import APIRouter, HTTPException, Query, Path, Depends
from app.api.schemas.messages import MessagesListResponse, MessageResponse, ExecutionCacheUpdateRequest
from app.services.message_service import message_service
from app.core.auth_middleware import get_current_user
from typing import Dict

messages_router = APIRouter(prefix="/sessions", tags=["messages"])

@messages_router.get("/{session_id}/messages", response_model=MessagesListResponse)
async def get_session_messages(session_id: str, current_user: Dict = Depends(get_current_user)):
    """Get all messages for a specific session."""
    user_id = current_user.get("user_id")
    result = await message_service.get_session_messages(session_id, requester_user_id=user_id)

    if "error" in result:
        error_message = result["error"]
        if "access denied" in error_message.lower():
            raise HTTPException(status_code=403, detail=error_message)
        status_code = 404 if "not found" in error_message.lower() else 500
        raise HTTPException(status_code=status_code, detail=error_message)

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

    return result


@messages_router.patch("/messages/{message_id}/execution-cache")
async def update_execution_cache(
    message_id: str,
    request: ExecutionCacheUpdateRequest,
    current_user: Dict = Depends(get_current_user),
):
    """Persist computed execution output for an assistant message."""
    user_id = current_user.get("user_id")
    result = await message_service.update_execution_cache(
        message_id=message_id,
        execution_cache=request.execution_cache,
        requester_user_id=user_id,
    )

    if "error" in result:
        error_message = result["error"]
        if "access denied" in error_message.lower():
            raise HTTPException(status_code=403, detail=error_message)
        status_code = 404 if "not found" in error_message.lower() else 500
        raise HTTPException(status_code=status_code, detail=error_message)

    return result
