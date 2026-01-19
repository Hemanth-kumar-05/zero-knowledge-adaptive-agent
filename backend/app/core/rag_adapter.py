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
    
    def query(self, question: str) -> dict:
        """Query the RAG pipeline with fixed Phase-1 parameters"""
        return self.rag_pipeline.query(question=question)
    
rag_adapter = RAGAdapter()