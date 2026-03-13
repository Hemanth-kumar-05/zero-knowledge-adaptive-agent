"""
User Repository
Handles all database operations for users collection
"""

from typing import Optional, Dict, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId


class UsersRepository:
    """Repository for users collection operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["users"]
    
    async def create_indexes(self):
        """Create database indexes for users collection"""
        await self.collection.create_index("google_id", unique=True)
        await self.collection.create_index("email", unique=True)
    
    async def create_user(self, user_data: Dict) -> Dict:
        """
        Create a new user
        
        Args:
            user_data: User information including google_id, email, name, profile_picture
            
        Returns:
            Created user document
        """
        user_doc = {
            "google_id": user_data["google_id"],
            "email": user_data["email"],
            "name": user_data.get("name", ""),
            "profile_picture": user_data.get("profile_picture", ""),
            "role": user_data.get("role", "student"),
            "identity_verification": {
                "required": user_data.get("verification_required", True),
                "status": user_data.get("verification_status", "pending"),
                "verified_role": None,
                "verified_at": None,
                "provider": None,
                "confidence": None,
                "decision": None,
                "reasons": [],
                "updated_at": datetime.utcnow(),
            },
            "created_at": datetime.utcnow(),
            "last_login": datetime.utcnow(),
            "account_status": "active",
            "preferences": [],
            "facts": [],  # NEW: Initialize facts array
            "personalization_metadata": {
                "total_interactions": 0,
                "preference_updates_count": 0,
                "last_preference_update": None,
                "total_preferences": 0
            },
            "memory_settings": {  # NEW: Memory control settings
                "auto_extract_enabled": True,
                "require_confirmation": True,
                "default_retention": "permanent"
            }
        }
        
        result = await self.collection.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        
        return user_doc
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by MongoDB _id"""
        return await self.collection.find_one({"_id": ObjectId(user_id)})
    
    async def get_user_by_google_id(self, google_id: str) -> Optional[Dict]:
        """Get user by Google ID"""
        return await self.collection.find_one({"google_id": google_id})
    
    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        return await self.collection.find_one({"email": email})

    async def update_identity_verification(self, user_id: str, verification_update: Dict) -> bool:
        """Update identity verification state for a user."""
        set_data = {
            "identity_verification.updated_at": datetime.utcnow(),
        }
        for key, value in verification_update.items():
            set_data[f"identity_verification.{key}"] = value

        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": set_data}
        )
        return result.modified_count > 0

    async def set_role_and_verification(
        self,
        user_id: str,
        role: str,
        verification_update: Dict,
        name_override: Optional[str] = None,
    ) -> bool:
        """Atomically update role and verification result."""
        set_data = {
            "role": role,
            "identity_verification.updated_at": datetime.utcnow(),
        }
        if name_override:
            set_data["name"] = name_override

        for key, value in verification_update.items():
            set_data[f"identity_verification.{key}"] = value

        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": set_data}
        )
        return result.modified_count > 0
    
    async def update_last_login(self, user_id: str) -> bool:
        """Update user's last login timestamp"""
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    async def update_user_profile(self, user_id: str, updates: Dict) -> Optional[Dict]:
        """
        Update user profile information
        
        Args:
            user_id: User's MongoDB _id
            updates: Dictionary of fields to update (name, profile_picture)
            
        Returns:
            Updated user document
        """
        # Only allow specific fields to be updated
        allowed_fields = ["name", "profile_picture", "role"]
        update_data = {k: v for k, v in updates.items() if k in allowed_fields}
        
        if not update_data:
            return await self.get_user_by_id(user_id)
        
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": update_data},
            return_document=True
        )
        
        return result
    
    async def get_user_preferences(self, user_id: str) -> List[Dict]:
        """Get all preferences for a user"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return []
        return user.get("preferences", [])
    
    async def add_preference(self, user_id: str, preference: Dict) -> bool:
        """
        Add a new preference to user's preferences array
        
        Args:
            user_id: User's MongoDB _id
            preference: Preference object with key, value, confidence, source, etc.
            
        Returns:
            True if successful
        """
        preference_doc = {
            "key": preference["key"],
            "category": preference.get("category", preference["key"]),
            "value": preference["value"],
            "confidence": preference.get("confidence", 1.0),
            "source": preference.get("source", "manual"),
            "explanation": preference.get("explanation", ""),
            "custom_instruction": preference.get("custom_instruction"),  # Freeform text
            "extracted_from_message": preference.get("extracted_from_message"),
            "source_session_id": preference.get("source_session_id"),
            "source_message_id": preference.get("source_message_id"),
            "source_message_preview": preference.get("source_message_preview"),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "update_count": 1,
            "locked": preference.get("locked", False)
        }
        
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$push": {"preferences": preference_doc},
                "$inc": {"personalization_metadata.total_preferences": 1},
                "$set": {"personalization_metadata.last_preference_update": datetime.utcnow()}
            }
        )
        
        return result.modified_count > 0
    
    async def update_preference(self, user_id: str, key: str, updates: Dict) -> bool:
        """
        Update an existing preference
        
        Args:
            user_id: User's MongoDB _id
            key: Preference key to update
            updates: Dictionary of fields to update
            
        Returns:
            True if successful
        """
        set_fields = {}
        for field, value in updates.items():
            set_fields[f"preferences.$.{field}"] = value
        
        set_fields["preferences.$.updated_at"] = datetime.utcnow()
        
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id), "preferences.key": key},
            {
                "$set": set_fields,
                "$inc": {"preferences.$.update_count": 1}
            }
        )
        
        return result.modified_count > 0
    
    async def delete_preference(self, user_id: str, key: str) -> bool:
        """Delete a preference from user's preferences array"""
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$pull": {"preferences": {"key": key}},
                "$inc": {"personalization_metadata.total_preferences": -1}
            }
        )
        
        return result.modified_count > 0
    
    async def reset_preferences(self, user_id: str) -> bool:
        """Clear all preferences for a user"""
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "preferences": [],
                    "personalization_metadata.total_preferences": 0
                }
            }
        )
        
        return result.modified_count > 0
    
    async def lock_preference(self, user_id: str, key: str, locked: bool) -> bool:
        """Lock or unlock a preference to prevent/allow automatic updates"""
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id), "preferences.key": key},
            {"$set": {"preferences.$.locked": locked}}
        )
        
        return result.modified_count > 0
    
    async def update_preferences_bulk(self, user_id: str, preferences: List[Dict]) -> bool:
        """
        Replace entire preferences array with new list
        Used after preference extraction and merging
        
        Args:
            user_id: User's MongoDB _id
            preferences: Complete new preferences array
            
        Returns:
            True if successful
        """
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "preferences": preferences,
                    "personalization_metadata.total_preferences": len(preferences),
                    "personalization_metadata.last_preference_update": datetime.utcnow()
                },
                "$inc": {
                    "personalization_metadata.preference_updates_count": 1
                }
            }
        )
        
        return result.modified_count > 0
    
    async def get_preferences_for_extraction(self, user_id: str) -> List[Dict]:
        """
        Get only non-locked preferences for extraction merging
        
        Args:
            user_id: User's MongoDB _id
            
        Returns:
            List of non-locked preferences
        """
        user = await self.collection.find_one(
            {"_id": ObjectId(user_id)},
            {"preferences": 1}
        )
        
        if not user:
            return []
        
        # Return all preferences (merging logic will handle locked ones)
        return user.get("preferences", [])
    
    async def increment_interactions(self, user_id: str) -> bool:
        """
        Increment total interaction count for personalization metrics
        
        Args:
            user_id: User's MongoDB _id
            
        Returns:
            True if successful
        """
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$inc": {"personalization_metadata.total_interactions": 1}
            }
        )
        
        return result.modified_count > 0
    
    async def get_personalization_metadata(self, user_id: str) -> Optional[Dict]:
        """
        Get user's personalization metadata for rate limiting checks
        
        Args:
            user_id: User's MongoDB _id
            
        Returns:
            Personalization metadata dict or None
        """
        user = await self.collection.find_one(
            {"_id": ObjectId(user_id)},
            {"personalization_metadata": 1}
        )
        
        if not user:
            return None
        
        return user.get("personalization_metadata", {})
    
    # ==================== Fact Memory Management ====================
    
    async def get_user_facts(self, user_id: str) -> List[Dict]:
        """Get all facts stored for a user"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return []
        return user.get("facts", [])
    
    async def add_fact(self, user_id: str, fact: Dict) -> bool:
        """
        Add a new fact to user's facts array
        
        Args:
            user_id: User's MongoDB _id
            fact: Fact object with category, key, value, retention, confidence, etc.
            
        Returns:
            True if successful
        """
        fact_doc = {
            "category": fact["category"],
            "key": fact["key"],
            "value": fact["value"],
            "retention": fact.get("retention", "permanent"),
            "locked": fact.get("locked", False),
            "confidence": fact.get("confidence", 1.0),
            "explanation": fact.get("explanation", ""),
            "source": fact.get("source", "conversation"),
            "extracted_at": fact.get("extracted_at", datetime.utcnow()),
            "extraction_method": fact.get("extraction_method"),
            "llm_provider": fact.get("llm_provider"),
            "llm_model": fact.get("llm_model"),
            "confirmed_by_user": fact.get("confirmed_by_user", False),
            "confirmed_at": fact.get("confirmed_at")
        }
        
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$push": {"facts": fact_doc}}
        )
        
        return result.modified_count > 0
    
    async def update_fact(self, user_id: str, key: str, updates: Dict) -> bool:
        """
        Update an existing fact
        
        Args:
            user_id: User's MongoDB _id
            key: Fact key to update
            updates: Dictionary of fields to update
            
        Returns:
            True if successful
        """
        # Build update document
        set_updates = {}
        for update_key, value in updates.items():
            set_updates[f"facts.$.{update_key}"] = value
        
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id), "facts.key": key},
            {"$set": set_updates}
        )
        
        return result.modified_count > 0
    
    async def delete_fact(self, user_id: str, key: str) -> bool:
        """Delete a specific fact by key"""
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$pull": {"facts": {"key": key}}}
        )
        
        return result.modified_count > 0
    
    async def delete_all_facts(self, user_id: str, category: Optional[str] = None) -> bool:
        """
        Delete all facts for a user, optionally filtered by category
        
        Args:
            user_id: User's MongoDB _id
            category: Optional category filter
            
        Returns:
            True if successful
        """
        if category:
            # Delete only facts in specified category
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$pull": {"facts": {"category": category}}}
            )
        else:
            # Delete all facts
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"facts": []}}
            )
        
        return result.modified_count > 0
    
    async def lock_fact(self, user_id: str, key: str, locked: bool) -> bool:
        """Lock or unlock a fact to prevent/allow updates"""
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id), "facts.key": key},
            {"$set": {"facts.$.locked": locked}}
        )
        
        return result.modified_count > 0

    # ==================== Admin User Management ====================

    async def list_users_for_admin(self, limit: int = 500) -> List[Dict]:
        """List users for admin dashboard (newest first)."""
        cursor = self.collection.find({}).sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def update_user_role_admin(self, user_id: str, role: str) -> bool:
        """Admin action: update a user's role."""
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "role": role,
                    "identity_verification.verified_role": role,
                    "identity_verification.updated_at": datetime.utcnow(),
                }
            }
        )
        return result.modified_count > 0

    async def update_account_status_admin(self, user_id: str, account_status: str) -> bool:
        """Admin action: activate/suspend a user account."""
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"account_status": account_status}}
        )
        return result.modified_count > 0

    async def reset_verification_admin(self, user_id: str) -> bool:
        """Admin action: reset identity verification to pending."""
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "identity_verification.required": True,
                    "identity_verification.status": "pending",
                    "identity_verification.verified_role": None,
                    "identity_verification.verified_at": None,
                    "identity_verification.provider": "manual_admin_reset",
                    "identity_verification.confidence": None,
                    "identity_verification.decision": "manual_review",
                    "identity_verification.reasons": ["Verification reset by admin"],
                    "identity_verification.updated_at": datetime.utcnow(),
                }
            }
        )
        return result.modified_count > 0
