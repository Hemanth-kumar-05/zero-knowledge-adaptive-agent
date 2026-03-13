"""
Extension Executor Service
Dynamically loads and executes extension scripts
"""

import importlib.util
import tempfile
import os
import asyncio
from typing import Dict, Optional
from bson import ObjectId


class ExtensionExecutor:
    """Execute custom extension scripts dynamically and safely"""
    
    def __init__(self, db):
        """
        Initialize executor with database connection
        
        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.execution_timeout = 30  # 30 seconds max execution time
    
    async def execute_script(
        self, 
        extension: Dict, 
        file_data: bytes,
        session_id: str,
        user_id: str
    ) -> Dict:
        """
        Load and execute extension script dynamically
        
        Args:
            extension: Extension document from database
            file_data: Uploaded file content as bytes
            session_id: Current session ID
            user_id: User ID who uploaded the file
            
        Returns:
            dict with execution results or error
        """
        try:
            script_config = extension.get("script_config")
            
            if not script_config:
                # Fallback to prompt-based mode
                return {
                    "success": False,
                    "error": "No script configuration found",
                    "fallback": "prompt-based"
                }
            
            script_file_id = script_config.get("script_file_id")
            handler_function = script_config.get("handler_function", "process")
            
            if not script_file_id:
                return {
                    "success": False,
                    "error": "No script file uploaded",
                    "fallback": "prompt-based"
                }
            
            # Retrieve script from GridFS
            from motor.motor_asyncio import AsyncIOMotorGridFSBucket
            from io import BytesIO
            fs = AsyncIOMotorGridFSBucket(self.db)
            
            # Download script content
            stream = BytesIO()
            await fs.download_to_stream(ObjectId(script_file_id), stream)
            script_content = stream.getvalue()
            
            # Execute script with timeout
            result = await self._execute_with_timeout(
                script_content=script_content,
                handler_function=handler_function,
                file_data=file_data,
                session_id=session_id,
                user_id=user_id
            )
            
            return {
                "success": True,
                "result": result,
                "extension_type": "script-based"
            }
        
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "Script execution timed out (max 30s)",
                "fallback": "prompt-based"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Script execution failed: {str(e)}",
                "fallback": "prompt-based"
            }
    
    async def _execute_with_timeout(
        self,
        script_content: bytes,
        handler_function: str,
        file_data: bytes,
        session_id: str,
        user_id: str
    ):
        """
        Execute script with timeout protection
        
        Args:
            script_content: Python script content
            handler_function: Function name to call
            file_data: Input file data
            session_id: Session ID
            user_id: User ID
            
        Returns:
            Result from handler function
        """
        # Create temporary file for dynamic import
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
            tmp.write(script_content.decode('utf-8'))
            tmp_path = tmp.name
        
        try:
            # Dynamic import with timeout
            result = await asyncio.wait_for(
                self._load_and_execute(tmp_path, handler_function, file_data, session_id, user_id),
                timeout=self.execution_timeout
            )
            return result
        
        finally:
            # Cleanup temporary file
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except:
                    pass  # Ignore cleanup errors
    
    async def _load_and_execute(
        self,
        script_path: str,
        handler_function: str,
        file_data: bytes,
        session_id: str,
        user_id: str
    ):
        """
        Load module and execute handler function
        
        Args:
            script_path: Path to temporary script file
            handler_function: Function name to call
            file_data: Input file data
            session_id: Session ID
            user_id: User ID
            
        Returns:
            Result from handler function
        """
        # Dynamic import from file path
        spec = importlib.util.spec_from_file_location("extension_script", script_path)
        if not spec or not spec.loader:
            raise ImportError("Failed to load script module")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get handler function
        if not hasattr(module, handler_function):
            raise AttributeError(f"Function '{handler_function}' not found in script")
        
        handler = getattr(module, handler_function)
        
        # Check if handler is async or sync
        if asyncio.iscoroutinefunction(handler):
            result = await handler(
                file_data=file_data,
                session_id=session_id,
                user_id=user_id
            )
        else:
            # Run sync function in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                handler,
                file_data,
                session_id,
                user_id
            )
        
        return result
    
    @staticmethod
    def validate_result(result: any) -> Dict:
        """
        Validate and normalize script execution result
        
        Args:
            result: Result from script execution
            
        Returns:
            Normalized result dictionary
        """
        if not isinstance(result, dict):
            return {
                "success": False,
                "error": "Script must return a dictionary"
            }
        
        # Ensure required fields
        if "success" not in result:
            result["success"] = True
        
        return result
