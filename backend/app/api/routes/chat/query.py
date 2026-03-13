# POST /api/v1/query endpoint
from fastapi import APIRouter, HTTPException, Depends, File, Form, UploadFile, Request
from app.api.schemas.query import QueryRequest, QueryResponse
from app.services.query_service import query_service
from app.core.auth_middleware import get_optional_user
from typing import Optional, Dict

query_router = APIRouter()

@query_router.post("/query", response_model=QueryResponse)
async def query(
    http_request: Request,
    current_user: Optional[Dict] = Depends(get_optional_user),
    question: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """
    Handle user query and return answer with sources.
    Supports both JSON and multipart/form-data (with file upload).
    """
    # Add user_id to request if authenticated
    user_id = current_user.get("user_id") if current_user else None
    
    # Check content type to determine how to parse request
    content_type = http_request.headers.get("content-type", "")
    
    # Handle multipart/form-data (with or without file)
    if "multipart/form-data" in content_type:
        if not question or not session_id:
            raise HTTPException(status_code=400, detail="Missing question or session_id in form data")
        
        # Create request from form data
        req = QueryRequest(question=question, session_id=session_id)
        
        if file:
            # File upload case - read file content
            file_content = await file.read()
            file_data = {
                "filename": file.filename,
                "content": file_content,
                "content_type": file.content_type
            }
            response = await query_service.query(req, user_id=user_id, file_data=file_data)
        else:
            # Form data without file
            response = await query_service.query(req, user_id=user_id)
    
    # Handle JSON request
    elif "application/json" in content_type:
        body = await http_request.json()
        request_obj = QueryRequest(**body)
        response = await query_service.query(request_obj, user_id=user_id)
    
    else:
        raise HTTPException(status_code=400, detail="Invalid content type. Use application/json or multipart/form-data")
    
    if isinstance(response, str):
        raise HTTPException(status_code=400, detail=response)
    return response