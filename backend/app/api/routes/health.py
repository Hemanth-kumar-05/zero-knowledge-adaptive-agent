# GET /health endpoint
from fastapi import APIRouter, HTTPException
from app.api.schemas.health import HealthResponse, LivenessResponse, ReadinessResponse
from app.services.health_service import health_service

health_router = APIRouter(prefix="/health", tags=["health"])


@health_router.get("/", response_model=HealthResponse)
async def health_check():
    """
    Comprehensive health check endpoint.
    Checks all critical components: MongoDB, ChromaDB, RAG Pipeline.
    """
    result = await health_service.check_health()
    
    # If overall status is unhealthy, return 503
    if result["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=result)
    
    return result


@health_router.get("/live", response_model=LivenessResponse)
async def liveness_probe():
    """
    Kubernetes liveness probe.
    Returns 200 if the application is alive and running.
    """
    return await health_service.check_liveness()


@health_router.get("/ready", response_model=ReadinessResponse)
async def readiness_probe():
    """
    Kubernetes readiness probe.
    Returns 200 if the application is ready to serve traffic.
    Checks MongoDB and ChromaDB connectivity.
    """
    result = await health_service.check_readiness()
    
    # If not ready, return 503
    if not result["ready"]:
        raise HTTPException(status_code=503, detail=result)
    
    return result
