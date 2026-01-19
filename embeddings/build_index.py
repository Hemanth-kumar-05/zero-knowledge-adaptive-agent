import chromadb
from typing import List, Dict
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from embeddings.embedder import Embedder
from rag.ingest import load_markdown_files, create_chunks_with_metadata


class VectorIndex:
    """Manages the ChromaDB vector database"""
    
    def __init__(self, persist_directory: str = "data/chroma_db"):
        self.persist_directory = persist_directory
        
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = None
        
    def create_collection(
        self,
        collection_name: str = "academic_docs",
        recreate: bool = False
    ):
        if recreate:
            self.client.delete_collection(collection_name)
        self.collection = self.client.get_or_create_collection(collection_name)
    
    def add_documents(
        self,
        chunks: List[Dict[str, str]],
        embedder: Embedder,
        batch_size: int = 100
    ):
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            texts = [chunk['text'] for chunk in batch]
            embeddings = embedder.embed_batch(texts, batch_size=batch_size)
            
            ids = [f"doc_{i + j}" for j in range(len(batch))]
            metadatas = []
            for chunk in batch:
                metadata = chunk.copy()
                del metadata['text']
                metadatas.append(metadata)
            
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=texts
            )
    
    def search(
        self,
        query: str,
        embedder: Embedder,
        top_k: int = 5,
        min_similarity: float = 0.5
    ) -> List[Dict]:
        query_embedding = embedder.embed_text(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        hits = []
        for i in range(len(results['ids'][0])):
            similarity = results['distances'][0][i]
            if similarity >= min_similarity:
                hit = {
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'similarity': similarity
                }
                hits.append(hit)
        return hits
    
    def get_stats(self) -> Dict:
        stats = {
            'collection_name': self.collection.name,
            'total_documents': self.collection.count()
        }
        return stats


def build_index_from_documents(
    data_dir: str = "data/raw",
    chunk_size: int = 800,
    chunk_overlap: int = 100,
    persist_directory: str = "data/chroma_db",
    recreate: bool = True
):
    # Step 1: Load and chunk documents
    print("Step 1: Loading and chunking documents...")
    documents = load_markdown_files(data_dir)
    chunks = create_chunks_with_metadata(
        documents,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    # Step 2: Initialize embedder
    print("\nStep 2: Initializing embedder...")
    embedder = Embedder()
    
    # Step 3: Create vector index
    print("\nStep 3: Creating vector database...")
    vector_index = VectorIndex(persist_directory=persist_directory)
    vector_index.create_collection(recreate=recreate)
    
    # Step 4: Add documents to index
    print("\nStep 4: Adding documents to index...")
    vector_index.add_documents(
        chunks,
        embedder,
        batch_size=100
    )
    
    print("\nIndex building complete!")
    return vector_index 


# ============================================================================
# TESTING SECTION
# ============================================================================

# if __name__ == "__main__":
#     print("🧪 Testing Vector Index Creation...\n")
    
#     # Build the index
#     index = build_index_from_documents(
#         data_dir="data/raw",
#         chunk_size=800,
#         chunk_overlap=100,
#         recreate=True
#     )
    
#     # Test search
#     if index:
#         print("\n" + "="*60)
#         print("🔍 Testing Search Functionality")
#         print("="*60)
        
#         embedder = Embedder()
        
#         test_queries = [
#             "How do I register for exams?",
#             "What is the grading system?",
#             "Tell me about final year projects"
#         ]
        
#         for query in test_queries:
#             print(f"\n📝 Query: '{query}'")
#             results = index.search(query, embedder, top_k=3)
            
#             if results:
#                 print(f"   Found {len(results)} relevant chunks:")
#                 for i, result in enumerate(results, 1):
#                     print(f"\n   [{i}] Similarity: {result.get('similarity', 0):.3f}")
#                     print(f"       Doc ID: {result['metadata'].get('doc_id', 'unknown')}")
#                     print(f"       Section: {result['metadata'].get('section', 'unknown')}")
#                     print(f"       Type: {result['metadata'].get('type', 'unknown')}")
#                     print(f"       Text: {result['text'][:100]}...")
#             else:
#                 print("   ⚠️  No relevant results found")
    
#     print("\n" + "="*60)
#     print("✅ All tests complete!")
#     print("="*60)
#     print("\n💡 Next steps:")
#     print("   1. Experiment with different chunk_size values")
#     print("   2. Try different embedding models")
#     print("   3. Test with more queries")
#     print("   4. Move on to building the RAG pipeline (generate.py)")
