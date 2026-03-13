"""
Extensions API Routes
Handles all extension management endpoints with RBAC
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import base64

from app.db.mongo import get_db
from app.core.auth_middleware import get_current_user
from app.services.extension_service import ExtensionService


router = APIRouter(prefix="/extensions", tags=["extensions"])


# Pydantic Models
class ExtensionCreate(BaseModel):
    """Schema for creating a new extension"""
    name: str = Field(..., min_length=3, max_length=100, description="Extension name")
    description: str = Field(..., min_length=10, max_length=500, description="Extension description")
    icon: str = Field(..., description="FontAwesome icon class (e.g., 'fa-solid fa-book')")
    category: str = Field(..., description="Extension category (Academic, Planning, Research, Career, Learning)")
    systemPrompt: str = Field(..., min_length=20, description="System prompt for the extension")
    requiredFiles: List[str] = Field(default_factory=list, description="List of required file types")
    isActive: bool = Field(default=True, description="Whether extension is active")
    welcomeMessage: str = Field(..., min_length=10, max_length=200, description="Welcome message shown in chat")
    inputPlaceholder: str = Field(..., min_length=10, max_length=100, description="Input placeholder text")
    
    # Script-based extension fields (optional)
    extensionType: str = Field(default="prompt-based", description="Extension type: 'prompt-based' or 'script-based'")
    handlerFunction: Optional[str] = Field(default=None, description="Handler function name for script-based extensions")
    dependencies: Optional[str] = Field(default=None, description="Comma-separated Python dependencies")


class ExtensionResponse(BaseModel):
    """Schema for extension response"""
    id: str
    name: str
    description: str
    icon: str
    category: str
    systemPrompt: str
    requiredFiles: List[str]
    createdBy: str
    createdAt: Optional[str]
    isActive: bool
    welcomeMessage: str
    inputPlaceholder: str
    
    # Script-based fields (optional)
    extensionType: str = "prompt-based"
    scriptConfig: Optional[dict] = None


@router.get("", response_model=List[ExtensionResponse])
async def get_all_extensions(
    active_only: bool = True,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all extensions
    
    **Accessible by**: All authenticated users (faculty and admin can view)
    
    **Query Parameters**:
    - active_only: If true, only return active extensions (default: true)
    
    **Returns**:
    - List of extension objects
    """
    try:
        service = ExtensionService(db)
        extensions = await service.get_all_extensions(active_only=active_only)
        
        # Format extensions for response
        formatted_extensions = [
            service.format_extension_for_response(ext)
            for ext in extensions
        ]
        
        return formatted_extensions
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve extensions: {str(e)}"
        )


@router.get("/{extension_id}", response_model=ExtensionResponse)
async def get_extension(
    extension_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific extension by ID
    
    **Accessible by**: All authenticated users
    
    **Path Parameters**:
    - extension_id: The unique extension identifier
    
    **Returns**:
    - Extension object
    """
    try:
        service = ExtensionService(db)
        extension = await service.get_extension(extension_id)
        
        if not extension:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Extension '{extension_id}' not found"
            )
        
        return service.format_extension_for_response(extension)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve extension: {str(e)}"
        )


@router.post("", response_model=ExtensionResponse, status_code=status.HTTP_201_CREATED)
async def create_extension(
    # Form fields
    name: str = Form(...),
    description: str = Form(...),
    icon: str = Form(...),
    category: str = Form(...),
    systemPrompt: Optional[str] = Form(None),
    welcomeMessage: str = Form(...),
    inputPlaceholder: str = Form(...),
    requiredFiles: str = Form(default=""),
    isActive: str = Form(default="true"),
    extensionType: str = Form(default="prompt-based"),
    
    # Script-based fields (optional)
    scriptFile: Optional[UploadFile] = File(None),
    scriptCode: Optional[str] = Form(None),
    handlerFunction: Optional[str] = Form(None),
    dependencies: Optional[str] = Form(None),
    
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new extension (supports both prompt-based and script-based)
    
    **Accessible by**: Admin only
    
    **Form Fields**:
    - name: Extension name
    - description: Extension description
    - icon: FontAwesome icon class
    - category: Extension category
    - systemPrompt: System prompt (required for prompt-based)
    - welcomeMessage: Welcome message
    - inputPlaceholder: Input placeholder  
    - requiredFiles: Comma-separated file types
    - isActive: "true" or "false"
    - extensionType: "prompt-based" or "script-based"
    - scriptFile: Python script file (optional, for script-based)
    - scriptCode: Inline Python code (optional, for script-based)
    - handlerFunction: Handler function name (for script-based)
    - dependencies: Comma-separated Python packages (optional)
    
    **Returns**:
    - Created extension object
    """
    # Check user permissions
    user_role = current_user.get("role", "student")
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create extensions"
        )
    
    try:
        from motor.motor_asyncio import AsyncIOMotorGridFSBucket
        from app.services.script_validator import ScriptValidator
        from datetime import datetime
        
        service = ExtensionService(db)
        
        # Validate based on extension type
        if extensionType == "prompt-based":
            if not systemPrompt or not systemPrompt.strip():
                raise ValueError("System prompt is required for prompt-based extensions")
        
        # Parse form data
        required_files_list = [f.strip() for f in requiredFiles.split(",") if f.strip()]
        is_active_bool = isActive.lower() == "true"
        
        script_config = None
        
        # Handle script-based extensions
        if extensionType == "script-based":
            if not handlerFunction:
                raise ValueError("Handler function name is required for script-based extensions")
            
            # Get script content (from file upload or inline code)
            script_content = None
            script_filename = None
            
            if scriptFile and scriptFile.filename:
                # Script uploaded as file
                script_content = await scriptFile.read()
                script_filename = scriptFile.filename
            elif scriptCode:
                # Inline script code
                script_content = scriptCode.encode('utf-8')
                script_filename = f"{name.lower().replace(' ', '_')}_script.py"
            else:
                raise ValueError("Either scriptFile or scriptCode is required for script-based extensions")
            
            # Validate script
            validation_result = ScriptValidator.validate(script_content, handlerFunction)
            
            if not validation_result["valid"]:
                raise ValueError(f"Script validation failed: {validation_result['error']}")
            
            # Store script in GridFS
            fs = AsyncIOMotorGridFSBucket(db)
            script_file_id = await fs.upload_from_stream(
                filename=script_filename,
                source=script_content,
                metadata={
                    "content_type": "text/x-python",
                    "handler_function": handlerFunction,
                    "uploaded_by": current_user["user_id"],
                    "uploaded_at": datetime.now(),
                    "extension_type": "script-based"
                }
            )
            
            # Create script configuration
            script_config = {
                "script_file_id": str(script_file_id),
                "script_filename": script_filename,
                "handler_function": handlerFunction,
                "version": "1.0.0",
                "uploaded_at": datetime.now(),
                "dependencies": [d.strip() for d in dependencies.split(",")] if dependencies else []
            }
        
        # Create extension
        extension = await service.create_extension(
            name=name,
            description=description,
            icon=icon,
            category=category,
            system_prompt=systemPrompt,
            required_files=required_files_list,
            created_by=current_user["user_id"],
            is_active=is_active_bool,
            welcome_message=welcomeMessage,
            input_placeholder=inputPlaceholder,
            extension_type=extensionType,
            script_config=script_config
        )
        
        return service.format_extension_for_response(extension)
    
    except ValueError as e:
        if "already exists" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create extension: {str(e)}"
        )


@router.delete("/{extension_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_extension(
    extension_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete an extension
    
    **Accessible by**: Admin only
    
    **Path Parameters**:
    - extension_id: The unique extension identifier
    
    **Returns**:
    - 204 No Content on success
    
    **Raises**:
    - 403: If user is not admin
    - 404: If extension not found
    """
    # Check user permissions (admin only)
    user_role = current_user.get("role", "student")
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete extensions"
        )
    
    try:
        service = ExtensionService(db)
        
        # Check if extension exists
        extension = await service.get_extension(extension_id)
        if not extension:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Extension '{extension_id}' not found"
            )
        
        # Delete extension
        deleted = await service.delete_extension(extension_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete extension"
            )
        
        return JSONResponse(
            status_code=status.HTTP_204_NO_CONTENT,
            content=None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete extension: {str(e)}"
        )


@router.get("/category/{category}", response_model=List[ExtensionResponse])
async def get_extensions_by_category(
    category: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all extensions in a specific category
    
    **Accessible by**: All authenticated users
    
    **Path Parameters**:
    - category: The category name (Academic, Planning, Research, Career, Learning)
    
    **Returns**:
    - List of extensions in the category
    """
    try:
        service = ExtensionService(db)
        extensions = await service.get_extensions_by_category(category)
        
        # Format extensions for response
        formatted_extensions = [
            service.format_extension_for_response(ext)
            for ext in extensions
        ]
        
        return formatted_extensions
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve extensions: {str(e)}"
        )
