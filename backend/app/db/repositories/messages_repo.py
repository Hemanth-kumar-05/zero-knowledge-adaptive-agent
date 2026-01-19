# Messages repository - handles chat_messages collection
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, Literal
from datetime import datetime
from bson import ObjectId

class MessageRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.chat_messages

    async def create_message(
        self,
        session_id: str,
        role: Literal["user", "assistant"],
        content: str,
        metadata: Optional[dict] = None
    ) -> str:
        """Create a new message in a session."""
        message_data = {
            "session_id": ObjectId(session_id),
            "role": role,
            "content": content,
            "timestamp": datetime.now(),
            "metadata": metadata or {}
        }
        result = await self.collection.insert_one(message_data)
        return str(result.inserted_id)

    async def get_session_messages(self, session_id: str) -> list:
        """Get all messages for a session, sorted by timestamp."""
        cursor = self.collection.find({"session_id": ObjectId(session_id)}).sort("timestamp", 1)
        messages = await cursor.to_list(length=None)
        
        for message in messages:
            message["_id"] = str(message["_id"])
            message["session_id"] = str(message["session_id"])
        return messages
