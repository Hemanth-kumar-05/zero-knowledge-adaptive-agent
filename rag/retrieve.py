import sys
from pathlib import Path
from typing import List, Dict

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from embeddings.embedder import Embedder
from embeddings.build_index import VectorIndex


class Retriever:
    """Handles document retrieval from vector database"""
    
    def __init__(
        self,
        persist_directory: str = "data/chroma_db",
        collection_name: str = "academic_docs"
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.index = VectorIndex(persist_directory)
        self.index.create_collection(collection_name, recreate=False)
        self.embedder = Embedder()
    
    @property
    def collection(self):
        """Access the underlying ChromaDB collection"""
        return self.index.collection
    
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.3,
        active_only: bool = True  # Phase 3: Filter deprecated chunks
    ) -> List[Dict]:
        results = self.index.search(
            query,
            top_k=top_k,
            min_similarity=min_similarity,
            embedder=self.embedder
        )
        
        # Phase 3: Filter out deprecated chunks if active_only=True
        if active_only:
            results = [
                r for r in results 
                if r.get('metadata', {}).get('status', 'active') == 'active'
            ]
        
        return results
    
    def format_context_for_llm(self, results: List[Dict]) -> str:
        context_parts = []
        
        for result in results:
            metadata = result.get('metadata', {})
            doc_id = metadata.get('doc_id', 'unknown')
            section = metadata.get('section', 'unknown')
            text = result.get('text', '')
            
            context_part = f"[Source: {doc_id} - {section}]\n{text}"
            context_parts.append(context_part)
        
        return "\n\n".join(context_parts)


# ============================================================================
# TESTING SECTION
# ============================================================================

# if __name__ == "__main__":
#     print("🧪 Testing Retrieval System...\n")
    
#     # Test 1: Initialize retriever
#     print("1️⃣ Initializing retriever...")
#     retriever = Retriever()
#     print("   ✓ Retriever initialized")
    
#     # Test 2: Test retrieval
#     print("\n2️⃣ Testing retrieval with sample queries...")
    
#     test_queries = [
#         "How do I register for exams?",
#         "What is the grading system?",
#         "Tell me about final year projects",
#         "What are the internship requirements?"
#     ]
    
#     for query in test_queries:
#         print(f"\n   Query: '{query}'")
#         results = retriever.retrieve(query, top_k=3, min_similarity=0.2)
        
#         if results:
#             print(f"   ✓ Found {len(results)} relevant chunks")
#             for i, result in enumerate(results, 1):
#                 print(f"      [{i}] Score: {result['similarity']:.3f} | "
#                       f"Section: {result['metadata']['section']}")
#         else:
#             print("   ⚠️  No results found (check min_similarity threshold)")
    
#     # Test 3: Test context formatting
#     print("\n3️⃣ Testing context formatting...")
#     query = "How do I register for exams?"
#     results = retriever.retrieve(query, top_k=2)
    
#     if results:
#         context = retriever.format_context_for_llm(results)
#         print(f"\n   Formatted context ({len(context)} characters):")
#         print("   " + "-" * 50)
#         print("   " + context[:300] + "...")
#         print("   " + "-" * 50)
    
#     # Test 4: Test metadata filtering
#     # print("\n4️⃣ Testing metadata filtering...")
#     # query = "Tell me about academic policies"
#     # all_results = retriever.retrieve(query, top_k=10, min_similarity=0.1)
#     # print(f"   Total results: {len(all_results)}")
    
#     # if all_results:
#     #     # Filter for specific document
#     #     filtered = retriever.filter_by_metadata(
#     #         all_results,
#     #         doc_id="ncie_exam_registration_process"
#     #     )
#     #     print(f"   Filtered by doc_id: {len(filtered)} results")
    
#     print("\n" + "="*60)
#     print("✅ Retrieval tests complete!")
#     print("="*60)
#     print("\n💡 Next: Implement generate.py to create answers from retrieved context")
