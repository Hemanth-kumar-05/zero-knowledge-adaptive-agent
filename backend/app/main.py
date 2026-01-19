# FastAPI application entry point
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.api.routes import query_router, sessions_router, messages_router, health_router
from app.db.mongo import MongoDB
from config import config

@asynccontextmanager
async def lifespan(app: FastAPI):
    mongodb = MongoDB
    # Startup: Connect to MongoDB
    await mongodb.connect()
    print("MongoDB connected at startup")
    yield
    # Shutdown: Close MongoDB connection
    await mongodb.close()
    print("MongoDB connection closed at shutdown")

app = FastAPI(
    version=config.API_VERSION, 
    title=config.API_TITLE, 
    description=config.API_PHASE, 
    lifespan=lifespan
)

# Include API routers
app.include_router(query_router, prefix="/api/v1")
app.include_router(sessions_router, prefix="/api/v1")
app.include_router(messages_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")