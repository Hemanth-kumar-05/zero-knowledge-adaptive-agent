"""
Semantic Policy Search Service

Finds all chunks related to a policy claim using semantic search,
without relying on keyword matching.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))  # project root for config

from typing import List, Dict, Optional
from groq import Groq
import os
import json
from embeddings.embedder import Embedder
import chromadb
from config import config


class SemanticPolicySearchService:
    """
    Semantic search for policy-related chunks across the knowledge base
    """
    
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_client = Groq(api_key=self.groq_api_key) if self.groq_api_key else None
        self.embedder = Embedder()
        
        # Connect to ChromaDB
        project_root = Path(__file__).parent.parent.parent.parent
        chroma_path = str(project_root / "data" / "chroma_db")
        self.chroma_client = config.get_chroma_client(chroma_path)
        self.collection = self.chroma_client.get_or_create_collection("academic_docs")
        
        print("✅ SemanticPolicySearchService initialized")
    
    async def extract_policy_concept(
        self, 
        user_claim: str, 
        proof_text: Optional[str] = None
    ) -> Dict:
        """
        Use LLM to extract the semantic concept from user's claim
        
        Returns: {
            "policy_area": "Continuous Assessment weightage",
            "search_query": "What is the current weightage of CA in total evaluation?",
            "concept_text": "Continuous Assessment contribution percentage"
        }
        """
        if not self.groq_client:
            # Fallback: simple extraction
            return {
                "policy_area": "Policy Update",
                "search_query": user_claim,
                "concept_text": user_claim
            }
        
        prompt = f"""You are a policy analyst. Extract the core policy concept from a user's claim.

User Claim: "{user_claim}"
{f'Proof Context: "{proof_text[:500]}"' if proof_text else ''}

Extract:
1. Policy Area: The specific policy domain (e.g., "Continuous Assessment weightage", "Exam registration deadline")
2. Search Query: A neutral question to find existing policy (e.g., "What is the current CA weightage?")
3. Concept Text: Short phrase for semantic embedding (e.g., "CA contribution percentage")

Respond ONLY with valid JSON:
{{
  "policy_area": "...",
  "search_query": "...",
  "concept_text": "..."
}}"""

        try:
            response = self.groq_client.chat.completions.create(
                model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=300
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Extract JSON
            json_start = result_text.find("{")
            json_end = result_text.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                result_text = result_text[json_start:json_end]
            
            concept = json.loads(result_text)
            print(f"📊 Extracted policy concept: {concept['policy_area']}")
            return concept
            
        except Exception as e:
            print(f"❌ Error extracting concept: {e}")
            return {
                "policy_area": "Policy Update",
                "search_query": user_claim,
                "concept_text": user_claim
            }
    
    def semantic_search_chunks(
        self, 
        concept_text: str, 
        top_k: int = 50
    ) -> List[Dict]:
        """
        Search ChromaDB for chunks semantically related to concept
        
        Returns list of chunks with metadata
        """
        # Embed the concept
        concept_embedding = self.embedder.embed_text(concept_text)
        
        # Search (no deprecated filter - we want to see all active chunks)
        results = self.collection.query(
            query_embeddings=[concept_embedding],
            n_results=top_k,
            where={"status": {"$ne": "deprecated"}}  # Only active chunks
        )
        
        chunks = []
        for idx, (chunk_id, text, distance, metadata) in enumerate(zip(
            results['ids'][0],
            results['documents'][0],
            results['distances'][0],
            results['metadatas'][0]
        )):
            similarity = 1 - distance
            chunks.append({
                'id': chunk_id,
                'text': text,
                'doc_id': metadata.get('doc_id', 'unknown'),
                'section': metadata.get('section', 'unknown'),
                'similarity': similarity,
                'metadata': metadata
            })
        
        print(f"🔍 Semantic search found {len(chunks)} chunks")
        return chunks
    
    async def filter_relevant_chunks(
        self,
        chunks: List[Dict],
        policy_area: str,
        user_claim: str
    ) -> Dict[str, List[Dict]]:
        """
        Use LLM to classify chunks as high confidence or possibly related
        
        Returns: {
            "high_confidence": [...],  # Definitely contains the policy
            "possibly_related": [...]   # Related but uncertain
        }
        """
        if not self.groq_client:
            # Fallback: use similarity threshold
            high_conf = [c for c in chunks if c['similarity'] >= 0.7]
            maybe = [c for c in chunks if 0.5 <= c['similarity'] < 0.7]
            return {"high_confidence": high_conf, "possibly_related": maybe}
        
        # Process in batches to avoid token limits
        high_confidence = []
        possibly_related = []
        
        for chunk in chunks[:30]:  # Limit to top 30 by similarity
            prompt = f"""Is this chunk related to the policy: "{policy_area}"?

User Claim: "{user_claim}"

Chunk Text:
"{chunk['text'][:400]}"

Classify as:
- "high": This chunk definitely discusses the policy mentioned
- "possible": This chunk is related but doesn't directly discuss it
- "unrelated": Not related

Respond with ONLY: high, possible, or unrelated"""

            try:
                response = self.groq_client.chat.completions.create(
                    os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=10
                )
                
                classification = response.choices[0].message.content.strip().lower()
                
                if "high" in classification:
                    high_confidence.append(chunk)
                elif "possible" in classification:
                    possibly_related.append(chunk)
                    
            except Exception as e:
                print(f"⚠️ Error classifying chunk {chunk['id']}: {e}")
                # On error, use similarity threshold
                if chunk['similarity'] >= 0.7:
                    high_confidence.append(chunk)
                else:
                    possibly_related.append(chunk)
        
        print(f"✅ Classified: {len(high_confidence)} high confidence, {len(possibly_related)} possibly related")
        return {
            "high_confidence": high_confidence,
            "possibly_related": possibly_related
        }
    
    def _deduplicate_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """
        Remove duplicate chunks based on text content
        
        When multiple chunks have identical text (but different IDs/metadata),
        keep only the most recent one or the one with highest similarity.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            Deduplicated list of chunks
        """
        seen_texts = {}
        deduplicated = []
        
        for chunk in chunks:
            text = chunk.get('text', '').strip()
            
            if not text:
                continue
            
            # If we haven't seen this text before, add it
            if text not in seen_texts:
                seen_texts[text] = chunk
                deduplicated.append(chunk)
            else:
                # If we've seen this text, keep the one with better similarity
                existing = seen_texts[text]
                if chunk.get('similarity', 0) > existing.get('similarity', 0):
                    # Replace with better match
                    deduplicated.remove(existing)
                    deduplicated.append(chunk)
                    seen_texts[text] = chunk
        
        removed_count = len(chunks) - len(deduplicated)
        if removed_count > 0:
            print(f"🧹 Removed {removed_count} duplicate chunks (same text content)")
        
        return deduplicated
    
    async def find_affected_chunks(
        self,
        user_claim: str,
        proof_text: Optional[str] = None
    ) -> Dict:
        """
        Complete workflow: Find all chunks affected by a policy claim
        
        Returns: {
            "policy_area": "...",
            "high_confidence_chunks": [...],
            "possibly_related_chunks": [...],
            "total_found": 29
        }
        """
        print("\n" + "="*80)
        print("🔍 SEMANTIC POLICY SEARCH")
        print("="*80)
        
        # Step 1: Extract policy concept
        print("\n1️⃣ Extracting policy concept...")
        concept = await self.extract_policy_concept(user_claim, proof_text)
        
        # Step 2: Semantic search
        print("\n2️⃣ Searching for related chunks...")
        all_chunks = self.semantic_search_chunks(concept["concept_text"], top_k=50)
        
        # Step 3: LLM filtering
        print("\n3️⃣ Classifying relevance...")
        classified = await self.filter_relevant_chunks(
            all_chunks,
            concept["policy_area"],
            user_claim
        )
        
        # Step 4: Deduplicate results
        print("\n4️⃣ Deduplicating chunks...")
        deduplicated_high = self._deduplicate_chunks(classified["high_confidence"])
        deduplicated_related = self._deduplicate_chunks(classified["possibly_related"])
        
        result = {
            "policy_area": concept["policy_area"],
            "search_query": concept["search_query"],
            "high_confidence_chunks": deduplicated_high,
            "possibly_related_chunks": deduplicated_related,
            "total_found": len(deduplicated_high) + len(deduplicated_related)
        }
        
        print("\n" + "="*80)
        print(f"✅ Found {result['total_found']} unique chunks (after deduplication)")
        print(f"   - {len(deduplicated_high)} high confidence")
        print(f"   - {len(deduplicated_related)} possibly related")
        print("="*80)
        
        return result


# Singleton instance
semantic_policy_search = SemanticPolicySearchService()
