# MongoDB connection and client
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure
import certifi

from config import config

class MongoDB:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None

    @classmethod
    async def connect(cls):
        try:
            cls.client = AsyncIOMotorClient(
                config.MONGODB_URI,
                tls=True,
                tlsCAFile=certifi.where(),
                serverSelectionTimeoutMS=20000
            )

            await cls.client.admin.command("ping")
            cls.db = cls.client[config.MONGODB_DB_NAME]
            print("✅ Connected to MongoDB Atlas")

        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            raise

    @classmethod
    async def close(cls):
        if cls.client:
            cls.client.close()
            print("MongoDB connection closed")

    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        if cls.db is None:
            raise Exception("Database not connected. Call connect() first.")
        return cls.db

# Global MongoDB instance
mongodb = MongoDB()