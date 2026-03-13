"""
Policy Update Tickets Repository
Handles database operations for policy_update_tickets collection (Phase 3)
Manages policy change requests and review workflow
"""

from typing import Optional, Dict, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import logging
import uuid

logger = logging.getLogger(__name__)


class PolicyUpdateTicketsRepository:
    """Repository for policy_update_tickets collection operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["policy_update_tickets"]
    
    async def create_indexes(self):
        """Create database indexes for policy_update_tickets collection"""
        await self.collection.create_index("ticket_id", unique=True)
        await self.collection.create_index("status")
        await self.collection.create_index("user_id")
        await self.collection.create_index("created_at")
        await self.collection.create_index([("status", 1), ("created_at", -1)])
        await self.collection.create_index("confidence_level")
        logger.info("Policy update tickets indexes created")
    
    async def create_ticket(self, ticket_data: Dict) -> str:
        """
        Create a new policy update ticket
        
        Args:
            ticket_data: {
                "user_id": str,
                "session_id": str,
                "claim_text": str,
                "query_context": str,
                "claim_type": str,
                "confidence_score": float,
                "confidence_level": str,
                "extracted_fields": dict,
                "affected_chunks": List[dict]
            }
            
        Returns:
            Created ticket_id
        """
        ticket_id = f"PT-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        ticket_doc = {
            "ticket_id": ticket_id,
            "status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            **ticket_data,
            "reviewer_id": None,
            "reviewed_at": None,
            "decision": None,
            "reviewer_notes": None,
            "implemented_at": None,
            "audit_trail_id": None
        }
        
        await self.collection.insert_one(ticket_doc)
        logger.info(f"Created policy update ticket: {ticket_id}")
        return ticket_id
    
    async def get_ticket_by_id(self, ticket_id: str) -> Optional[Dict]:
        """
        Get policy update ticket by ticket_id
        
        Args:
            ticket_id: Ticket identifier (e.g., "PT-20260303-A1B2C3D4")
            
        Returns:
            Ticket document or None
        """
        doc = await self.collection.find_one({"ticket_id": ticket_id})
        
        if doc:
            doc["_id"] = str(doc["_id"])
        
        return doc
    
    async def list_tickets(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: int = -1  # -1 for descending, 1 for ascending
    ) -> List[Dict]:
        """
        List policy update tickets with filters
        
        Args:
            status: Filter by status ("pending", "approved", "rejected", "implemented")
            limit: Maximum number of tickets
            offset: Number to skip
            sort_by: Field to sort by
            sort_order: Sort direction
            
        Returns:
            List of ticket documents
        """
        query = {}
        if status:
            query["status"] = status
        
        cursor = self.collection.find(query).sort(sort_by, sort_order).skip(offset).limit(limit)
        
        tickets = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            tickets.append(doc)
        
        return tickets
    
    async def update_ticket_status(
        self,
        ticket_id: str,
        new_status: str,
        additional_fields: Optional[Dict] = None
    ) -> bool:
        """
        Update ticket status
        
        Args:
            ticket_id: Ticket identifier
            new_status: New status
            additional_fields: Additional fields to update
            
        Returns:
            True if updated successfully
        """
        update_data = {
            "status": new_status,
            "updated_at": datetime.utcnow()
        }
        
        if additional_fields:
            update_data.update(additional_fields)
        
        try:
            result = await self.collection.update_one(
                {"ticket_id": ticket_id},
                {"$set": update_data}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Updated ticket {ticket_id} status to {new_status}")
            
            return success
        except Exception as e:
            logger.error(f"Error updating ticket status: {e}")
            return False
    
    async def add_review_decision(
        self,
        ticket_id: str,
        reviewer_id: str,
        decision: str,  # "approve" or "reject"
        reviewer_notes: Optional[str] = None
    ) -> bool:
        """
        Add review decision to ticket
        
        Args:
            ticket_id: Ticket identifier
            reviewer_id: User ID of reviewer
            decision: "approve" or "reject"
            reviewer_notes: Optional notes from reviewer
            
        Returns:
            True if updated successfully
        """
        new_status = "approved" if decision == "approve" else "rejected"
        
        update_data = {
            "status": new_status,
            "reviewer_id": reviewer_id,
            "reviewed_at": datetime.utcnow(),
            "decision": decision,
            "reviewer_notes": reviewer_notes,
            "updated_at": datetime.utcnow()
        }
        
        try:
            result = await self.collection.update_one(
                {"ticket_id": ticket_id},
                {"$set": update_data}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Added review decision for ticket {ticket_id}: {decision}")
            
            return success
        except Exception as e:
            logger.error(f"Error adding review decision: {e}")
            return False
    
    async def mark_implemented(
        self,
        ticket_id: str,
        audit_trail_id: str
    ) -> bool:
        """
        Mark ticket as implemented
        
        Args:
            ticket_id: Ticket identifier
            audit_trail_id: Reference to audit trail record
            
        Returns:
            True if updated successfully
        """
        try:
            result = await self.collection.update_one(
                {"ticket_id": ticket_id},
                {
                    "$set": {
                        "status": "implemented",
                        "implemented_at": datetime.utcnow(),
                        "audit_trail_id": audit_trail_id,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Marked ticket {ticket_id} as implemented")
            
            return success
        except Exception as e:
            logger.error(f"Error marking ticket as implemented: {e}")
            return False
    
    async def count_by_status(self, status: str) -> int:
        """Count tickets by status"""
        return await self.collection.count_documents({"status": status})
    
    async def get_user_tickets(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get tickets created by a specific user
        
        Args:
            user_id: User identifier
            limit: Maximum number of tickets
            
        Returns:
            List of ticket documents
        """
        cursor = self.collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(limit)
        
        tickets = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            tickets.append(doc)
        
        return tickets
    
    async def get_tickets_by_confidence_level(
        self,
        confidence_level: str,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get tickets by confidence level
        
        Args:
            confidence_level: "low", "medium", or "high"
            status: Optional status filter
            limit: Maximum number of tickets
            
        Returns:
            List of ticket documents
        """
        query = {"confidence_level": confidence_level}
        if status:
            query["status"] = status
        
        cursor = self.collection.find(query).sort("created_at", -1).limit(limit)
        
        tickets = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            tickets.append(doc)
        
        return tickets
    
    async def get_pending_tickets_count(self) -> int:
        """Get count of pending tickets"""
        return await self.collection.count_documents({"status": "pending"})
    
    async def search_tickets(
        self,
        query_filter: Dict,
        limit: int = 50
    ) -> List[Dict]:
        """
        Search tickets with custom filter
        
        Args:
            query_filter: MongoDB query filter
            limit: Maximum results
            
        Returns:
            List of matching tickets
        """
        cursor = self.collection.find(query_filter).sort("created_at", -1).limit(limit)
        
        tickets = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            tickets.append(doc)
        
        return tickets
