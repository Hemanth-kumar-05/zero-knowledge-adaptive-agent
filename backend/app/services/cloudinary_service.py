"""
Cloudinary Service for Policy Proof Upload (Phase 3)
Handles temporary storage of proof documents (images, PDFs, text files)
"""

import cloudinary
import cloudinary.uploader
import cloudinary.api
from typing import List, Dict, Optional
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class CloudinaryService:
    """Service for managing proof file uploads to Cloudinary"""
    
    def __init__(self):
        """Initialize Cloudinary configuration"""
        self.enabled = False
        try:
            cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
            api_key = os.getenv("CLOUDINARY_API_KEY")
            api_secret = os.getenv("CLOUDINARY_API_SECRET")
            
            if cloud_name and api_key and api_secret:
                cloudinary.config(
                    cloud_name=cloud_name,
                    api_key=api_key,
                    api_secret=api_secret,
                    secure=True
                )
                self.folder = os.getenv("CLOUDINARY_FOLDER", "policy_proofs")
                self.enabled = True
                logger.info("Cloudinary service initialized successfully")
            else:
                logger.warning("Cloudinary credentials not configured")
        except Exception as e:
            logger.error(f"Failed to initialize Cloudinary: {e}")
    
    async def upload_proof(
        self,
        file_content: bytes,
        filename: str,
        ticket_id: str,
        file_type: str
    ) -> Optional[Dict]:
        """
        Upload proof file to Cloudinary
        
        Args:
            file_content: Binary file content
            filename: Original filename
            ticket_id: Associated ticket ID
            file_type: File type (image, pdf, text)
            
        Returns:
            {
                "public_id": str,
                "secure_url": str,
                "resource_type": str,
                "format": str,
                "size": int
            }
        """
        if not self.enabled:
            logger.error("Cloudinary service not enabled")
            return None
        
        try:
            # Determine resource type
            resource_type = "auto"  # auto-detect
            if file_type.startswith("image"):
                resource_type = "image"
            elif file_type == "application/pdf":
                resource_type = "raw"
            elif file_type.startswith("text"):
                resource_type = "raw"
            
            # Create unique public_id with ticket reference
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            public_id = f"{self.folder}/{ticket_id}/{timestamp}_{filename}"
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                file_content,
                public_id=public_id,
                resource_type=resource_type,
                folder=self.folder,
                use_filename=True,
                unique_filename=True,
                overwrite=False,
                tags=[ticket_id, "policy_proof"]
            )
            
            upload_info = {
                "public_id": result["public_id"],
                "secure_url": result["secure_url"],
                "resource_type": result["resource_type"],
                "format": result.get("format"),
                "size": result.get("bytes"),
                "uploaded_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Uploaded proof: {public_id}")
            return upload_info
            
        except Exception as e:
            logger.error(f"Error uploading proof to Cloudinary: {e}")
            return None
    
    async def delete_proof(self, public_id: str) -> bool:
        """
        Delete proof file from Cloudinary
        
        Args:
            public_id: Cloudinary public_id of the file
            
        Returns:
            True if deleted successfully
        """
        if not self.enabled:
            logger.error("Cloudinary service not enabled")
            return False
        
        try:
            result = cloudinary.uploader.destroy(public_id, invalidate=True)
            
            if result.get("result") == "ok":
                logger.info(f"Deleted proof: {public_id}")
                return True
            else:
                logger.warning(f"Failed to delete proof: {public_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting proof from Cloudinary: {e}")
            return False
    
    async def delete_ticket_proofs(self, ticket_id: str) -> int:
        """
        Delete all proofs associated with a ticket
        
        Args:
            ticket_id: Ticket identifier
            
        Returns:
            Number of proofs deleted
        """
        if not self.enabled:
            logger.error("Cloudinary service not enabled")
            return 0
        
        try:
            # Search for files with ticket_id tag
            result = cloudinary.api.resources_by_tag(
                ticket_id,
                max_results=100
            )
            
            deleted_count = 0
            for resource in result.get("resources", []):
                public_id = resource["public_id"]
                if await self.delete_proof(public_id):
                    deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} proofs for ticket {ticket_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting ticket proofs: {e}")
            return 0
    
    async def get_proof_info(self, public_id: str) -> Optional[Dict]:
        """
        Get information about uploaded proof
        
        Args:
            public_id: Cloudinary public_id
            
        Returns:
            Proof metadata
        """
        if not self.enabled:
            return None
        
        try:
            result = cloudinary.api.resource(public_id)
            return {
                "public_id": result["public_id"],
                "secure_url": result["secure_url"],
                "resource_type": result["resource_type"],
                "format": result.get("format"),
                "size": result.get("bytes"),
                "created_at": result.get("created_at")
            }
        except Exception as e:
            logger.error(f"Error getting proof info: {e}")
            return None


# Singleton instance
cloudinary_service = CloudinaryService()
