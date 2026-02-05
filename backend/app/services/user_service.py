"""
User Service
Business logic for user management
"""

from typing import Optional, Dict, List
from datetime import datetime
from backend.app.db.repositories.users_repo import UsersRepository
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


class UserService:
    """Service for user management operations"""
    
    def __init__(self, users_repo: UsersRepository):
        self.users_repo = users_repo
    
    async def get_or_create_user(self, google_user_info: Dict) -> Dict:
        """
        Get existing user or create new one from Google OAuth data
        
        Args:
            google_user_info: User information from Google OAuth
            
        Returns:
            User document
        """
        google_id = google_user_info.get("sub") or google_user_info.get("id")
        email = google_user_info.get("email")
        
        if not google_id or not email:
            raise ValueError("Invalid Google user info: missing ID or email")
        
        # Try to find existing user by Google ID
        user = await self.users_repo.get_user_by_google_id(google_id)
        
        if user:
            # Update last login
            await self.users_repo.update_last_login(str(user["_id"]))
            logger.info(f"User logged in: {email}")
            return user
        
        # Create new user
        user_data = {
            "google_id": google_id,
            "email": email,
            "name": google_user_info.get("name", ""),
            "profile_picture": google_user_info.get("picture", "")
        }
        
        user = await self.users_repo.create_user(user_data)
        logger.info(f"New user created: {email}")
        
        return user
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile by ID"""
        user = await self.users_repo.get_user_by_id(user_id)
        
        if not user:
            return None
        
        # Convert ObjectId to string for JSON serialization
        user["_id"] = str(user["_id"])
        
        return user
    
    async def update_user_profile(self, user_id: str, updates: Dict) -> Optional[Dict]:
        """
        Update user profile
        
        Args:
            user_id: User's MongoDB _id
            updates: Dictionary of fields to update
            
        Returns:
            Updated user document
        """
        user = await self.users_repo.update_user_profile(user_id, updates)
        
        if user:
            user["_id"] = str(user["_id"])
            logger.info(f"User profile updated: {user_id}")
        
        return user
    
    async def get_user_preferences(self, user_id: str) -> Dict:
        """
        Get user preferences with metadata
        
        Returns:
            Dictionary with preferences array and metadata
        """
        preferences = await self.users_repo.get_user_preferences(user_id)
        user = await self.users_repo.get_user_by_id(user_id)
        
        return {
            "preferences": preferences,
            "total_count": len(preferences),
            "auto_extraction_enabled": True  # Can be extended to per-user setting
        }
    
    async def add_preference(self, user_id: str, preference: Dict) -> Dict:
        """
        Add a new preference for user
        
        Args:
            user_id: User's MongoDB _id
            preference: Preference data (key, value, etc.)
            
        Returns:
            Response with message and preference
        """
        # Check if preference key already exists
        existing_prefs = await self.users_repo.get_user_preferences(user_id)
        
        for pref in existing_prefs:
            if pref["key"] == preference["key"]:
                # Update existing preference instead
                await self.users_repo.update_preference(
                    user_id,
                    preference["key"],
                    {
                        "value": preference["value"],
                        "confidence": preference.get("confidence", 1.0),
                        "source": preference.get("source", "manual")
                    }
                )
                
                return {
                    "message": "Preference updated",
                    "preference": preference
                }
        
        # Add new preference
        success = await self.users_repo.add_preference(user_id, preference)
        
        if success:
            logger.info(f"Preference added for user {user_id}: {preference['key']}")
            return {
                "message": "Preference added",
                "preference": preference
            }
        
        raise Exception("Failed to add preference")
    
    async def update_preference(self, user_id: str, key: str, updates: Dict) -> Dict:
        """Update an existing preference"""
        success = await self.users_repo.update_preference(user_id, key, updates)
        
        if success:
            logger.info(f"Preference updated for user {user_id}: {key}")
            return {"message": "Preference updated", "key": key}
        
        raise Exception("Failed to update preference or preference not found")
    
    async def delete_preference(self, user_id: str, key: str) -> Dict:
        """Delete a preference"""
        success = await self.users_repo.delete_preference(user_id, key)
        
        if success:
            logger.info(f"Preference deleted for user {user_id}: {key}")
            return {"message": "Preference deleted", "deleted_key": key}
        
        raise Exception("Failed to delete preference or preference not found")
    
    async def reset_preferences(self, user_id: str) -> Dict:
        """Reset all preferences for user"""
        success = await self.users_repo.reset_preferences(user_id)
        
        if success:
            logger.info(f"All preferences reset for user {user_id}")
            return {"message": "All preferences reset", "preferences": []}
        
        raise Exception("Failed to reset preferences")
    
    async def lock_preference(self, user_id: str, key: str, locked: bool) -> Dict:
        """Lock or unlock a preference"""
        success = await self.users_repo.lock_preference(user_id, key, locked)
        
        if success:
            status = "locked" if locked else "unlocked"
            logger.info(f"Preference {status} for user {user_id}: {key}")
            return {"message": f"Preference {status}", "key": key, "locked": locked}
        
        raise Exception("Failed to lock/unlock preference or preference not found")
