# Health check service
import time
from datetime import datetime
from app.db.repositories.health_repo import health_repo
from config import config


class HealthService:
    """Service layer for health checks"""
    
    def __init__(self):
        self.start_time = time.time()
    
    async def check_health(self) -> dict:
        """
        Comprehensive health check of all components.
        Returns overall health status and individual component statuses.
        """
        components = {}
        
        # Check MongoDB
        mongo_health = await health_repo.check_mongodb()
        components["mongodb"] = mongo_health
        
        # Check ChromaDB
        chroma_health = await health_repo.check_chromadb()
        components["chromadb"] = chroma_health
        
        # Check RAG Pipeline
        rag_health = await health_repo.check_rag_pipeline()
        components["rag_pipeline"] = rag_health
        
        # Determine overall status
        overall_status = self._determine_overall_status(components)
        
        # Calculate uptime
        uptime = time.time() - self.start_time
        
        return {
            "status": overall_status,
            "timestamp": datetime.now(),
            "version": config.API_VERSION,
            "components": components,
            "uptime_seconds": round(uptime, 2)
        }
    
    async def check_liveness(self) -> dict:
        """
        Liveness probe - checks if application is alive.
        Always returns true unless the process is dead.
        """
        return {
            "alive": True,
            "timestamp": datetime.now()
        }
    
    async def check_readiness(self) -> dict:
        """
        Readiness probe - checks if application is ready to serve traffic.
        Checks critical dependencies: MongoDB and ChromaDB.
        """
        # Check only critical components
        mongo_health = await health_repo.check_mongodb()
        chroma_health = await health_repo.check_chromadb()
        
        # Application is ready if both MongoDB and ChromaDB are healthy
        is_ready = (
            mongo_health["status"] == "healthy" and 
            chroma_health["status"] == "healthy"
        )
        
        message = "Ready" if is_ready else "Not ready - check component health"
        
        return {
            "ready": is_ready,
            "timestamp": datetime.now(),
            "message": message
        }
    
    def _determine_overall_status(self, components: dict) -> str:
        """
        Determine overall health based on component statuses.
        - healthy: All components healthy
        - degraded: Some non-critical components unhealthy
        - unhealthy: Critical components (MongoDB, ChromaDB) unhealthy
        """
        statuses = [comp["status"] for comp in components.values()]
        
        # If any component is unhealthy, check if it's critical
        if "unhealthy" in statuses:
            critical_components = ["mongodb", "chromadb"]
            for comp_name in critical_components:
                if comp_name in components and components[comp_name]["status"] == "unhealthy":
                    return "unhealthy"
            return "degraded"
        
        # If any component is degraded
        if "degraded" in statuses:
            return "degraded"
        
        return "healthy"


# Singleton instance
health_service = HealthService()
