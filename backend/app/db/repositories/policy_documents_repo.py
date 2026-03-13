"""
Policy Documents Repository
Handles database operations for policy_documents collection (Phase 3)
Manages versioned policy documents and their metadata
"""

from typing import Optional, Dict, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


class PolicyDocumentsRepository:
    """Repository for policy_documents collection operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["policy_documents"]
    
    async def create_indexes(self):
        """Create database indexes for policy_documents collection"""
        await self.collection.create_index("doc_id")
        await self.collection.create_index([("doc_id", 1), ("version", -1)])
        await self.collection.create_index("status")
        await self.collection.create_index("effective_date")
        await self.collection.create_index([("status", 1), ("doc_id", 1)])
        logger.info("Policy documents indexes created")
    
    async def create_policy_document(self, policy_data: Dict) -> str:
        """
        Create a new policy document version
        
        Args:
            policy_data: {
                "doc_id": str,
                "version": int,
                "status": str,  # "active", "deprecated", "draft"
                "effective_date": datetime,
                "supersedes": str | None,
                "source_reference": str,
                "created_by": str,
                "chunk_ids": List[str],
                "metadata": dict
            }
            
        Returns:
            Created policy document _id as string
        """
        policy_doc = {
            **policy_data,
            "created_at": datetime.utcnow(),
        }
        
        result = await self.collection.insert_one(policy_doc)
        logger.info(f"Created policy document: {policy_data['doc_id']} v{policy_data['version']}")
        return str(result.inserted_id)
    
    async def get_policy_document_by_id(self, document_id: str) -> Optional[Dict]:
        """
        Get policy document by MongoDB _id
        
        Args:
            document_id: MongoDB ObjectId as string
            
        Returns:
            Policy document or None
        """
        try:
            doc = await self.collection.find_one({"_id": ObjectId(document_id)})
            if doc:
                doc["_id"] = str(doc["_id"])
            return doc
        except Exception as e:
            logger.error(f"Error fetching policy document {document_id}: {e}")
            return None
    
    async def get_active_version(self, doc_id: str) -> Optional[Dict]:
        """
        Get the active version of a policy document
        
        Args:
            doc_id: Policy document identifier (e.g., "ncie_exam_registration_process")
            
        Returns:
            Active policy document or None
        """
        doc = await self.collection.find_one({
            "doc_id": doc_id,
            "status": "active"
        })
        
        if doc:
            doc["_id"] = str(doc["_id"])
        
        return doc
    
    async def get_latest_version_number(self, doc_id: str) -> int:
        """
        Get the latest version number for a document
        
        Args:
            doc_id: Policy document identifier
            
        Returns:
            Latest version number (0 if no versions exist)
        """
        doc = await self.collection.find_one(
            {"doc_id": doc_id},
            sort=[("version", -1)]
        )
        
        return doc["version"] if doc else 0
    
    async def get_all_versions(self, doc_id: str, limit: int = 50) -> List[Dict]:
        """
        Get all versions of a policy document
        
        Args:
            doc_id: Policy document identifier
            limit: Maximum number of versions to return
            
        Returns:
            List of policy document versions (newest first)
        """
        cursor = self.collection.find(
            {"doc_id": doc_id}
        ).sort("version", -1).limit(limit)
        
        docs = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            docs.append(doc)
        
        return docs
    
    async def update_policy_status(
        self,
        document_id: str,
        new_status: str,
        updated_by: str
    ) -> bool:
        """
        Update policy document status
        
        Args:
            document_id: MongoDB ObjectId as string
            new_status: New status ("active", "deprecated", "draft")
            updated_by: User ID who made the update
            
        Returns:
            True if updated successfully
        """
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(document_id)},
                {
                    "$set": {
                        "status": new_status,
                        "updated_at": datetime.utcnow(),
                        "updated_by": updated_by
                    }
                }
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Updated policy {document_id} status to {new_status}")
            
            return success
        except Exception as e:
            logger.error(f"Error updating policy status: {e}")
            return False
    
    async def deprecate_version(
        self,
        doc_id: str,
        version: int,
        deprecated_by: str,
        reason: str
    ) -> bool:
        """
        Deprecate a specific version of a policy document
        
        Args:
            doc_id: Policy document identifier
            version: Version number to deprecate
            deprecated_by: User ID who deprecated it
            reason: Reason for deprecation
            
        Returns:
            True if deprecated successfully
        """
        try:
            result = await self.collection.update_one(
                {"doc_id": doc_id, "version": version},
                {
                    "$set": {
                        "status": "deprecated",
                        "deprecated_at": datetime.utcnow(),
                        "deprecated_by": deprecated_by,
                        "deprecation_reason": reason
                    }
                }
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Deprecated policy {doc_id} v{version}")
            
            return success
        except Exception as e:
            logger.error(f"Error deprecating policy: {e}")
            return False
    
    async def get_policies_by_status(
        self,
        status: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        Get policy documents by status
        
        Args:
            status: Status filter ("active", "deprecated", "draft")
            limit: Maximum number to return
            offset: Number to skip
            
        Returns:
            List of policy documents
        """
        cursor = self.collection.find(
            {"status": status}
        ).sort("created_at", -1).skip(offset).limit(limit)
        
        docs = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            docs.append(doc)
        
        return docs
    
    async def count_by_status(self, status: str) -> int:
        """Count policy documents by status"""
        return await self.collection.count_documents({"status": status})
    
    async def search_policies(
        self,
        query_filter: Dict,
        limit: int = 50
    ) -> List[Dict]:
        """
        Search policy documents with custom filter
        
        Args:
            query_filter: MongoDB query filter
            limit: Maximum results
            
        Returns:
            List of matching policy documents
        """
        cursor = self.collection.find(query_filter).limit(limit)
        
        docs = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            docs.append(doc)
        
        return docs
