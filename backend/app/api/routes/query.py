# POST /api/v1/query endpoint
from fastapi import APIRouter, HTTPException, Depends
from app.api.schemas.query import QueryRequest, QueryResponse
from app.services.query_service import query_service
from app.core.auth_middleware import get_optional_user
from typing import Optional, Dict

query_router = APIRouter()

@query_router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest, current_user: Optional[Dict] = Depends(get_optional_user)):
    """
    Handle user query and return answer with sources.
    """
    # Add user_id to request if authenticated
    user_id = current_user.get("user_id") if current_user else None
    
    response = await query_service.query(request, user_id=user_id)
    if isinstance(response, str):
        raise HTTPException(status_code=400, detail=response)
    return response