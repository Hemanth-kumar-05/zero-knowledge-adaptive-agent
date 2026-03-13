"""
Extensions Repository
Handles all database operations for extensions collection
"""

from typing import Optional, Dict, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId


class ExtensionsRepository:
    """Repository for extensions collection operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["extensions"]
    
    async def create_indexes(self):
        """Create database indexes for extensions collection"""
        await self.collection.create_index("extension_id", unique=True)
        await self.collection.create_index("category")
        await self.collection.create_index("is_active")
    
    async def create_extension(self, extension_data: Dict) -> Dict:
        """
        Create a new extension
        
        Args:
            extension_data: Extension information including all metadata
            
        Returns:
            Created extension document
        """
        extension_doc = {
            "extension_id": extension_data["extension_id"],
            "name": extension_data["name"],
            "description": extension_data["description"],
            "icon": extension_data["icon"],  # SVG as base64 string
            "category": extension_data["category"],
            "required_files": extension_data.get("required_files", []),
            "created_by": extension_data["created_by"],
            "created_at": datetime.utcnow(),
            "is_active": extension_data.get("is_active", True),
            "extension_type": extension_data.get("extension_type", "prompt-based"),
            "welcome_message": extension_data.get("welcome_message", ""),
            "input_placeholder": extension_data.get("input_placeholder", "")
        }
        
        # Add system_prompt only if present (required for prompt-based, optional for script-based)
        if "system_prompt" in extension_data:
            extension_doc["system_prompt"] = extension_data["system_prompt"]
        
        # Add script_config if present (for script-based extensions)
        if "script_config" in extension_data:
            extension_doc["script_config"] = extension_data["script_config"]
        
        result = await self.collection.insert_one(extension_doc)
        extension_doc["_id"] = result.inserted_id
        
        return extension_doc
    
    async def get_all_extensions(self, active_only: bool = True) -> List[Dict]:
        """
        Get all extensions
        
        Args:
            active_only: If True, only return active extensions
            
        Returns:
            List of extension documents
        """
        query = {"is_active": True} if active_only else {}
        cursor = self.collection.find(query)
        extensions = await cursor.to_list(length=None)
        
        # Convert ObjectId to string
        for ext in extensions:
            ext["_id"] = str(ext["_id"])
        
        return extensions
    
    async def get_extension_by_id(self, extension_id: str) -> Optional[Dict]:
        """
        Get extension by extension_id
        
        Args:
            extension_id: The unique extension identifier
            
        Returns:
            Extension document or None
        """
        extension = await self.collection.find_one({"extension_id": extension_id})
        
        if extension:
            extension["_id"] = str(extension["_id"])
        
        return extension
    
    async def delete_extension(self, extension_id: str) -> bool:
        """
        Delete an extension (hard delete)
        
        Args:
            extension_id: The unique extension identifier
            
        Returns:
            True if deleted, False otherwise
        """
        result = await self.collection.delete_one({"extension_id": extension_id})
        return result.deleted_count > 0
    
    async def deactivate_extension(self, extension_id: str) -> bool:
        """
        Deactivate an extension (soft delete)
        
        Args:
            extension_id: The unique extension identifier
            
        Returns:
            True if deactivated, False otherwise
        """
        result = await self.collection.update_one(
            {"extension_id": extension_id},
            {"$set": {"is_active": False}}
        )
        return result.modified_count > 0
    
    async def get_extensions_by_category(self, category: str) -> List[Dict]:
        """
        Get all extensions in a specific category
        
        Args:
            category: The category name
            
        Returns:
            List of extension documents
        """
        cursor = self.collection.find({"category": category, "is_active": True})
        extensions = await cursor.to_list(length=None)
        
        # Convert ObjectId to string
        for ext in extensions:
            ext["_id"] = str(ext["_id"])
        
        return extensions
    
    async def extension_exists(self, extension_id: str) -> bool:
        """
        Check if an extension with the given ID exists
        
        Args:
            extension_id: The unique extension identifier
            
        Returns:
            True if exists, False otherwise
        """
        count = await self.collection.count_documents({"extension_id": extension_id})
        return count > 0
