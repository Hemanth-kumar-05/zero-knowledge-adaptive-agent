# POST /api/v1/query endpoint
from fastapi import APIRouter, HTTPException
from app.api.schemas.query import QueryRequest, QueryResponse
from app.services.query_service import query_service
from typing import Optional

query_router = APIRouter()

@query_router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Handle user query and return answer with sources.
    """
    # Placeholder implementation
    response = await query_service.query(request)
    if isinstance(response, str):
        raise HTTPException(status_code=400, detail=response)
    return response