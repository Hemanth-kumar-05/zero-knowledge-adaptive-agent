"""
Extension Service
Handles business logic for extension management
"""

from typing import Dict, List, Optional
import base64
import re
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.repositories.extensions_repo import ExtensionsRepository


class ExtensionService:
    """Service for managing extensions"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.repo = ExtensionsRepository(db)
    
    def _generate_extension_id(self, name: str) -> str:
        """
        Generate a URL-safe extension ID from name
        
        Args:
            name: Extension name
            
        Returns:
            Lowercase, hyphenated extension ID
        """
        # Convert to lowercase and replace spaces/special chars with hyphens
        extension_id = re.sub(r'[^a-z0-9]+', '-', name.lower())
        # Remove leading/trailing hyphens
        extension_id = extension_id.strip('-')
        return extension_id
    
    def _validate_svg_icon(self, icon_data: str) -> bool:
        """
        Validate icon data (FontAwesome class name or legacy SVG)
        
        Args:
            icon_data: FontAwesome class name (e.g., "fa-solid fa-book") or base64 SVG
            
        Returns:
            True if valid, False otherwise
        """
        # Check if it's a FontAwesome class name (new format)
        if icon_data.startswith('fa-'):
            # Validate FontAwesome class format
            parts = icon_data.split()
            if len(parts) >= 2:
                # Should have at least style (fa-solid/fa-regular/fa-brands) and icon name
                valid_styles = ['fa-solid', 'fa-regular', 'fa-light', 'fa-thin', 'fa-duotone', 'fa-brands']
                return parts[0] in valid_styles and all(p.startswith('fa-') for p in parts)
            return False
        
        # Legacy support: Check if it's base64 encoded SVG
        if icon_data.startswith('data:image/svg+xml;base64,'):
            try:
                # Decode base64
                base64_data = icon_data.split(',')[1]
                decoded = base64.b64decode(base64_data).decode('utf-8')
                return '<svg' in decoded.lower()
            except Exception:
                return False
        
        # Legacy support: Check if it's raw SVG
        if '<svg' in icon_data.lower():
            return True
            
        return False
    
    async def create_extension(
        self,
        name: str,
        description: str,
        icon: str,
        category: str,
        system_prompt: str = None,
        required_files: List[str] = None,
        created_by: str = None,
        is_active: bool = True,
        welcome_message: str = "",
        input_placeholder: str = "",
        extension_type: str = "prompt-based",
        script_config: Dict = None
    ) -> Dict:
        """
        Create a new extension (prompt-based or script-based)
        
        Args:
            name: Extension name
            description: Extension description
            icon: SVG icon (base64 encoded or raw SVG)
            category: Extension category
            system_prompt: System prompt for the extension (required for prompt-based)
            required_files: List of required file types/names
            created_by: User ID of creator (admin)
            is_active: Whether extension is active
            welcome_message: Welcome message shown in chat
            input_placeholder: Input placeholder text
            extension_type: 'prompt-based' or 'script-based' (default: 'prompt-based')
            script_config: Script configuration for script-based extensions (optional)
            description: Extension description
            icon: SVG icon (base64 encoded or raw SVG)
            category: Extension category
            system_prompt: System prompt for the extension
            required_files: List of required file types/names
            created_by: User ID of creator (admin)
            is_active: Whether extension is active
            welcome_message: Welcome message shown in chat
            input_placeholder: Input placeholder text
            extension_type: 'prompt-based' or 'script-based' (default: 'prompt-based')
            script_config: Script configuration for script-based extensions (optional)
            category: Extension category
            system_prompt: System prompt for the extension
            required_files: List of required file types/names
            created_by: User ID of creator (admin)
            is_active: Whether extension is active
            welcome_message: Welcome message shown in chat
            input_placeholder: Input placeholder text
            
        Returns:
            Created extension document
            
        Raises:
            ValueError: If validation fails
        """
        # Handle None defaults
        if required_files is None:
            required_files = []
        
        # Validate inputs
        if not name or len(name.strip()) < 3:
            raise ValueError("Extension name must be at least 3 characters")
        
        if not description or len(description.strip()) < 10:
            raise ValueError("Extension description must be at least 10 characters")
        
        if not welcome_message or len(welcome_message.strip()) < 10:
            raise ValueError("Welcome message must be at least 10 characters")
        
        if not input_placeholder or len(input_placeholder.strip()) < 10:
            raise ValueError("Input placeholder must be at least 10 characters")
        
        if not self._validate_svg_icon(icon):
            raise ValueError("Invalid icon format. Use FontAwesome class (e.g., 'fa-solid fa-book')")
        
        if category not in ["Academic", "Planning", "Research", "Career", "Learning"]:
            raise ValueError("Invalid category")
        
        # Validate system_prompt only for prompt-based extensions
        if extension_type == "prompt-based":
            if not system_prompt or len(system_prompt.strip()) < 20:
                raise ValueError("System prompt must be at least 20 characters for prompt-based extensions")
        
        # Generate extension ID
        extension_id = self._generate_extension_id(name)
        
        # Check if extension ID already exists
        if await self.repo.extension_exists(extension_id):
            raise ValueError(f"Extension with ID '{extension_id}' already exists")
        
        # Create extension data
        extension_data = {
            "extension_id": extension_id,
            "name": name.strip(),
            "description": description.strip(),
            "icon": icon,
            "category": category,
            "required_files": required_files,
            "created_by": created_by,
            "is_active": is_active,
            "welcome_message": welcome_message.strip(),
            "input_placeholder": input_placeholder.strip(),
            "extension_type": extension_type
        }
        
        # Add system_prompt only for prompt-based extensions
        if extension_type == "prompt-based" and system_prompt:
            extension_data["system_prompt"] = system_prompt.strip()
        
        # Add script config if provided (for script-based extensions)
        if script_config:
            extension_data["script_config"] = script_config
        
        # Create in database
        extension = await self.repo.create_extension(extension_data)
        
        return extension
    
    async def get_all_extensions(self, active_only: bool = True) -> List[Dict]:
        """
        Get all extensions
        
        Args:
            active_only: If True, only return active extensions
            
        Returns:
            List of extensions
        """
        return await self.repo.get_all_extensions(active_only)
    
    async def get_extension(self, extension_id: str) -> Optional[Dict]:
        """
        Get a specific extension by ID
        
        Args:
            extension_id: Extension ID
            
        Returns:
            Extension document or None
        """
        return await self.repo.get_extension_by_id(extension_id)
    
    async def delete_extension(self, extension_id: str) -> bool:
        """
        Delete an extension (hard delete)
        
        Args:
            extension_id: Extension ID
            
        Returns:
            True if deleted, False otherwise
        """
        return await self.repo.delete_extension(extension_id)
    
    async def get_extensions_by_category(self, category: str) -> List[Dict]:
        """
        Get extensions by category
        
        Args:
            category: Category name
            
        Returns:
            List of extensions in the category
        """
        return await self.repo.get_extensions_by_category(category)
    
    def format_extension_for_response(self, extension: Dict) -> Dict:
        """
        Format extension document for API response
        
        Args:
            extension: Extension document from database
            
        Returns:
            Formatted extension data
        """
        script_config = extension.get("script_config", None)
        if script_config and isinstance(script_config, dict):
            script_config = {
                key: value for key, value in script_config.items()
                if key != "script_source_b64"
            }

        return {
            "id": extension["extension_id"],
            "name": extension["name"],
            "description": extension["description"],
            "icon": extension["icon"],
            "category": extension["category"],
            "systemPrompt": extension.get("system_prompt", ""),  # Optional for script-based
            "requiredFiles": extension.get("required_files", []),
            "createdBy": extension["created_by"],
            "createdAt": extension["created_at"].isoformat() if "created_at" in extension else None,
            "isActive": extension.get("is_active", True),
            "welcomeMessage": extension.get("welcome_message", ""),
            "inputPlaceholder": extension.get("input_placeholder", ""),
            "extensionType": extension.get("extension_type", "prompt-based"),
            "scriptConfig": script_config
        }
