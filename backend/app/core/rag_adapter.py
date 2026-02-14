# RAG pipeline adapter - interfaces with rag.pipeline
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from rag.pipeline import RAGPipeline

class RAGAdapter:
    def __init__(self):
        # Use absolute path to ChromaDB from project root
        chroma_db_path = str(project_root / "data" / "chroma_db")
        
        self.rag_pipeline = RAGPipeline(persist_directory=chroma_db_path)
    
    def query(
        self, 
        question: str, 
        conversation_history: list = None, 
        conversation_metadata: dict = None,
        user_preferences: list = None,
        preference_instructions: str = None,
        user_context: str = None
    ) -> dict:
        """Query the RAG pipeline with conversation history, user preferences, and user context"""
        return self.rag_pipeline.query(
            question=question,
            conversation_history=conversation_history or [],
            conversation_metadata=conversation_metadata or {},
            user_preferences=user_preferences or [],
            preference_instructions=preference_instructions,
            user_context=user_context
        )
    
rag_adapter = RAGAdapter()