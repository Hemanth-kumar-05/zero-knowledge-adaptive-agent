"""
Global Configuration for Canonical RAG System
Single source of truth for all environment variables
Used by both backend API and RAG pipeline
"""

import os
from pathlib import Path
from urllib.parse import urlparse
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
    # Authentication & Authorization (Phase 2)
    # ============================================
    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    # LLM for Preference Extraction
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Preference Extraction Settings
    PREFERENCE_EXTRACTION_ENABLED = os.getenv("PREFERENCE_EXTRACTION_ENABLED", "true").lower() == "true"
    PREFERENCE_MIN_CONFIDENCE = float(os.getenv("PREFERENCE_MIN_CONFIDENCE", "0.70"))
    PREFERENCE_MAX_PER_USER = int(os.getenv("PREFERENCE_MAX_PER_USER", "50"))
    PREFERENCE_DAILY_LIMIT = int(os.getenv("PREFERENCE_DAILY_LIMIT", "20"))
    
    # ============================================
    # Phase 3 - Policy Unlearning (Feature Flags)
    # ============================================
    ENABLE_POLICY_UNLEARNING = os.getenv("ENABLE_POLICY_UNLEARNING", "false").lower() == "true"
    POLICY_UPDATE_APPROVAL_REQUIRED = os.getenv("POLICY_UPDATE_APPROVAL_REQUIRED", "true").lower() == "true"
    
    # Confidence thresholds for auto-categorization
    POLICY_CLAIM_CONFIDENCE_LOW = float(os.getenv("POLICY_CLAIM_CONFIDENCE_LOW", "0.3"))
    POLICY_CLAIM_CONFIDENCE_MEDIUM = float(os.getenv("POLICY_CLAIM_CONFIDENCE_MEDIUM", "0.6"))
    POLICY_CLAIM_CONFIDENCE_HIGH = float(os.getenv("POLICY_CLAIM_CONFIDENCE_HIGH", "0.85"))
    
    # Cloudinary Configuration (Phase 3 - Proof Upload)
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
    CLOUDINARY_FOLDER = os.getenv("CLOUDINARY_FOLDER", "policy_proofs")
    
    # Application URLs
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
    
    # ============================================
    # CORS Configuration
    # ============================================
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", '["*"]')

    # ============================================
    # ChromaDB Configuration
    # ============================================
    # When CHROMA_HOST is set the app connects via HttpClient (Docker / remote).
    # When unset it falls back to PersistentClient using a local path (dev default).
    CHROMA_HOST = os.getenv("CHROMA_HOST")
    CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
    CHROMA_SSL = os.getenv("CHROMA_SSL", "false").lower() == "true"

    @classmethod
    def is_chroma_http_mode(cls) -> bool:
        """Whether ChromaDB should be accessed over HTTP."""
        return bool(cls.CHROMA_HOST)

    @classmethod
    def get_chroma_connection_info(cls, persist_directory: str = "data/chroma_db"):
        """
        Return normalized connection metadata for the active ChromaDB mode.

        Accepts either:
        - CHROMA_HOST=localhost with optional CHROMA_PORT / CHROMA_SSL
        - CHROMA_HOST=http://localhost:8000
        - CHROMA_HOST=https://example.com
        """
        if not cls.CHROMA_HOST:
            return {
                "mode": "persistent",
                "persist_directory": persist_directory,
            }

        host = cls.CHROMA_HOST.strip()
        port = cls.CHROMA_PORT
        ssl = cls.CHROMA_SSL

        if "://" in host:
            parsed = urlparse(host)
            host = parsed.hostname or host
            port = parsed.port or port
            ssl = parsed.scheme == "https"

        return {
            "mode": "http",
            "host": host,
            "port": port,
            "ssl": ssl,
            "scheme": "https" if ssl else "http",
            "url": f"{'https' if ssl else 'http'}://{host}:{port}",
        }

    @classmethod
    def get_chroma_client(cls, persist_directory: str = "data/chroma_db"):
        """Return an HttpClient when CHROMA_HOST is configured, else PersistentClient."""
        import chromadb
        connection_info = cls.get_chroma_connection_info(persist_directory)
        if connection_info["mode"] == "http":
            return chromadb.HttpClient(
                host=connection_info["host"],
                port=connection_info["port"],
                ssl=connection_info["ssl"]
            )
        return chromadb.PersistentClient(path=persist_directory)

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
