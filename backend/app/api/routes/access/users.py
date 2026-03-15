"""
User Routes
User profile and preference management endpoints
"""

import asyncio
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Dict, List, Optional
from app.api.schemas.users import (
    UserProfile,
    UserProfileUpdate,
    PreferenceCreate,
    Preference,
    PreferenceLock,
    PreferencesResponse,
    PreferenceResponse,
    ManualPreferenceInput,
    AdminUserRoleUpdate,
    AdminUserStatusUpdate,
)
from app.db.mongo import get_db
from app.db.repositories.users_repo import UsersRepository
from app.db.repositories.messages_repo import MessageRepository
from app.services.user_service import UserService
from app.services.preference_extraction_service import AIPreferenceExtractor
from app.core.auth_middleware import get_current_user
from app.utils.logger import get_logger
from bson import ObjectId
from config import config

logger = get_logger(__name__)
router = APIRouter(prefix="/users", tags=["User Management"])
PROJECT_ROOT = Path(__file__).resolve().parents[5]
CHROMA_COLLECTION_NAME = "academic_docs"


def _serialize_user(user: Dict) -> Dict:
    """Helper to serialize user document for response"""
    if not user:
        return None
    
    user_copy = user.copy()
    user_copy["id"] = str(user_copy.pop("_id"))
    
    return user_copy


def _serialize_admin_user(user: Dict) -> Dict:
    """Minimal user payload for admin management UI."""
    identity = user.get("identity_verification", {})
    return {
        "id": str(user.get("_id")),
        "email": user.get("email", ""),
        "name": user.get("name", ""),
        "role": user.get("role", "student"),
        "account_status": user.get("account_status", "active"),
        "created_at": user.get("created_at"),
        "last_login": user.get("last_login"),
        "verification_required": identity.get("required", True),
        "verification_status": identity.get("status", "pending"),
        "verified_role": identity.get("verified_role"),
        "verification_provider": identity.get("provider"),
    }


async def _require_admin(current_user: Dict, users_repo: UsersRepository):
    """Ensure current user exists and has admin role."""
    requester = await users_repo.get_user_by_id(current_user["user_id"])
    if not requester:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requester user not found"
        )
    if requester.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )


def _build_chroma_chunk_payload(chunk_id: str, document: str, metadata: Optional[Dict]) -> Dict:
    metadata = metadata or {}
    return {
        "id": chunk_id,
        "document": document or "",
        "metadata": metadata,
        "preview": (document or "")[:240],
        "source": metadata.get("source") or metadata.get("file_name") or metadata.get("document_name"),
        "chunk_index": metadata.get("chunk_index"),
        "status": metadata.get("status", "active"),
    }


@router.get("/admin/users")
async def admin_list_users(
    current_user: Dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """Admin-only: list users for management dashboard."""
    users_repo = UsersRepository(db)
    await _require_admin(current_user, users_repo)

    users = await users_repo.list_users_for_admin(limit=1000)
    return {
        "users": [_serialize_admin_user(user) for user in users],
        "count": len(users),
    }


@router.get("/admin/chroma/chunks")
async def admin_list_chroma_chunks(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None, min_length=1),
    status: Optional[str] = Query(default=None),
    chunk_type: Optional[str] = Query(default=None),
    ticket_id: Optional[str] = Query(default=None),
    policy_updates_only: bool = Query(default=False),
    current_user: Dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """Admin-only: inspect chunks from the active Chroma collection."""
    users_repo = UsersRepository(db)
    await _require_admin(current_user, users_repo)

    chroma_path = str(PROJECT_ROOT / "data" / "chroma_db")

    def _load_chunks() -> Dict:
        client = config.get_chroma_client(chroma_path)
        collection = client.get_collection(CHROMA_COLLECTION_NAME)
        raw = collection.get(include=["documents", "metadatas"])

        ids = raw.get("ids") or []
        documents = raw.get("documents") or []
        metadatas = raw.get("metadatas") or []

        chunks = [
            _build_chroma_chunk_payload(chunk_id, document, metadata)
            for chunk_id, document, metadata in zip(ids, documents, metadatas)
        ]

        query = (search or "").strip().lower()
        status_filter = (status or "").strip().lower()
        chunk_type_filter = (chunk_type or "").strip().lower()
        ticket_filter = (ticket_id or "").strip().lower()

        if policy_updates_only:
            chunks = [
                chunk for chunk in chunks
                if chunk["metadata"].get("type") == "policy_update"
                or chunk["metadata"].get("ticket_id")
                or chunk["metadata"].get("replaces")
                or chunk["metadata"].get("version", 0) == 2
            ]

        if status_filter:
            chunks = [
                chunk for chunk in chunks
                if str(chunk["metadata"].get("status", chunk.get("status", ""))).lower() == status_filter
            ]

        if chunk_type_filter:
            chunks = [
                chunk for chunk in chunks
                if str(chunk["metadata"].get("type", "")).lower() == chunk_type_filter
            ]

        if ticket_filter:
            chunks = [
                chunk for chunk in chunks
                if ticket_filter in str(chunk["metadata"].get("ticket_id", "")).lower()
            ]

        if query:
            chunks = [
                chunk for chunk in chunks
                if query in chunk["document"].lower()
                or query in str(chunk["metadata"]).lower()
                or query in (chunk["source"] or "").lower()
            ]

        chunks.sort(
            key=lambda chunk: (
                0 if chunk["metadata"].get("type") == "policy_update" else 1,
                0 if chunk["metadata"].get("status") == "deprecated" else 1,
                str(
                    chunk["metadata"].get("updated_at")
                    or chunk["metadata"].get("created_at")
                    or chunk["metadata"].get("deprecated_at")
                    or ""
                ),
            ),
            reverse=True,
        )

        total_chunks = len(chunks)
        paginated_chunks = chunks[offset:offset + limit]
        connection_info = config.get_chroma_connection_info(chroma_path)

        return {
            "collection_name": CHROMA_COLLECTION_NAME,
            "connection": connection_info,
            "total_chunks": total_chunks,
            "returned_count": len(paginated_chunks),
            "limit": limit,
            "offset": offset,
            "search": search,
            "filters": {
                "status": status,
                "chunk_type": chunk_type,
                "ticket_id": ticket_id,
                "policy_updates_only": policy_updates_only,
            },
            "chunks": paginated_chunks,
        }

    try:
        return await asyncio.to_thread(_load_chunks)
    except Exception as exc:
        logger.error("Failed to load Chroma chunks for admin page: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load Chroma chunks: {exc}"
        )


@router.patch("/admin/users/{target_user_id}/role")
async def admin_update_user_role(
    target_user_id: str,
    update: AdminUserRoleUpdate,
    current_user: Dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """Admin-only: promote/demote user role."""
    users_repo = UsersRepository(db)
    await _require_admin(current_user, users_repo)

    if not ObjectId.is_valid(target_user_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id")

    if target_user_id == current_user["user_id"] and update.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot demote your own admin role"
        )

    target_user = await users_repo.get_user_by_id(target_user_id)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found")

    await users_repo.update_user_role_admin(target_user_id, update.role)
    refreshed_user = await users_repo.get_user_by_id(target_user_id)
    return {
        "message": f"Role updated to {update.role}",
        "user": _serialize_admin_user(refreshed_user),
    }


@router.patch("/admin/users/{target_user_id}/status")
async def admin_update_user_status(
    target_user_id: str,
    update: AdminUserStatusUpdate,
    current_user: Dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """Admin-only: activate or suspend user account."""
    users_repo = UsersRepository(db)
    await _require_admin(current_user, users_repo)

    if not ObjectId.is_valid(target_user_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id")

    if target_user_id == current_user["user_id"] and update.account_status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot suspend your own account"
        )

    target_user = await users_repo.get_user_by_id(target_user_id)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found")

    await users_repo.update_account_status_admin(target_user_id, update.account_status)
    refreshed_user = await users_repo.get_user_by_id(target_user_id)
    return {
        "message": f"Account status updated to {update.account_status}",
        "user": _serialize_admin_user(refreshed_user),
    }


@router.post("/admin/users/{target_user_id}/verification/reset")
async def admin_reset_user_verification(
    target_user_id: str,
    current_user: Dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """Admin-only: reset user verification to pending manual review."""
    users_repo = UsersRepository(db)
    await _require_admin(current_user, users_repo)

    if not ObjectId.is_valid(target_user_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id")

    target_user = await users_repo.get_user_by_id(target_user_id)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found")

    await users_repo.reset_verification_admin(target_user_id)
    refreshed_user = await users_repo.get_user_by_id(target_user_id)
    return {
        "message": "Verification reset successfully",
        "user": _serialize_admin_user(refreshed_user),
    }


@router.get("/profile", response_model=UserProfile)
async def get_user_profile(
    current_user: Dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """Get current user's complete profile"""
    users_repo = UsersRepository(db)
    user_service = UserService(users_repo)
    
    user = await user_service.get_user_profile(current_user["user_id"])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    return UserProfile(**_serialize_user(user))


@router.put("/profile", response_model=UserProfile)
async def update_user_profile(
    updates: UserProfileUpdate,
    current_user: Dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """Update user profile information"""
    users_repo = UsersRepository(db)
    user_service = UserService(users_repo)
    
    user = await user_service.update_user_profile(
        current_user["user_id"],
        updates.model_dump(exclude_unset=True)
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserProfile(**_serialize_user(user))


@router.get("/preferences", response_model=PreferencesResponse)
async def get_user_preferences(
    current_user: Dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """Get all user preferences"""
    users_repo = UsersRepository(db)
    user_service = UserService(users_repo)
    
    result = await user_service.get_user_preferences(current_user["user_id"])
    
    return PreferencesResponse(**result)


@router.post("/preferences", response_model=PreferenceResponse)
async def add_or_update_preference(
    preference: PreferenceCreate,
    current_user: Dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """Add or update a single preference"""
    users_repo = UsersRepository(db)
    user_service = UserService(users_repo)
    
    try:
        result = await user_service.add_preference(
            current_user["user_id"],
            preference.model_dump()
        )
        
        return PreferenceResponse(**result)
        
    except Exception as e:
        logger.error(f"Error adding preference: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/preferences/{key}", response_model=PreferenceResponse)
async def delete_preference(
    key: str,
    current_user: Dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """Delete a specific preference"""
    users_repo = UsersRepository(db)
    user_service = UserService(users_repo)
    
    try:
        result = await user_service.delete_preference(current_user["user_id"], key)
        return PreferenceResponse(**result)
        
    except Exception as e:
        logger.error(f"Error deleting preference: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/preferences/{key}/lock", response_model=PreferenceResponse)
async def lock_preference(
    key: str,
    lock_data: PreferenceLock,
    current_user: Dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """Lock or unlock a preference"""
    users_repo = UsersRepository(db)
    user_service = UserService(users_repo)
    
    try:
        result = await user_service.lock_preference(
            current_user["user_id"],
            key,
            lock_data.locked
        )
        
        return PreferenceResponse(**result)
        
    except Exception as e:
        logger.error(f"Error locking preference: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/preferences/reset", response_model=PreferenceResponse)
async def reset_preferences(
    current_user: Dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """Reset all user preferences"""
    users_repo = UsersRepository(db)
    user_service = UserService(users_repo)
    
    try:
        result = await user_service.reset_preferences(current_user["user_id"])
        return PreferenceResponse(**result)
        
    except Exception as e:
        logger.error(f"Error resetting preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/preferences/extract")
async def extract_preferences_manual(
    session_id: str,
    current_user: Dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Manually trigger preference extraction from a specific session
    Useful for extracting from older conversations
    """
    users_repo = UsersRepository(db)
    messages_repo = MessageRepository(db)
    extractor = AIPreferenceExtractor()
    
    try:
        # Get user data
        user = await users_repo.get_user_by_id(current_user["user_id"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get session messages
        messages = await messages_repo.get_session_messages(session_id)
        if not messages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No messages found in session"
            )
        
        # Verify session belongs to user
        first_message = messages[0] if messages else None
        if first_message and first_message.get("user_id") != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session does not belong to user"
            )
        
        # Format messages for extraction
        formatted_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]
        
        # Extract preferences
        extracted_prefs = await extractor.extract_preferences(
            formatted_messages,
            min_confidence=0.65
        )
        
        if not extracted_prefs:
            return {
                "success": True,
                "message": "No new preferences detected",
                "extracted": [],
                "total_preferences": len(user.get("preferences", []))
            }
        
        # Get existing preferences and merge
        existing_prefs = user.get("preferences", [])
        merged_prefs = extractor.merge_preferences(
            existing_prefs,
            extracted_prefs,
            max_preferences=50
        )
        
        # Update database
        success = await users_repo.update_preferences_bulk(
            current_user["user_id"], merged_prefs
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update preferences"
            )
        
        # Increment interaction count
        await users_repo.increment_interactions(current_user["user_id"])
        
        return {
            "success": True,
            "message": f"Extracted and merged {len(extracted_prefs)} new preferences",
            "extracted": [
                {
                    "category": p["category"],
                    "value": p["value"],
                    "confidence": p["confidence"],
                    "explanation": p.get("explanation", "")
                }
                for p in extracted_prefs
            ],
            "total_preferences": len(merged_prefs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting preferences: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/preferences/metadata")
async def get_preference_metadata(
    current_user: Dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """Get personalization metadata for current user"""
    users_repo = UsersRepository(db)
    
    try:
        metadata = await users_repo.get_personalization_metadata(current_user["user_id"])
        
        if metadata is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "success": True,
            "metadata": metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metadata: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/preferences/categories")
async def get_preference_categories():
    """Get all available preference categories and their possible values"""
    extractor = AIPreferenceExtractor()
    
    return {
        "success": True,
        "categories": extractor.PREFERENCE_CATEGORIES
    }


@router.post("/preferences/check-conflicts")
async def check_preference_conflicts(
    current_user: Dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Check all user preferences for conflicts
    Returns list of conflicting preference pairs
    """
    users_repo = UsersRepository(db)
    extractor = AIPreferenceExtractor()
    
    try:
        # Get existing preferences
        existing_preferences = await users_repo.get_user_preferences(current_user["user_id"])
        
        conflicts = []
        checked = set()  # Track which pairs we've already checked
        
        for i, pref1 in enumerate(existing_preferences):
            for j, pref2 in enumerate(existing_preferences):
                if i >= j:  # Skip same preference and already checked pairs
                    continue
                
                pair_key = f"{pref1.get('key')}:{pref2.get('key')}"
                if pair_key in checked:
                    continue
                checked.add(pair_key)
                
                # Check if pref2 conflicts with pref1
                conflict = extractor.detect_conflicts([pref1], pref2)
                if conflict:
                    conflicts.append({
                        "preference1": {
                            "key": pref1.get("key"),
                            "category": pref1.get("category"),
                            "value": pref1.get("value"),
                            "confidence": pref1.get("confidence")
                        },
                        "preference2": {
                            "key": pref2.get("key"),
                            "category": pref2.get("category"),
                            "value": pref2.get("value"),
                            "confidence": pref2.get("confidence")
                        }
                    })
        
        return {
            "success": True,
            "conflicts": conflicts,
            "total_conflicts": len(conflicts)
        }
        
    except Exception as e:
        logger.error(f"Error checking conflicts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/preferences/resolve-conflict")
async def resolve_preference_conflict(
    preference_key: str,
    action: str,  # 'keep' or 'delete'
    current_user: Dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Resolve a preference conflict by keeping or deleting a preference
    """
    users_repo = UsersRepository(db)
    
    try:
        if action not in ['keep', 'delete']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action must be 'keep' or 'delete'"
            )
        
        if action == 'delete':
            success = await users_repo.delete_preference(
                current_user["user_id"],
                preference_key
            )
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Preference not found"
                )
            
            return {
                "success": True,
                "message": f"Preference '{preference_key}' deleted"
            }
        else:  # keep
            return {
                "success": True,
                "message": f"Preference '{preference_key}' kept"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving conflict: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/preferences/manual", response_model=PreferenceResponse)
async def add_manual_preference(
    manual_pref: ManualPreferenceInput,
    current_user: Dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Add preference as freeform text - preserves user's exact words
    """
    users_repo = UsersRepository(db)
    user_service = UserService(users_repo)
    
    try:
        logger.info(f"Adding freeform manual preference for user {current_user['user_id']}")
        
        # Create a freeform preference with user's exact text
        # Use a simple key based on first few words
        words = manual_pref.preference_text.split()[:3]
        pref_key = "_".join(words).lower().replace(",", "").replace(".", "")
        
        preference_data = {
            "key": pref_key,
            "category": "custom",
            "value": manual_pref.preference_text[:50] + "..." if len(manual_pref.preference_text) > 50 else manual_pref.preference_text,
            "custom_instruction": manual_pref.preference_text,  # Store full text
            "confidence": 1.0,
            "source": "manual",
            "explanation": "User-provided freeform preference",
            "locked": True  # Auto-lock manual preferences
        }
        
        # Save the freeform preference
        result = await user_service.add_preference(
            current_user["user_id"],
            preference_data
        )
        
        return PreferenceResponse(
            message="Preference added successfully",
            preference=Preference(**preference_data)
        )
        
    except Exception as e:
        logger.error(f"Error adding manual preference: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process preference: {str(e)}"
        )

