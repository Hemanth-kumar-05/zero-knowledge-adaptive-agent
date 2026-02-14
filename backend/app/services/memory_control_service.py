"""
Memory Control Service
Manages user facts with consent and control mechanisms
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from app.db.repositories.users_repo import UsersRepository

logger = logging.getLogger(__name__)


class MemoryController:
    """Manages user fact memory with user control"""
    
    def __init__(self, users_repo: UsersRepository):
        self.users_repo = users_repo
    
    async def store_fact(
        self,
        user_id: str,
        fact: Dict,
        require_confirmation: bool = True
    ) -> bool:
        """
        Store a fact with user consent
        
        Args:
            user_id: User's MongoDB ID
            fact: Fact dictionary from extraction
            require_confirmation: Whether user confirmation is needed
            
        Returns:
            True if successful
        """
        try:
            # Check if fact already exists
            existing_facts = await self.users_repo.get_user_facts(user_id)
            
            for existing in existing_facts:
                if existing.get("key") == fact.get("key"):
                    # Update existing fact
                    return await self.update_fact(user_id, fact.get("key"), fact)
            
            # Store new fact
            success = await self.users_repo.add_fact(user_id, fact)
            
            if success:
                logger.info(
                    f"✅ Stored fact for user {user_id}: "
                    f"{fact.get('category')}.{fact.get('key')} = {fact.get('value')}"
                )
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error storing fact: {e}", exc_info=True)
            return False
    
    async def store_facts_bulk(
        self,
        user_id: str,
        facts: List[Dict],
        require_confirmation: bool = True
    ) -> Dict[str, int]:
        """
        Store multiple facts at once
        
        Returns:
            Dict with counts: {"stored": N, "updated": M, "failed": K}
        """
        counts = {"stored": 0, "updated": 0, "failed": 0}
        
        for fact in facts:
            # Check if exists
            existing_facts = await self.users_repo.get_user_facts(user_id)
            exists = any(f.get("key") == fact.get("key") for f in existing_facts)
            
            success = await self.store_fact(user_id, fact, require_confirmation)
            
            if success:
                if exists:
                    counts["updated"] += 1
                else:
                    counts["stored"] += 1
            else:
                counts["failed"] += 1
        
        return counts
    
    async def update_fact(
        self,
        user_id: str,
        key: str,
        updates: Dict
    ) -> bool:
        """
        Update an existing fact
        
        Args:
            user_id: User's MongoDB ID
            key: Fact key to update
            updates: New values for the fact
            
        Returns:
            True if successful
        """
        try:
            success = await self.users_repo.update_fact(user_id, key, updates)
            
            if success:
                logger.info(f"✅ Updated fact for user {user_id}: {key}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error updating fact: {e}", exc_info=True)
            return False
    
    async def delete_fact(
        self,
        user_id: str,
        key: str
    ) -> bool:
        """
        Delete a specific fact
        
        Args:
            user_id: User's MongoDB ID
            key: Fact key to delete
            
        Returns:
            True if successful
        """
        try:
            success = await self.users_repo.delete_fact(user_id, key)
            
            if success:
                logger.info(f"🗑️ Deleted fact for user {user_id}: {key}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error deleting fact: {e}", exc_info=True)
            return False
    
    async def delete_all_facts(
        self,
        user_id: str,
        category: Optional[str] = None
    ) -> bool:
        """
        Delete all facts for a user, optionally filtered by category
        
        Args:
            user_id: User's MongoDB ID
            category: Optional category filter (e.g., "concern", "identity")
            
        Returns:
            True if successful
        """
        try:
            success = await self.users_repo.delete_all_facts(user_id, category)
            
            if success:
                category_str = f" in category '{category}'" if category else ""
                logger.info(f"🗑️ Deleted all facts for user {user_id}{category_str}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error deleting facts: {e}", exc_info=True)
            return False
    
    async def get_user_memory(
        self,
        user_id: str,
        include_metadata: bool = False
    ) -> List[Dict]:
        """
        Get all stored facts for a user
        
        Args:
            user_id: User's MongoDB ID
            include_metadata: Include extraction metadata
            
        Returns:
            List of facts
        """
        try:
            facts = await self.users_repo.get_user_facts(user_id)
            
            if not include_metadata:
                # Strip internal metadata for user display
                facts = [
                    {
                        "category": f.get("category"),
                        "key": f.get("key"),
                        "value": f.get("value"),
                        "retention": f.get("retention"),
                        "confirmed": f.get("confirmed_by_user", False),
                        "locked": f.get("locked", False),
                        "created_at": f.get("extracted_at")
                    }
                    for f in facts
                ]
            
            return facts
            
        except Exception as e:
            logger.error(f"❌ Error getting user memory: {e}", exc_info=True)
            return []
    
    async def confirm_fact(
        self,
        user_id: str,
        key: str
    ) -> bool:
        """
        Mark a fact as confirmed by the user
        
        Args:
            user_id: User's MongoDB ID
            key: Fact key to confirm
            
        Returns:
            True if successful
        """
        try:
            updates = {
                "confirmed_by_user": True,
                "confirmed_at": datetime.utcnow()
            }
            
            success = await self.users_repo.update_fact(user_id, key, updates)
            
            if success:
                logger.info(f"✅ User confirmed fact: {key}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error confirming fact: {e}", exc_info=True)
            return False
    
    async def lock_fact(
        self,
        user_id: str,
        key: str,
        locked: bool = True
    ) -> bool:
        """
        Lock or unlock a fact (prevent/allow updates)
        
        Args:
            user_id: User's MongoDB ID
            key: Fact key to lock/unlock
            locked: True to lock, False to unlock
            
        Returns:
            True if successful
        """
        try:
            updates = {"locked": locked}
            success = await self.users_repo.update_fact(user_id, key, updates)
            
            if success:
                action = "locked" if locked else "unlocked"
                logger.info(f"🔒 User {action} fact: {key}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error locking/unlocking fact: {e}", exc_info=True)
            return False
    
    async def set_retention_policy(
        self,
        user_id: str,
        key: str,
        retention: str
    ) -> bool:
        """
        Update retention policy for a fact
        
        Args:
            user_id: User's MongoDB ID
            key: Fact key
            retention: "permanent", "semester", or "session"
            
        Returns:
            True if successful
        """
        if retention not in ["permanent", "semester", "session"]:
            logger.error(f"Invalid retention policy: {retention}")
            return False
        
        try:
            updates = {"retention": retention}
            success = await self.users_repo.update_fact(user_id, key, updates)
            
            if success:
                logger.info(f"⏱️ Updated retention policy for {key}: {retention}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error setting retention policy: {e}", exc_info=True)
            return False
    
    async def cleanup_expired_facts(self, user_id: str) -> int:
        """
        Remove facts that have expired based on retention policy
        
        Args:
            user_id: User's MongoDB ID
            
        Returns:
            Number of facts deleted
        """
        try:
            facts = await self.users_repo.get_user_facts(user_id)
            deleted_count = 0
            
            for fact in facts:
                should_delete = False
                retention = fact.get("retention", "permanent")
                extracted_at = fact.get("extracted_at")
                
                if retention == "session":
                    # Session facts expire after 24 hours
                    if isinstance(extracted_at, datetime):
                        age = datetime.utcnow() - extracted_at
                        if age > timedelta(hours=24):
                            should_delete = True
                
                elif retention == "semester":
                    # Semester facts expire after 6 months
                    if isinstance(extracted_at, datetime):
                        age = datetime.utcnow() - extracted_at
                        if age > timedelta(days=180):
                            should_delete = True
                
                # Permanent facts never expire
                
                if should_delete:
                    success = await self.delete_fact(user_id, fact.get("key"))
                    if success:
                        deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"🧹 Cleaned up {deleted_count} expired fact(s) for user {user_id}")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up expired facts: {e}", exc_info=True)
            return 0
    
    async def build_user_context(self, user_id: str) -> str:
        """
        Build a context string from user facts for personalized responses
        
        Args:
            user_id: User's MongoDB ID
            
        Returns:
            Formatted context string
        """
        # Fetch user's facts from database
        facts = await self.users_repo.get_user_facts(user_id)
        
        if not facts:
            return ""
        
        # Group facts by category
        identity_facts = [f for f in facts if f.get("category") == "identity"]
        academic_facts = [f for f in facts if f.get("category") == "academic_context"]
        
        context_parts = []
        
        # Build identity context
        if identity_facts:
            identity_info = {}

            for fact in identity_facts:
                identity_info[fact.get("key")] = fact.get("value")
            
            if identity_info.get("name"):
                context_parts.append(f"User's name is {identity_info['name']}")
            
            if identity_info.get("year"):
                context_parts.append(f"in {identity_info['year']} year")
            
            if identity_info.get("major"):
                context_parts.append(f"studying {identity_info['major']}")
        
        # Build academic context
        if academic_facts:
            for fact in academic_facts:
                key = fact.get("key")
                value = fact.get("value")
                
                if key == "current_courses" and isinstance(value, list):
                    courses_str = ", ".join(value)
                    context_parts.append(f"taking courses: {courses_str}")
                
                elif key == "advisor":
                    context_parts.append(f"advised by {value}")
        
        if context_parts:
            return "CONTEXT: " + ", ".join(context_parts) + "."
        
        return ""


# Factory function to create controller with repository
def create_memory_controller(users_repo: UsersRepository) -> MemoryController:
    """Create a memory controller instance"""
    return MemoryController(users_repo)
