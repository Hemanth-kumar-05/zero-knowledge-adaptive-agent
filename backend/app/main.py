# FastAPI application entry point
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.routes import query_router, sessions_router, messages_router, health_router, memory_router
from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.db.mongo import MongoDB
from app.db.repositories.users_repo import UsersRepository
from config import config

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to MongoDB
    await MongoDB.connect()
    print("MongoDB connected at startup")
    
    # Create indexes for users collection
    db = MongoDB.get_db()
    users_repo = UsersRepository(db)
    await users_repo.create_indexes()
    print("User indexes created")
    
    yield
    # Shutdown: Close MongoDB connection
    await MongoDB.close()
    print("MongoDB connection closed at shutdown")

app = FastAPI(
    version=config.API_VERSION, 
    title=config.API_TITLE, 
    description=config.API_PHASE, 
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include API routers
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api/v1")
app.include_router(memory_router)
app.include_router(query_router, prefix="/api/v1")
app.include_router(sessions_router, prefix="/api/v1")
app.include_router(messages_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")