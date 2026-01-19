from typing import List
import numpy as np

from sentence_transformers import SentenceTransformer

class Embedder:
    """Handles text-to-embedding conversion"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
    
    def embed_text(self, text: str) -> List[float]:
        embedding = self.model.encode(text, normalize_embeddings=True, show_progress_bar=True)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        embeddings = self.model.encode(texts, batch_size=batch_size, normalize_embeddings=True, show_progress_bar=True)
        return [embedding.tolist() for embedding in embeddings]
    
    def get_embedding_dimension(self) -> int:
        test_embedding = self.embed_text("Test")
        return len(test_embedding)


# ============================================================================
# TESTING SECTION - Use this to verify your implementation works!
# ============================================================================

# if __name__ == "__main__":
#     print("🧪 Testing Embedder Implementation...")
    
#     # Test 1: Initialize embedder
#     print("\n1️⃣ Initializing embedder...")
#     embedder = Embedder()
    
#     # Test 2: Single text embedding
#     print("\n2️⃣ Testing single text embedding...")
#     test_text = "Academic advising helps students plan their coursework."
#     embedding = embedder.embed_text(test_text)
#     print(f"   ✓ Embedded text into {len(embedding)} dimensions")
#     print(f"   ✓ First 5 values: {embedding[:5]}")
    
#     # Test 3: Batch embedding
#     print("\n3️⃣ Testing batch embedding...")
#     test_texts = [
#         "Students must register for exams two weeks in advance.",
#         "The final year project requires a supervisor approval.",
#         "Lab evaluation contributes 25% to internal marks."
#     ]
#     embeddings = embedder.embed_batch(test_texts)
#     print(f"   ✓ Embedded {len(embeddings)} texts")
#     print(f"   ✓ Each embedding has {len(embeddings[0])} dimensions")
    
#     # Test 4: Verify similarity (similar texts should have similar embeddings)
#     print("\n4️⃣ Testing semantic similarity...")
#     query = "How do I register for exams?"
#     query_embedding = embedder.embed_text(query)
    
#     # Calculate cosine similarity with test texts
#     def cosine_similarity(vec1, vec2):
#         dot_product = np.dot(vec1, vec2)
#         norm1 = np.linalg.norm(vec1)
#         norm2 = np.linalg.norm(vec2)
#         return dot_product / (norm1 * norm2)
    
#     print(f"\n   Query: '{query}'")
#     for i, text in enumerate(test_texts):
#         similarity = cosine_similarity(query_embedding, embeddings[i])
#         print(f"   Similarity with text {i+1}: {similarity:.3f}")
    
#     print("\n✅ All tests complete! The text about exam registration should have highest similarity.")
