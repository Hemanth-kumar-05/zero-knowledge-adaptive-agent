# Query logs repository - handles query_logs collection
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
from datetime import datetime
from bson import ObjectId

class QueryLogRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.query_logs

    async def log_query(self, data: dict) -> str:
        # Convert session_id to ObjectId if it's a string
        if "session_id" in data and isinstance(data["session_id"], str):
            data["session_id"] = ObjectId(data["session_id"])
        
        if "timestamp" not in data:
            data["timestamp"] = datetime.now()
        
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)

    async def get_query_log(self, log_id: str) -> Optional[dict]:
        return await self.collection.find_one({"_id": ObjectId(log_id)})
    
    async def get_session_logs(self, session_id: str) -> list:
        cursor = self.collection.find({"session_id": ObjectId(session_id)}).sort("timestamp", -1)
        return await cursor.to_list(length=None)

    async def delete_session_logs(self, session_id: str) -> int:
        """Delete all query logs for a session."""
        result = await self.collection.delete_many({"session_id": ObjectId(session_id)})
        return result.deleted_count