"""
Policy Change Audit Repository
Handles database operations for policy_change_audit collection (Phase 3)
Manages audit trail for all policy changes and rollback capability
"""

from typing import Optional, Dict, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import logging
import uuid

logger = logging.getLogger(__name__)


class PolicyChangeAuditRepository:
    """Repository for policy_change_audit collection operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["policy_change_audit"]
    
    async def create_indexes(self):
        """Create database indexes for policy_change_audit collection"""
        await self.collection.create_index("audit_id", unique=True)
        await self.collection.create_index("ticket_id")
        await self.collection.create_index("timestamp")
        await self.collection.create_index("change_type")
        await self.collection.create_index("executed_by")
        await self.collection.create_index([("timestamp", -1)])
        await self.collection.create_index("affected_doc_ids")
        logger.info("Policy change audit indexes created")
    
    async def write_audit_record(
        self,
        ticket_id: str,
        change_type: str,
        old_chunk_ids: List[str],
        new_chunk_ids: List[str],
        affected_doc_ids: List[str],
        executed_by: str,
        reason: str,
        source_reference: Optional[str] = None,
        embedding_job_id: Optional[str] = None,
        rollback_pointer: Optional[str] = None
    ) -> str:
        """
        Write a new audit record
        
        Args:
            ticket_id: Associated policy update ticket ID
            change_type: "deprecate", "add", "update", "rollback"
            old_chunk_ids: List of deprecated chunk IDs
            new_chunk_ids: List of new chunk IDs
            affected_doc_ids: List of affected document IDs
            executed_by: User ID who executed the change
            reason: Reason for the change
            source_reference: Optional policy source reference
            embedding_job_id: Optional background job ID
            rollback_pointer: Previous audit_id for rollback capability
            
        Returns:
            Created audit_id
        """
        audit_id = f"AUDIT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8].upper()}"
        
        audit_doc = {
            "audit_id": audit_id,
            "ticket_id": ticket_id,
            "timestamp": datetime.utcnow(),
            "change_type": change_type,
            "old_chunk_ids": old_chunk_ids,
            "new_chunk_ids": new_chunk_ids,
            "affected_doc_ids": affected_doc_ids,
            "executed_by": executed_by,
            "reason": reason,
            "source_reference": source_reference,
            "embedding_job_id": embedding_job_id,
            "rollback_pointer": rollback_pointer,
            "verification_status": "pending",
            "verification_notes": None
        }
        
        await self.collection.insert_one(audit_doc)
        logger.info(f"Created audit record: {audit_id} for ticket {ticket_id}")
        return audit_id
    
    async def get_audit_by_id(self, audit_id: str) -> Optional[Dict]:
        """
        Get audit record by audit_id
        
        Args:
            audit_id: Audit identifier
            
        Returns:
            Audit document or None
        """
        doc = await self.collection.find_one({"audit_id": audit_id})
        
        if doc:
            doc["_id"] = str(doc["_id"])
        
        return doc
    
    async def get_audit_history(
        self,
        doc_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        Get audit history, optionally filtered by document ID
        
        Args:
            doc_id: Optional document ID filter
            limit: Maximum number of records
            offset: Number to skip
            
        Returns:
            List of audit records (newest first)
        """
        query = {}
        if doc_id:
            query["affected_doc_ids"] = doc_id
        
        cursor = self.collection.find(query).sort("timestamp", -1).skip(offset).limit(limit)
        
        audits = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            audits.append(doc)
        
        return audits
    
    async def get_audits_by_ticket(self, ticket_id: str) -> List[Dict]:
        """
        Get all audit records for a specific ticket
        
        Args:
            ticket_id: Ticket identifier
            
        Returns:
            List of audit records
        """
        cursor = self.collection.find(
            {"ticket_id": ticket_id}
        ).sort("timestamp", -1)
        
        audits = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            audits.append(doc)
        
        return audits
    
    async def get_latest_audit_for_rollback(
        self,
        doc_id: str,
        change_type: str = "update"
    ) -> Optional[Dict]:
        """
        Get the latest audit record for rollback purposes
        
        Args:
            doc_id: Document identifier
            change_type: Type of change to find
            
        Returns:
            Latest matching audit record or None
        """
        doc = await self.collection.find_one(
            {
                "affected_doc_ids": doc_id,
                "change_type": change_type
            },
            sort=[("timestamp", -1)]
        )
        
        if doc:
            doc["_id"] = str(doc["_id"])
        
        return doc
    
    async def update_verification_status(
        self,
        audit_id: str,
        status: str,
        notes: Optional[str] = None
    ) -> bool:
        """
        Update verification status of an audit record
        
        Args:
            audit_id: Audit identifier
            status: "pending", "verified", "failed"
            notes: Optional verification notes
            
        Returns:
            True if updated successfully
        """
        update_data = {
            "verification_status": status,
            "verification_notes": notes,
            "verified_at": datetime.utcnow()
        }
        
        try:
            result = await self.collection.update_one(
                {"audit_id": audit_id},
                {"$set": update_data}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Updated audit {audit_id} verification status to {status}")
            
            return success
        except Exception as e:
            logger.error(f"Error updating verification status: {e}")
            return False
    
    async def get_audits_by_user(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get audit records by user who executed them
        
        Args:
            user_id: User identifier
            limit: Maximum number of records
            
        Returns:
            List of audit records
        """
        cursor = self.collection.find(
            {"executed_by": user_id}
        ).sort("timestamp", -1).limit(limit)
        
        audits = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            audits.append(doc)
        
        return audits
    
    async def get_audits_by_change_type(
        self,
        change_type: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get audit records by change type
        
        Args:
            change_type: "deprecate", "add", "update", "rollback"
            limit: Maximum number of records
            
        Returns:
            List of audit records
        """
        cursor = self.collection.find(
            {"change_type": change_type}
        ).sort("timestamp", -1).limit(limit)
        
        audits = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            audits.append(doc)
        
        return audits
    
    async def count_audits(
        self,
        query_filter: Optional[Dict] = None
    ) -> int:
        """
        Count audit records with optional filter
        
        Args:
            query_filter: Optional MongoDB query filter
            
        Returns:
            Count of matching records
        """
        if query_filter:
            return await self.collection.count_documents(query_filter)
        return await self.collection.count_documents({})
    
    async def get_recent_audits(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get recent audit records within specified hours
        
        Args:
            hours: Number of hours to look back
            limit: Maximum number of records
            
        Returns:
            List of recent audit records
        """
        cutoff_time = datetime.utcnow()
        cutoff_time = cutoff_time.replace(hour=cutoff_time.hour - hours)
        
        cursor = self.collection.find(
            {"timestamp": {"$gte": cutoff_time}}
        ).sort("timestamp", -1).limit(limit)
        
        audits = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            audits.append(doc)
        
        return audits
    
    async def search_audits(
        self,
        query_filter: Dict,
        limit: int = 50
    ) -> List[Dict]:
        """
        Search audit records with custom filter
        
        Args:
            query_filter: MongoDB query filter
            limit: Maximum results
            
        Returns:
            List of matching audit records
        """
        cursor = self.collection.find(query_filter).sort("timestamp", -1).limit(limit)
        
        audits = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            audits.append(doc)
        
        return audits
