# Health check repository - performs actual health checks
import time
import asyncio
from typing import Dict
from app.db.mongo import MongoDB
from app.core.rag_adapter import rag_adapter
from config import config


class HealthRepository:
    """Repository for health check operations"""
    
    async def check_mongodb(self) -> Dict:
        """Check MongoDB connection and responsiveness"""
        start_time = time.time()
        
        try:
            # Attempt to ping MongoDB
            db = MongoDB.get_db()
            await db.client.admin.command('ping')
            
            latency = round((time.time() - start_time) * 1000, 2)
            
            # Get additional details
            server_info = await db.client.server_info()
            
            return {
                "status": "healthy",
                "message": "MongoDB is connected and responsive",
                "latency_ms": latency,
                "details": {
                    "version": server_info.get("version"),
                    "database": db.name
                }
            }
        except Exception as e:
            latency = round((time.time() - start_time) * 1000, 2)
            return {
                "status": "unhealthy",
                "message": f"MongoDB connection failed: {str(e)}",
                "latency_ms": latency,
                "details": {"error": str(e)}
            }
    
    async def check_chromadb(self) -> Dict:
        """Check ChromaDB connection and data availability"""
        start_time = time.time()
        
        try:
            # Run in thread pool since ChromaDB is synchronous
            def _check_chroma():
                # Access the retriever from RAG adapter
                retriever = rag_adapter.rag_pipeline.retriever
                
                # Check if collection exists and has data
                collection = retriever.collection
                count = collection.count()
                
                return {
                    "collection_name": retriever.collection_name,
                    "document_count": count,
                    **config.get_chroma_connection_info(retriever.persist_directory)
                }
            
            details = await asyncio.to_thread(_check_chroma)
            latency = round((time.time() - start_time) * 1000, 2)
            
            # Check if collection has documents
            if details["document_count"] == 0:
                return {
                    "status": "degraded",
                    "message": "ChromaDB is connected but collection is empty",
                    "latency_ms": latency,
                    "details": details
                }
            
            return {
                "status": "healthy",
                "message": "ChromaDB is connected and has documents",
                "latency_ms": latency,
                "details": details
            }
            
        except Exception as e:
            latency = round((time.time() - start_time) * 1000, 2)
            return {
                "status": "unhealthy",
                "message": f"ChromaDB check failed: {str(e)}",
                "latency_ms": latency,
                "details": {"error": str(e)}
            }
    
    async def check_rag_pipeline(self) -> Dict:
        """Check RAG pipeline functionality with a test query"""
        start_time = time.time()
        
        try:
            # Run a lightweight test query
            def _test_rag():
                # Simple test query to verify pipeline works
                result = rag_adapter.query("test")
                return {
                    "has_answer": bool(result.get("answer")),
                    "has_sources": bool(result.get("retrieved_chunks")),
                    "num_sources": len(result.get("retrieved_chunks", []))
                }
            
            details = await asyncio.to_thread(_test_rag)
            latency = round((time.time() - start_time) * 1000, 2)
            
            # Check if pipeline returned meaningful results
            if not details["has_answer"]:
                return {
                    "status": "degraded",
                    "message": "RAG pipeline responding but not generating answers",
                    "latency_ms": latency,
                    "details": details
                }
            
            return {
                "status": "healthy",
                "message": "RAG pipeline is operational",
                "latency_ms": latency,
                "details": details
            }
            
        except Exception as e:
            latency = round((time.time() - start_time) * 1000, 2)
            return {
                "status": "unhealthy",
                "message": f"RAG pipeline check failed: {str(e)}",
                "latency_ms": latency,
                "details": {"error": str(e)}
            }


# Singleton instance
health_repo = HealthRepository()
