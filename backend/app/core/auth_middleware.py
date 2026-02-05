"""
Authentication Middleware
Dependency injection for protected routes
"""

from fastapi import Depends, HTTPException, status, Header
from typing import Optional, Dict
from backend.app.utils.auth import AuthUtils


async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict:
    """
    Dependency to get current authenticated user from JWT token
    
    Args:
        authorization: Authorization header from request
        
    Returns:
        User data from token payload
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not authorization:
        raise credentials_exception
    
    # Extract token from "Bearer <token>" format
    token = AuthUtils.extract_token_from_header(authorization)
    if not token:
        raise credentials_exception
    
    # Verify and decode token
    payload = AuthUtils.verify_token(token)
    if not payload:
        raise credentials_exception
    
    # Extract user information
    user_id = payload.get("user_id")
    email = payload.get("email")
    
    if not user_id or not email:
        raise credentials_exception
    
    return {
        "user_id": user_id,
        "email": email,
        "name": payload.get("name"),
    }


async def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[Dict]:
    """
    Dependency to optionally get current user (doesn't raise exception if not authenticated)
    
    Args:
        authorization: Authorization header from request
        
    Returns:
        User data if authenticated, None otherwise
    """
    if not authorization:
        return None
    
    token = AuthUtils.extract_token_from_header(authorization)
    if not token:
        return None
    
    payload = AuthUtils.verify_token(token)
    if not payload:
        return None
    
    return {
        "user_id": payload.get("user_id"),
        "email": payload.get("email"),
        "name": payload.get("name"),
    }
