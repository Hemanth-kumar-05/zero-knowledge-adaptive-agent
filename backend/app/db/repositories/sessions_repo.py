# Sessions repository - handles chat_sessions collection
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
from datetime import datetime
from bson import ObjectId

class SessionRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.chat_sessions

    async def create_session(
        self, 
        user_id: Optional[str] = None,
        extension_id: Optional[str] = None,
        extension_name: Optional[str] = None,
        extension_icon: Optional[str] = None,
        extension_welcome_message: Optional[str] = None,
        extension_input_placeholder: Optional[str] = None
    ) -> str:
        """Create a new chat session and return its ID."""
        session_data = {
            "user_id": user_id,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "message_count": 0
        }
        
        # Add extension info if provided
        if extension_id:
            session_data["extension_id"] = extension_id
            session_data["extension_name"] = extension_name
            session_data["extension_icon"] = extension_icon
            session_data["extension_welcome_message"] = extension_welcome_message
            session_data["extension_input_placeholder"] = extension_input_placeholder
        
        result = await self.collection.insert_one(session_data)
        return str(result.inserted_id)

    async def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        try:
            count = await self.collection.count_documents({"_id": ObjectId(session_id)}, limit=1)
            return count > 0
        except Exception:
            return False

    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get session by ID."""
        session = await self.collection.find_one({"_id": ObjectId(session_id)})
        if session:
            session["_id"] = str(session["_id"])
        return session

    async def get_all_sessions(self, user_id: Optional[str] = None) -> list:
        """Get all sessions, optionally filtered by user_id."""
        query = {}
        if user_id:
            query["user_id"] = user_id
        
        cursor = self.collection.find(query).sort("updated_at", -1)
        sessions = await cursor.to_list(length=None)
        
        for session in sessions:
            session["_id"] = str(session["_id"])
        return sessions

    async def update_session_timestamp(self, session_id: str) -> bool:
        """Update the updated_at timestamp."""
        result = await self.collection.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": {"updated_at": datetime.now()}}
        )
        return result.modified_count > 0

    async def increment_message_count(self, session_id: str) -> bool:
        """Increment message count for a session."""
        result = await self.collection.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$inc": {"message_count": 1},
                "$set": {"updated_at": datetime.now()}
            }
        )
        return result.modified_count > 0

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session by ID."""
        result = await self.collection.delete_one({"_id": ObjectId(session_id)})
        return result.deleted_count > 0

    async def update_metadata(self, session_id: str, metadata: dict) -> bool:
        """Update session metadata (for storing temporary data like pending claims)."""
        result = await self.collection.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "metadata": metadata,
                    "updated_at": datetime.now()
                }
            }
        )
        return result.modified_count > 0

    async def get_metadata(self, session_id: str) -> Optional[dict]:
        """Get session metadata."""
        session = await self.collection.find_one(
            {"_id": ObjectId(session_id)},
            {"metadata": 1}
        )
        return session.get("metadata") if session else None

