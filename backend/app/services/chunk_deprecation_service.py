"""
Chunk Deprecation Service (Phase 3)
Marks old policy chunks as deprecated in ChromaDB and creates new ones
"""

from typing import List, Dict
import logging
from datetime import datetime
from config import config
from embeddings.embedder import Embedder
import chromadb
from pathlib import Path

logger = logging.getLogger(__name__)


class ChunkDeprecationService:
    """
    Service to deprecate old policy chunks in ChromaDB
    Updates metadata to mark chunks as inactive without deleting them
    """
    
    def __init__(self, vector_index=None):
        """
        Initialize Chunk Deprecation Service
        
        Args:
            vector_index: VectorIndex instance (for ChromaDB access)
        """
        self.vector_index = vector_index
        self.enabled = config.ENABLE_POLICY_UNLEARNING
    
    async def deprecate_chunks(
        self,
        chunk_ids: List[str],
        reason: str,
        audit_id: str,
        deprecated_by: str
    ) -> Dict:
        """
        Deprecate chunks by updating their metadata
        
        Args:
            chunk_ids: List of ChromaDB document IDs to deprecate
            reason: Reason for deprecation
            audit_id: Reference to audit trail record
            deprecated_by: User ID who triggered deprecation
            
        Returns:
            {
                "deprecated_count": int,
                "failed_chunks": List[str],
                "success": bool
            }
        """
        if not self.enabled:
            logger.warning("Chunk deprecation disabled (feature flag off)")
            return {
                "deprecated_count": 0,
                "failed_chunks": chunk_ids,
                "success": False,
                "message": "Feature disabled"
            }
        
        if not chunk_ids:
            return {
                "deprecated_count": 0,
                "failed_chunks": [],
                "success": True,
                "message": "No chunks to deprecate"
            }
        
        deprecated_count = 0
        failed_chunks = []
        
        try:
            # Get ChromaDB collection
            if not self.vector_index or not hasattr(self.vector_index, 'collection'):
                logger.error("Vector index not available")
                return {
                    "deprecated_count": 0,
                    "failed_chunks": chunk_ids,
                    "success": False,
                    "message": "Vector index not available"
                }
            
            collection = self.vector_index.collection
            
            # Update metadata for each chunk
            for chunk_id in chunk_ids:
                try:
                    # Get current metadata
                    result = collection.get(
                        ids=[chunk_id],
                        include=["metadatas"]
                    )
                    
                    if not result['ids']:
                        logger.warning(f"Chunk {chunk_id} not found in ChromaDB")
                        failed_chunks.append(chunk_id)
                        continue
                    
                    # Get existing metadata
                    current_metadata = result['metadatas'][0] if result['metadatas'] else {}
                    
                    # Update metadata with deprecation info
                    updated_metadata = {
                        **current_metadata,
                        "status": "deprecated",
                        "deprecated_at": datetime.utcnow().isoformat(),
                        "deprecated_by": deprecated_by,
                        "deprecation_reason": reason,
                        "audit_id": audit_id,
                        "active": False  # Backward compatibility flag
                    }
                    
                    # Update in ChromaDB
                    collection.update(
                        ids=[chunk_id],
                        metadatas=[updated_metadata]
                    )
                    
                    deprecated_count += 1
                    logger.info(f"Deprecated chunk {chunk_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to deprecate chunk {chunk_id}: {e}")
                    failed_chunks.append(chunk_id)
            
            success = deprecated_count > 0
            
            logger.info(f"Deprecated {deprecated_count}/{len(chunk_ids)} chunks")
            
            return {
                "deprecated_count": deprecated_count,
                "failed_chunks": failed_chunks,
                "success": success,
                "message": f"Successfully deprecated {deprecated_count} chunks"
            }
            
        except Exception as e:
            logger.error(f"Error in chunk deprecation: {e}")
            return {
                "deprecated_count": deprecated_count,
                "failed_chunks": failed_chunks + [c for c in chunk_ids if c not in failed_chunks][deprecated_count:],
                "success": False,
                "message": f"Deprecation failed: {str(e)}"
            }
    
    async def reactivate_chunks(
        self,
        chunk_ids: List[str],
        reason: str,
        audit_id: str,
        reactivated_by: str
    ) -> Dict:
        """
        Reactivate previously deprecated chunks (for rollback)
        
        Args:
            chunk_ids: List of ChromaDB document IDs to reactivate
            reason: Reason for reactivation (e.g., "rollback")
            audit_id: Reference to rollback audit record
            reactivated_by: User ID who triggered reactivation
            
        Returns:
            {
                "reactivated_count": int,
                "failed_chunks": List[str],
                "success": bool
            }
        """
        if not self.enabled:
            logger.warning("Chunk reactivation disabled (feature flag off)")
            return {
                "reactivated_count": 0,
                "failed_chunks": chunk_ids,
                "success": False,
                "message": "Feature disabled"
            }
        
        reactivated_count = 0
        failed_chunks = []
        
        try:
            if not self.vector_index or not hasattr(self.vector_index, 'collection'):
                logger.error("Vector index not available")
                return {
                    "reactivated_count": 0,
                    "failed_chunks": chunk_ids,
                    "success": False,
                    "message": "Vector index not available"
                }
            
            collection = self.vector_index.collection
            
            for chunk_id in chunk_ids:
                try:
                    result = collection.get(
                        ids=[chunk_id],
                        include=["metadatas"]
                    )
                    
                    if not result['ids']:
                        logger.warning(f"Chunk {chunk_id} not found in ChromaDB")
                        failed_chunks.append(chunk_id)
                        continue
                    
                    current_metadata = result['metadatas'][0] if result['metadatas'] else {}
                    
                    # Update metadata to reactivate
                    updated_metadata = {
                        **current_metadata,
                        "status": "active",
                        "reactivated_at": datetime.utcnow().isoformat(),
                        "reactivated_by": reactivated_by,
                        "reactivation_reason": reason,
                        "rollback_audit_id": audit_id,
                        "active": True
                    }
                    
                    # Remove deprecation fields
                    updated_metadata.pop("deprecated_at", None)
                    updated_metadata.pop("deprecated_by", None)
                    updated_metadata.pop("deprecation_reason", None)
                    
                    collection.update(
                        ids=[chunk_id],
                        metadatas=[updated_metadata]
                    )
                    
                    reactivated_count += 1
                    logger.info(f"Reactivated chunk {chunk_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to reactivate chunk {chunk_id}: {e}")
                    failed_chunks.append(chunk_id)
            
            success = reactivated_count > 0
            
            logger.info(f"Reactivated {reactivated_count}/{len(chunk_ids)} chunks")
            
            return {
                "reactivated_count": reactivated_count,
                "failed_chunks": failed_chunks,
                "success": success,
                "message": f"Successfully reactivated {reactivated_count} chunks"
            }
            
        except Exception as e:
            logger.error(f"Error in chunk reactivation: {e}")
            return {
                "reactivated_count": reactivated_count,
                "failed_chunks": failed_chunks,
                "success": False,
                "message": f"Reactivation failed: {str(e)}"
            }
    
    async def create_policy_chunks(
        self,
        new_policy_text: str,
        policy_area: str,
        ticket_id: str,
        created_by: str,
        chunk_size: int = 800,
        chunk_overlap: int = 100
    ) -> Dict:
        """
        Create new chunks from updated policy text
        
        Args:
            new_policy_text: The new policy text provided by admin
            policy_area: Policy area being updated (for metadata)
            ticket_id: Policy update ticket ID
            created_by: User ID who created the new policy
            chunk_size: Size of each chunk
            chunk_overlap: Overlap between chunks
        
        Returns: {
            "chunks_created": 3,
            "chunk_ids": ["doc_NEW_1", "doc_NEW_2", ...],
            "timestamp": "..."
        }
        """
        if not self.enabled:
            logger.warning("Policy chunk creation disabled (feature flag off)")
            return {
                "chunks_created": 0,
                "chunk_ids": [],
                "success": False,
                "message": "Feature disabled"
            }
        
        logger.info(f"Creating new policy chunks from text ({len(new_policy_text)} chars)...")
        
        try:
            # Get ChromaDB collection
            if not self.vector_index or not hasattr(self.vector_index, 'collection'):
                logger.error("Vector index not available")
                return {
                    "chunks_created": 0,
                    "chunk_ids": [],
                    "success": False,
                    "message": "Vector index not available"
                }
            
            collection = self.vector_index.collection
            
            # Create chunks from new policy text
            chunks = []
            position = 0
            text_length = len(new_policy_text)
            
            while position < text_length:
                chunk_text = new_policy_text[position:position + chunk_size].strip()
                
                if chunk_text:  # Only add non-empty chunks
                    chunks.append(chunk_text)
                
                position += (chunk_size - chunk_overlap)
            
            if not chunks:
                logger.warning("No chunks created from empty text")
                return {
                    "chunks_created": 0,
                    "chunk_ids": [],
                    "success": False,
                    "message": "No chunks created from empty text"
                }
            
            logger.info(f"Split into {len(chunks)} chunks")
            
            # Generate chunk IDs
            timestamp = datetime.utcnow().isoformat()
            existing_count = collection.count()
            chunk_ids = [f"doc_NEW_{existing_count + i + 1}" for i in range(len(chunks))]
            
            # Embed chunks
            logger.info("Embedding chunks...")
            embedder = Embedder()
            embeddings = embedder.embed_batch(chunks)
            
            # Prepare metadata
            metadatas = []
            for i, chunk_text in enumerate(chunks):
                metadata = {
                    'type': 'policy_update',
                    'doc_id': f'policy_update_{ticket_id}',
                    'section': policy_area,
                    'text': chunk_text,
                    'confidence': 1.0,
                    'active': True,
                    'status': 'active',
                    'version': 2,  # Version 2 = updated policy
                    'created_at': timestamp,
                    'updated_at': timestamp,
                    'created_by': created_by,
                    'ticket_id': ticket_id,
                    'policy_area': policy_area
                }
                metadatas.append(metadata)
            
            # Add to ChromaDB
            logger.info("Adding to ChromaDB...")
            collection.add(
                ids=chunk_ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=chunks
            )
            
            logger.info(f"Created {len(chunks)} new policy chunks: {chunk_ids}")
            
            return {
                "chunks_created": len(chunks),
                "chunk_ids": chunk_ids,
                "timestamp": timestamp,
                "success": True,
                "message": f"Successfully created {len(chunks)} new chunks"
            }
            
        except Exception as e:
            logger.error(f"Error creating policy chunks: {e}")
            return {
                "chunks_created": 0,
                "chunk_ids": [],
                "success": False,
                "message": f"Chunk creation failed: {str(e)}"
            }
    
    async def create_single_policy_chunk(
        self,
        new_text: str,
        policy_area: str,
        ticket_id: str,
        created_by: str,
        replaces_chunk_id: str = None
    ) -> Dict:
        """
        Create a single new chunk from edited text (1:1 replacement)
        
        Args:
            new_text: The edited policy text for this chunk
            policy_area: Policy area being updated
            ticket_id: Policy update ticket ID
            created_by: User ID who created/edited the policy
            replaces_chunk_id: Original chunk ID being replaced
        
        Returns: {
            "chunks_created": 1,
            "chunk_ids": ["doc_NEW_123"],
            "success": True
        }
        """
        if not self.enabled:
            logger.warning("Policy chunk creation disabled (feature flag off)")
            return {
                "chunks_created": 0,
                "chunk_ids": [],
                "success": False,
                "message": "Feature disabled"
            }
        
        logger.info(f"Creating single policy chunk (replacing {replaces_chunk_id})...")
        
        try:
            # Get ChromaDB collection
            if not self.vector_index or not hasattr(self.vector_index, 'collection'):
                logger.error("Vector index not available")
                return {
                    "chunks_created": 0,
                    "chunk_ids": [],
                    "success": False,
                    "message": "Vector index not available"
                }
            
            collection = self.vector_index.collection
            
            # Generate chunk ID
            timestamp = datetime.utcnow().isoformat()
            existing_count = collection.count()
            chunk_id = f"doc_NEW_{existing_count + 1}"
            
            # Embed the new text
            logger.info("Embedding chunk...")
            embedder = Embedder()
            embedding = embedder.embed_text(new_text)
            
            # Prepare metadata
            metadata = {
                'type': 'policy_update',
                'doc_id': f'policy_update_{ticket_id}',
                'section': policy_area,
                'text': new_text,
                'confidence': 1.0,
                'active': True,
                'status': 'active',
                'version': 2,  # Version 2 = updated policy
                'created_at': timestamp,
                'updated_at': timestamp,
                'created_by': created_by,
                'ticket_id': ticket_id,
                'policy_area': policy_area,
                'replaces': replaces_chunk_id  # Track what it replaces
            }
            
            # Add to ChromaDB
            logger.info(f"Adding chunk {chunk_id} to ChromaDB...")
            collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                metadatas=[metadata],
                documents=[new_text]
            )
            
            logger.info(f"Created policy chunk: {chunk_id}")
            
            return {
                "chunks_created": 1,
                "chunk_ids": [chunk_id],
                "timestamp": timestamp,
                "success": True,
                "message": f"Successfully created chunk {chunk_id}"
            }
            
        except Exception as e:
            logger.error(f"Error creating policy chunk: {e}")
            return {
                "chunks_created": 0,
                "chunk_ids": [],
                "success": False,
                "message": f"Chunk creation failed: {str(e)}"
            }
    
    async def create_deduplicated_policy_chunk(
        self,
        new_text: str,
        policy_area: str,
        ticket_id: str,
        created_by: str,
        replaces_chunk_ids: List[str] = None
    ) -> Dict:
        """
        Create a single new chunk that replaces multiple old chunks with same content.
        This eliminates duplicates at the source by storing multiple replaces IDs as a comma-separated string.
        
        Args:
            new_text: The edited policy text for this chunk
            policy_area: Policy area being updated
            ticket_id: Policy update ticket ID
            created_by: User ID who created/edited the policy
            replaces_chunk_ids: Array of original chunk IDs being replaced by this single chunk
        
        Note:
            ChromaDB metadata only supports scalar types, so replaces_chunk_ids is stored
            as a comma-separated string in metadata['replaces'].
        
        Returns: {
            "chunks_created": 1,
            "chunk_ids": ["doc_NEW_123"],
            "replaces_count": 3,  # How many old chunks this replaces
            "success": True
        }
        """
        if not self.enabled:
            logger.warning("Policy chunk creation disabled (feature flag off)")
            return {
                "chunks_created": 0,
                "chunk_ids": [],
                "replaces_count": 0,
                "success": False,
                "message": "Feature disabled"
            }
        
        replaces_chunk_ids = replaces_chunk_ids or []
        logger.info(f"Creating deduplicated chunk (replacing {len(replaces_chunk_ids)} chunks)...")
        
        try:
            # Get ChromaDB collection
            if not self.vector_index or not hasattr(self.vector_index, 'collection'):
                logger.error("Vector index not available")
                return {
                    "chunks_created": 0,
                    "chunk_ids": [],
                    "replaces_count": 0,
                    "success": False,
                    "message": "Vector index not available"
                }
            
            collection = self.vector_index.collection
            
            # Generate chunk ID
            timestamp = datetime.utcnow().isoformat()
            existing_count = collection.count()
            chunk_id = f"doc_NEW_{existing_count + 1}"
            
            # Embed the new text
            logger.info("Embedding chunk...")
            embedder = Embedder()
            embedding = embedder.embed_text(new_text)
            
            # Prepare metadata - ChromaDB only supports scalar types (str, int, float, bool)
            # Convert replaces array to comma-separated string
            replaces_str = ','.join(replaces_chunk_ids) if replaces_chunk_ids else ''
            
            metadata = {
                'type': 'policy_update',
                'doc_id': f'policy_update_{ticket_id}',
                'section': policy_area,
                'text': new_text,
                'confidence': 1.0,
                'active': True,
                'status': 'active',
                'version': 2,  # Version 2 = updated policy
                'created_at': timestamp,
                'updated_at': timestamp,
                'created_by': created_by,
                'ticket_id': ticket_id,
                'policy_area': policy_area,
                'replaces': replaces_str,  # Comma-separated string of replaced chunk IDs
                'replaces_count': len(replaces_chunk_ids)  # Track how many it replaces
            }
            
            # Add to ChromaDB
            logger.info(f"Adding deduplicated chunk {chunk_id} to ChromaDB (replaces {len(replaces_chunk_ids)} chunks)...")
            collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                metadatas=[metadata],
                documents=[new_text]
            )
            
            logger.info(f"✅ Created deduplicated policy chunk: {chunk_id}")
            
            return {
                "chunks_created": 1,
                "chunk_ids": [chunk_id],
                "replaces_count": len(replaces_chunk_ids),
                "timestamp": timestamp,
                "success": True,
                "message": f"Successfully created chunk {chunk_id} (replaces {len(replaces_chunk_ids)} old chunks)"
            }
            
        except Exception as e:
            logger.error(f"Error creating deduplicated policy chunk: {e}")
            return {
                "chunks_created": 0,
                "chunk_ids": [],
                "replaces_count": 0,
                "success": False,
                "message": f"Chunk creation failed: {str(e)}"
            }
    
    @staticmethod
    def parse_replaces_metadata(replaces_value) -> List[str]:
        """
        Parse the 'replaces' metadata field back into a list of chunk IDs.
        
        Args:
            replaces_value: Either a comma-separated string or a single string
        
        Returns:
            List of chunk IDs that were replaced
        
        Examples:
            "doc_1,doc_2,doc_3" -> ["doc_1", "doc_2", "doc_3"]
            "doc_1" -> ["doc_1"]
            "" -> []
        """
        if not replaces_value:
            return []
        
        if isinstance(replaces_value, str):
            # Handle comma-separated string
            if ',' in replaces_value:
                return [chunk_id.strip() for chunk_id in replaces_value.split(',') if chunk_id.strip()]
            # Handle single value
            elif replaces_value.strip():
                return [replaces_value.strip()]
        
        return []


# Singleton instance (will be initialized with actual vector_index)
chunk_deprecation_service = ChunkDeprecationService()
