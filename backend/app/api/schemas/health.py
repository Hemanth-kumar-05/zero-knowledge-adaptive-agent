# Health check schemas
from pydantic import BaseModel, ConfigDict
from typing import Dict, Optional
from datetime import datetime


class ComponentHealth(BaseModel):
    """Health status of a component"""
    status: str  # "healthy", "degraded", "unhealthy"
    message: Optional[str] = None
    latency_ms: Optional[float] = None
    details: Optional[Dict] = None


class HealthResponse(BaseModel):
    """Overall health check response"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: datetime
    version: str
    components: Dict[str, ComponentHealth]
    uptime_seconds: Optional[float] = None


class LivenessResponse(BaseModel):
    """Liveness probe response"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    alive: bool
    timestamp: datetime


class ReadinessResponse(BaseModel):
    """Readiness probe response"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    ready: bool
    timestamp: datetime
    message: Optional[str] = None
