"""
Policy Re-embedding Service (Phase 3)
Re-ingests and re-embeds updated policy text into ChromaDB
"""

from typing import Dict, List, Optional
import logging
from datetime import datetime
import uuid
from config import config

logger = logging.getLogger(__name__)


class PolicyReembeddingService:
    """
    Service to re-ingest and re-embed updated policy text
    Creates new chunks with embeddings for updated policies
    """
    
    def __init__(self, vector_index=None, embedder=None):
        """
        Initialize Policy Re-embedding Service
        
        Args:
            vector_index: VectorIndex instance (ChromaDB)
            embedder: Embedder instance for generating embeddings
        """
        self.vector_index = vector_index
        self.embedder = embedder
        self.enabled = config.ENABLE_POLICY_UNLEARNING
    
    def _chunk_text(
        self,
        text: str,
        chunk_size: int = 800,
        chunk_overlap: int = 100
    ) -> List[str]:
        """
        Chunk text into smaller pieces
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk
            chunk_overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        chunks = []
        position = 0
        text_length = len(text)
        
        while position < text_length:
            chunk_text = text[position:position + chunk_size]
            chunks.append(chunk_text.strip())
            position += (chunk_size - chunk_overlap)
        
        return chunks
    
    async def reingest_policy(
        self,
        new_policy_text: str,
        doc_id: str,
        version: int,
        metadata: Dict,
        source_reference: Optional[str] = None
    ) -> Dict:
        """
        Re-ingest updated policy text with new embeddings
        
        Args:
            new_policy_text: Updated policy text
            doc_id: Policy document identifier
            version: New version number
            metadata: Additional metadata (section, filename, etc.)
            source_reference: Optional policy source reference
            
        Returns:
            {
                "job_id": str,
                "new_chunk_ids": List[str],
                "status": str,  # "completed", "failed"
                "chunk_count": int
            }
        """
        if not self.enabled:
            logger.warning("Policy re-embedding disabled (feature flag off)")
            return {
                "job_id": None,
                "new_chunk_ids": [],
                "status": "disabled",
                "chunk_count": 0,
                "message": "Feature disabled"
            }
        
        if not new_policy_text:
            return {
                "job_id": None,
                "new_chunk_ids": [],
                "status": "failed",
                "chunk_count": 0,
                "message": "Empty policy text"
            }
        
        job_id = f"REEMBED-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8].upper()}"
        
        try:
            # Validate dependencies
            if not self.vector_index or not hasattr(self.vector_index, 'collection'):
                logger.error("Vector index not available")
                return {
                    "job_id": job_id,
                    "new_chunk_ids": [],
                    "status": "failed",
                    "chunk_count": 0,
                    "message": "Vector index not available"
                }
            
            if not self.embedder:
                logger.error("Embedder not available")
                return {
                    "job_id": job_id,
                    "new_chunk_ids": [],
                    "status": "failed",
                    "chunk_count": 0,
                    "message": "Embedder not available"
                }
            
            logger.info(f"Starting re-embedding job {job_id} for {doc_id} v{version}")
            
            # Step 1: Chunk the new policy text
            chunks = self._chunk_text(new_policy_text)
            logger.info(f"Created {len(chunks)} chunks from policy text")
            
            # Step 2: Generate embeddings and add to ChromaDB
            collection = self.vector_index.collection
            new_chunk_ids = []
            
            for i, chunk_text in enumerate(chunks):
                try:
                    # Generate unique chunk ID
                    chunk_id = f"{doc_id}_v{version}_chunk{i}_{uuid.uuid4().hex[:8]}"
                    
                    # Generate embedding
                    embedding = self.embedder.embed_text(chunk_text)
                    
                    # Prepare metadata
                    chunk_metadata = {
                        "doc_id": doc_id,
                        "version": version,
                        "chunk_index": i,
                        "status": "active",
                        "type": "canonical_knowledge",
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                        "job_id": job_id,
                        "active": True,
                        **metadata  # Include section, filename, etc.
                    }
                    
                    if source_reference:
                        chunk_metadata["source_reference"] = source_reference
                    
                    # Add to ChromaDB
                    collection.add(
                        ids=[chunk_id],
                        embeddings=[embedding],
                        documents=[chunk_text],
                        metadatas=[chunk_metadata]
                    )
                    
                    new_chunk_ids.append(chunk_id)
                    logger.debug(f"Added chunk {chunk_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to embed chunk {i}: {e}")
                    # Continue with other chunks
            
            success = len(new_chunk_ids) > 0
            status = "completed" if success else "failed"
            
            logger.info(f"Re-embedding job {job_id} {status}: {len(new_chunk_ids)}/{len(chunks)} chunks")
            
            return {
                "job_id": job_id,
                "new_chunk_ids": new_chunk_ids,
                "status": status,
                "chunk_count": len(new_chunk_ids),
                "message": f"Successfully embedded {len(new_chunk_ids)} chunks"
            }
            
        except Exception as e:
            logger.error(f"Error in re-embedding job {job_id}: {e}")
            return {
                "job_id": job_id,
                "new_chunk_ids": [],
                "status": "failed",
                "chunk_count": 0,
                "message": f"Re-embedding failed: {str(e)}"
            }
    
    async def delete_chunks(
        self,
        chunk_ids: List[str]
    ) -> Dict:
        """
        Permanently delete chunks from ChromaDB (use with caution)
        
        Args:
            chunk_ids: List of chunk IDs to delete
            
        Returns:
            {
                "deleted_count": int,
                "success": bool
            }
        """
        if not self.enabled:
            return {
                "deleted_count": 0,
                "success": False,
                "message": "Feature disabled"
            }
        
        try:
            if not self.vector_index or not hasattr(self.vector_index, 'collection'):
                return {
                    "deleted_count": 0,
                    "success": False,
                    "message": "Vector index not available"
                }
            
            collection = self.vector_index.collection
            
            # Delete from ChromaDB
            collection.delete(ids=chunk_ids)
            
            logger.info(f"Deleted {len(chunk_ids)} chunks from ChromaDB")
            
            return {
                "deleted_count": len(chunk_ids),
                "success": True,
                "message": f"Deleted {len(chunk_ids)} chunks"
            }
            
        except Exception as e:
            logger.error(f"Error deleting chunks: {e}")
            return {
                "deleted_count": 0,
                "success": False,
                "message": f"Deletion failed: {str(e)}"
            }


# Singleton instance (will be initialized with actual dependencies)
policy_reembedding_service = PolicyReembeddingService()
