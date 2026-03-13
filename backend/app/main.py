# FastAPI application entry point
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.routes import query_router, sessions_router, messages_router, health_router, memory_router
from app.api.routes.access.auth import router as auth_router
from app.api.routes.access.users import router as users_router
from app.api.routes.extensions.extensions import router as extensions_router
from app.db.mongo import MongoDB
from app.db.repositories.users_repo import UsersRepository
from app.db.repositories.extensions_repo import ExtensionsRepository
from config import config

# Phase 3 - Policy Unlearning imports (conditional)
if config.ENABLE_POLICY_UNLEARNING:
    from app.db.repositories.policy_documents_repo import PolicyDocumentsRepository
    from app.db.repositories.policy_update_tickets_repo import PolicyUpdateTicketsRepository
    from app.db.repositories.policy_change_audit_repo import PolicyChangeAuditRepository
    from app.api.routes.policy.policy_updates import router as policy_updates_router
    from app.api.routes.policy.policy_proofs import router as policy_proofs_router

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
    
    # Create indexes for extensions collection
    extensions_repo = ExtensionsRepository(db)
    await extensions_repo.create_indexes()
    print("Extensions indexes created")
    
    # Phase 3 - Create indexes for policy unlearning collections (conditional)
    if config.ENABLE_POLICY_UNLEARNING:
        print("Phase 3 Policy Unlearning ENABLED - Initializing collections...")
        policy_docs_repo = PolicyDocumentsRepository(db)
        policy_tickets_repo = PolicyUpdateTicketsRepository(db)
        policy_audit_repo = PolicyChangeAuditRepository(db)
        
        await policy_docs_repo.create_indexes()
        await policy_tickets_repo.create_indexes()
        await policy_audit_repo.create_indexes()
        print("Phase 3 collections initialized")
    
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
app.include_router(extensions_router, prefix="/api/v1")
app.include_router(memory_router)
app.include_router(query_router, prefix="/api/v1")
app.include_router(sessions_router, prefix="/api/v1")
app.include_router(messages_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")

# Phase 3 - Policy Updates router (conditional)
if config.ENABLE_POLICY_UNLEARNING:
    app.include_router(policy_updates_router, prefix="/api/v1/policy-updates")
    app.include_router(policy_proofs_router, prefix="/api/v1")