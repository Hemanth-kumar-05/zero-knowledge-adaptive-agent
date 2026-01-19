"""
Global Configuration for Canonical RAG System
Single source of truth for all environment variables
Used by both backend API and RAG pipeline
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Global configuration class"""
    
    # ============================================
    # API Configuration
    # ============================================
    API_VERSION = os.getenv("API_VERSION", "1.0.0")
    API_TITLE = os.getenv("API_TITLE", "Canonical RAG System")
    API_PHASE = os.getenv("API_PHASE", "Phase I - Baseline RAG")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    # ============================================
    # MongoDB Configuration
    # ============================================
    MONGODB_URI = os.getenv("MONGODB_URI")
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "canonical_rag_db")

    # ============================================
    # Google Gemini API
    # ============================================
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # ============================================
    # CORS Configuration
    # ============================================
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", '["*"]')
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is required in .env file")
        
        return True
    
    @classmethod
    def get_db_config(cls):
        """Get MongoDB configuration"""
        return {
            "uri": cls.MONGODB_URI,
            "db_name": cls.MONGODB_DB_NAME,
        }

# Global config instance
config = Config()