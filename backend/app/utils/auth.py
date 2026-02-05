"""
Authentication Utilities
JWT token generation and validation
"""

from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from config import Config


class AuthUtils:
    """Utility class for authentication operations"""
    
    @staticmethod
    def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token
        
        Args:
            data: Dictionary containing user data (user_id, email, name)
            expires_delta: Optional custom expiration time
            
        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRATION_HOURS)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow()
        })
        
        encoded_jwt = jwt.encode(
            to_encode,
            Config.JWT_SECRET_KEY,
            algorithm=Config.JWT_ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict]:
        """
        Verify and decode a JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                Config.JWT_SECRET_KEY,
                algorithms=[Config.JWT_ALGORITHM]
            )
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def extract_token_from_header(authorization: str) -> Optional[str]:
        """
        Extract token from Authorization header
        
        Args:
            authorization: Authorization header value (e.g., "Bearer <token>")
            
        Returns:
            Token string if valid format, None otherwise
        """
        if not authorization:
            return None
        
        parts = authorization.split()
        
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
        
        return parts[1]
