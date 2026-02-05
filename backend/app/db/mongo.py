from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import certifi
from config import config


class MongoDB:
    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorDatabase | None = None

    @classmethod
    async def connect(cls):
        try:
            cls.client = AsyncIOMotorClient(
                config.MONGODB_URI,
                tls=True,
                tlsCAFile=certifi.where(),
                retryWrites=True,
                serverSelectionTimeoutMS=5000,
                # For development: allow self-signed certificates
                tlsAllowInvalidCertificates=True,
                tlsAllowInvalidHostnames=True
            )

            await cls.client.admin.command("ping")
            cls.db = cls.client[config.MONGODB_DB_NAME]
            print("✅ Connected to MongoDB Atlas")

        except Exception as e:
            print("❌ MongoDB connection failed")
            print(e)
            raise

    @classmethod
    async def close(cls):
        if cls.client:
            cls.client.close()

    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        if cls.db is None:
            raise RuntimeError("Database not connected")
        return cls.db


mongodb = MongoDB()


# Dependency function for FastAPI
async def get_db() -> AsyncIOMotorDatabase:
    """
    Get database instance (async)
    Usage: db = Depends(get_db)
    """
    return MongoDB.get_db()