"""
Memory Management API Routes
Handles user fact storage, retrieval, and control
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from app.core.auth_middleware import get_current_user
from app.db.mongo import MongoDB
from app.db.repositories.users_repo import UsersRepository
from app.services.memory_control_service import create_memory_controller
from app.services.fact_extraction_service import fact_extractor
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/memory", tags=["Memory Management"])


# ==================== Schemas ====================

class FactSchema(BaseModel):
    """Schema for a user fact"""
    category: str = Field(..., description="Fact category: identity, academic_context, concern")
    key: str = Field(..., description="Unique key for the fact")
    value: str | List[str] | Dict = Field(..., description="Fact value")
    retention: str = Field(default="permanent", description="Retention policy: permanent, semester, session")
    locked: bool = Field(default=False, description="Whether fact is locked from updates")
    confirmed: bool = Field(default=False, description="Whether user confirmed this fact")


class MemoryViewResponse(BaseModel):
    """Response for viewing user memory"""
    facts: List[Dict]
    total_count: int
    categories: Dict[str, int]


class MemoryCommandRequest(BaseModel):
    """Request for explicit memory commands"""
    command: str = Field(..., description="Command type: remember, forget, view_memory, reset_memory")
    key: Optional[str] = Field(None, description="Fact key for forget command")
    fact: Optional[FactSchema] = Field(None, description="Fact data for remember command")


class StoreFactRequest(BaseModel):
    """Request to store a fact"""
    fact: FactSchema
    require_confirmation: bool = Field(default=True)


class UpdateFactRequest(BaseModel):
    """Request to update a fact"""
    updates: Dict


class SetRetentionRequest(BaseModel):
    """Request to set retention policy"""
    retention: str = Field(..., description="Retention policy: permanent, semester, session")


# ==================== Routes ====================

@router.get("/view", response_model=MemoryViewResponse)
async def view_user_memory(
    current_user: dict = Depends(get_current_user)
):
    """
    Get all stored facts for the current user
    
    Returns:
        User's stored facts with statistics
    """
    try:
        users_repo = UsersRepository(MongoDB.get_db())
        memory_controller = create_memory_controller(users_repo)
        
        user_id = str(current_user["user_id"])
        facts = await memory_controller.get_user_memory(user_id, include_metadata=False)
        
        # Count by category
        categories = {}
        for fact in facts:
            cat = fact.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
        
        return MemoryViewResponse(
            facts=facts,
            total_count=len(facts),
            categories=categories
        )
        
    except Exception as e:
        logger.error(f"❌ Error viewing user memory: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user memory"
        )


@router.post("/store")
async def store_fact(
    request: StoreFactRequest,
    current_user: dict = Depends(get_current_user)
):
    """Store a new fact for the user"""
    try:
        users_repo = UsersRepository(MongoDB.get_db())
        memory_controller = create_memory_controller(users_repo)
        
        user_id = str(current_user["user_id"])
        fact_dict = request.fact.model_dump()
        
        success = await memory_controller.store_fact(
            user_id,
            fact_dict,
            require_confirmation=request.require_confirmation
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to store fact"
            )
        
        return {
            "success": True,
            "message": "Fact stored successfully",
            "key": request.fact.key
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error storing fact: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store fact"
        )


@router.put("/update/{key}")
async def update_fact(
    key: str,
    request: UpdateFactRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing fact"""
    try:
        users_repo = UsersRepository(MongoDB.get_db())
        memory_controller = create_memory_controller(users_repo)
        
        user_id = str(current_user["user_id"])
        
        success = await memory_controller.update_fact(user_id, key, request.updates)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fact '{key}' not found"
            )
        
        return {
            "success": True,
            "message": f"Fact '{key}' updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating fact: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update fact"
        )


@router.delete("/forget/{key}")
async def forget_fact(
    key: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a specific fact"""
    try:
        users_repo = UsersRepository(MongoDB.get_db())
        memory_controller = create_memory_controller(users_repo)
        
        user_id = str(current_user["user_id"])
        
        success = await memory_controller.delete_fact(user_id, key)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fact '{key}' not found"
            )
        
        return {
            "success": True,
            "message": f"Forgot '{key}' successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting fact: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete fact"
        )


@router.delete("/reset")
async def reset_memory(
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Delete all facts, optionally filtered by category"""
    try:
        users_repo = UsersRepository(MongoDB.get_db())
        memory_controller = create_memory_controller(users_repo)
        
        user_id = str(current_user["user_id"])
        
        success = await memory_controller.delete_all_facts(user_id, category)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to reset memory"
            )
        
        category_msg = f" in category '{category}'" if category else ""
        return {
            "success": True,
            "message": f"Memory reset successfully{category_msg}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error resetting memory: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset memory"
        )


@router.post("/confirm/{key}")
async def confirm_fact(
    key: str,
    current_user: dict = Depends(get_current_user)
):
    """Confirm a fact that was auto-extracted"""
    try:
        users_repo = UsersRepository(MongoDB.get_db())
        memory_controller = create_memory_controller(users_repo)
        
        user_id = str(current_user["user_id"])
        
        success = await memory_controller.confirm_fact(user_id, key)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fact '{key}' not found"
            )
        
        return {
            "success": True,
            "message": f"Fact '{key}' confirmed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error confirming fact: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm fact"
        )


@router.post("/lock/{key}")
async def lock_fact(
    key: str,
    locked: bool = True,
    current_user: dict = Depends(get_current_user)
):
    """Lock or unlock a fact to prevent/allow updates"""
    try:
        users_repo = UsersRepository(MongoDB.get_db())
        memory_controller = create_memory_controller(users_repo)
        
        user_id = str(current_user["user_id"])
        
        success = await memory_controller.lock_fact(user_id, key, locked)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fact '{key}' not found"
            )
        
        action = "locked" if locked else "unlocked"
        return {
            "success": True,
            "message": f"Fact '{key}' {action}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error locking fact: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to lock/unlock fact"
        )


@router.put("/retention/{key}")
async def set_retention_policy(
    key: str,
    request: SetRetentionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update retention policy for a fact"""
    try:
        users_repo = UsersRepository(MongoDB.get_db())
        memory_controller = create_memory_controller(users_repo)
        
        user_id = str(current_user["user_id"])
        
        success = await memory_controller.set_retention_policy(
            user_id, key, request.retention
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fact '{key}' not found"
            )
        
        return {
            "success": True,
            "message": f"Retention policy for '{key}' updated to '{request.retention}'"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error setting retention policy: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set retention policy"
        )


@router.post("/cleanup")
async def cleanup_expired_facts(
    current_user: dict = Depends(get_current_user)
):
    """Remove expired facts based on retention policy"""
    try:
        users_repo = UsersRepository(MongoDB.get_db())
        memory_controller = create_memory_controller(users_repo)
        
        user_id = str(current_user["user_id"])
        
        deleted_count = await memory_controller.cleanup_expired_facts(user_id)
        
        return {
            "success": True,
            "message": f"Cleaned up {deleted_count} expired fact(s)",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"❌ Error cleaning up facts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup expired facts"
        )
