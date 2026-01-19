# Sessions repository - handles chat_sessions collection
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
from datetime import datetime
from bson import ObjectId

class SessionRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.chat_sessions

    async def create_session(self, user_id: Optional[str] = None) -> str:
        """Create a new chat session and return its ID."""
        session_data = {
            "user_id": user_id,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "message_count": 0
        }
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

    async def get_all_sessions(self) -> list:
        """Get all sessions, optionally filtered by user_id."""
        cursor = self.collection.find().sort("updated_at", -1)
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

