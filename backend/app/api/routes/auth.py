"""
Authentication Routes
Google OAuth and JWT token management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from google.oauth2 import id_token
from google.auth.transport import requests
from typing import Dict
from config import Config
from app.api.schemas.auth import (
    GoogleAuthRequest,
    GoogleCallbackRequest,
    TokenResponse,
    UserInfo,
    MessageResponse
)
from app.db.mongo import get_db
from app.db.repositories.users_repo import UsersRepository
from app.services.user_service import UserService
from app.utils.auth import AuthUtils
from app.core.auth_middleware import get_current_user
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/google", response_model=Dict)
async def initiate_google_auth(request: GoogleAuthRequest):
    """
    Initiate Google OAuth flow
    Returns the Google OAuth URL for frontend redirect
    """
    # Build Google OAuth URL
    scopes = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ]
    scope_param = "%20".join(scopes)
    oauth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={Config.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={Config.GOOGLE_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope={scope_param}&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    
    return {"auth_url": oauth_url}


@router.get("/google/callback")
async def google_callback(code: str = None, error: str = None, db=Depends(get_db)):
    """
    Handle Google OAuth callback
    Exchange authorization code for user info and generate JWT
    """
    try:
        # Check for OAuth errors
        if error:
            logger.error(f"OAuth error from Google: {error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Authentication failed: {error}"
            )
        
        if not code:
            logger.error("No authorization code received")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No authorization code received"
            )
        
        logger.info("Processing Google OAuth callback with code")
        
        # Validate config
        if not Config.GOOGLE_CLIENT_ID or not Config.GOOGLE_CLIENT_SECRET:
            logger.error("Google OAuth credentials not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OAuth not configured properly"
            )
        
        # Exchange authorization code for tokens
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import Flow
        import os
        
        # Create OAuth flow
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": Config.GOOGLE_CLIENT_ID,
                    "client_secret": Config.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [Config.GOOGLE_REDIRECT_URI]
                }
            },
            scopes=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile"
            ]
        )
        flow.redirect_uri = Config.GOOGLE_REDIRECT_URI
        
        logger.info(f"Using redirect URI: {Config.GOOGLE_REDIRECT_URI}")
        
        # Exchange code for tokens
        try:
            flow.fetch_token(code=code)
            credentials = flow.credentials
            logger.info("Successfully exchanged code for tokens")
        except Exception as token_error:
            logger.error(f"Token exchange failed: {str(token_error)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to exchange authorization code: {str(token_error)}"
            )
        
        # Verify the ID token with clock skew tolerance
        try:
            # Add 60 seconds of clock skew tolerance to handle time sync issues
            idinfo = id_token.verify_oauth2_token(
                credentials.id_token,
                requests.Request(),
                Config.GOOGLE_CLIENT_ID,
                clock_skew_in_seconds=60
            )
            logger.info("ID token verified successfully")
        except Exception as verify_error:
            logger.error(f"Token verification failed: {str(verify_error)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token verification failed: {str(verify_error)}"
            )
        
        # Check issuer
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        
        google_user_info = {
            "sub": idinfo.get("sub"),
            "email": idinfo.get("email"),
            "name": idinfo.get("name"),
            "picture": idinfo.get("picture")
        }
        
        logger.info(f"Successfully authenticated user: {google_user_info['email']}")
        
        # Get or create user
        users_repo = UsersRepository(db)
        user_service = UserService(users_repo)
        
        user = await user_service.get_or_create_user(google_user_info)
        
        # Generate JWT token
        token_data = {
            "user_id": str(user["_id"]),
            "email": user["email"],
            "name": user["name"]
        }
        
        access_token = AuthUtils.create_access_token(token_data)
        
        # Redirect to frontend with token in URL
        frontend_url = Config.FRONTEND_URL
        redirect_url = f"{frontend_url}/auth/callback?token={access_token}&user={user['email']}"
        
        return RedirectResponse(url=redirect_url)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Google callback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: Dict = Depends(get_current_user)):
    """
    Logout endpoint (token is managed on client side)
    """
    logger.info(f"User logged out: {current_user['email']}")
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(
    current_user: Dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Get current authenticated user information
    """
    users_repo = UsersRepository(db)
    user = await users_repo.get_user_by_id(current_user["user_id"])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserInfo(
        id=str(user["_id"]),
        email=user["email"],
        name=user["name"],
        profile_picture=user.get("profile_picture")
    )
