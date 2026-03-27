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
        user_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        applied_preferences: Optional[list] = None,
        extracted_preferences: Optional[list] = None
    ) -> str:
        """Create a new message in a session."""
        message_data = {
            "session_id": ObjectId(session_id),
            "user_id": user_id,
            "role": role,
            "content": content,
            "timestamp": datetime.now(),
            "metadata": metadata or {},
            "applied_preferences": applied_preferences or [],
            "extracted_preferences": extracted_preferences or [],
            "has_feedback": False
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

    async def get_message_by_id(self, message_id: str) -> Optional[dict]:
        """Get a single message by id."""
        message = await self.collection.find_one({"_id": ObjectId(message_id)})
        if not message:
            return None
        message["_id"] = str(message["_id"])
        message["session_id"] = str(message["session_id"])
        return message

    async def update_message_metadata(self, message_id: str, metadata_updates: dict) -> bool:
        """Merge metadata fields into an existing message."""
        update_fields = {f"metadata.{key}": value for key, value in metadata_updates.items()}
        result = await self.collection.update_one(
            {"_id": ObjectId(message_id)},
            {"$set": update_fields}
        )
        return result.modified_count > 0 or result.matched_count > 0

    async def delete_session_messages(self, session_id: str) -> int:
        """Delete all messages for a session."""
        result = await self.collection.delete_many({"session_id": ObjectId(session_id)})
        return result.deleted_count
