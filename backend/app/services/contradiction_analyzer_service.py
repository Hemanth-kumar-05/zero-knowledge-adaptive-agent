"""
Contradiction Analyzer Service (Phase 3)
Analyzes contradictions between user claims and retrieved policy chunks using LLM
"""

from typing import Dict, List, Optional
import logging
import json
import os
from config import config

logger = logging.getLogger(__name__)

# Import LLM clients
try:
    from google import genai
    from groq import Groq
    print("LLM libraries imported successfully for contradiction analysis")
except ImportError as e:
    print(f"LLM libraries not available for contradiction analysis: {e}")
    genai = None
    Groq = None


class ContradictionAnalyzer:
    """
    AI-powered analyzer to detect contradictions between user claims
    and currently retrieved policy chunks
    """
    
    def __init__(self):
        """Initialize Contradiction Analyzer with LLM client"""
        self.enabled = config.ENABLE_POLICY_UNLEARNING
        self.llm_provider = os.getenv("LLM_PROVIDER", "groq").lower()
        
        if genai and Groq:
            if self.llm_provider == "groq":
                self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
                self.model = "llama-3.3-70b-versatile"
                print("🔍 ContradictionAnalyzer initialized with Groq")
            else:
                genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
                self.gemini_model = genai.GenerativeModel("gemini-1.5-flash-8b")
                self.model = "gemini-1.5-flash-8b"
                print("🔍 ContradictionAnalyzer initialized with Gemini")
        else:
            self.llm_provider = None
            print(f"LLM not available - will use heuristic fallback (genai={genai is not None}, Groq={Groq is not None})")
    
    def _build_contradiction_prompt(
        self,
        claim_text: str,
        retrieved_chunks: List[Dict]
    ) -> str:
        """Build prompt for LLM-based contradiction analysis"""
        
        # Format retrieved chunks with full context
        chunks_str = ""
        for i, chunk in enumerate(retrieved_chunks[:5], 1):  # Top 5 chunks
            doc_id = chunk.get("metadata", {}).get("doc_id", "unknown")
            section = chunk.get("metadata", {}).get("section", "unknown")
            text = chunk.get("text", "")
            chunks_str += f"\n[CHUNK {i}]\nDocument: {doc_id}\nSection: {section}\nContent: {text}\n{'-'*80}\n"
    
        prompt = f"""You are an expert policy analyst reviewing student claims about academic policies. Your task is to identify which policy chunks (if any) are affected by the user's claim and should be reviewed by administrators.

**USER'S CLAIM:**
{claim_text}

**CURRENT POLICY CHUNKS (Retrieved by relevance):**
{chunks_str}

**YOUR TASK:**
For each chunk, analyze:
1. **Relevance**: Is this chunk related to the user's claim?
2. **Contradiction/Update**: Does the user's claim suggest this chunk is outdated, incorrect, or needs updating?
3. **Confidence**: How confident are you that this chunk needs review? (0.0-1.0)

**WHAT TO FLAG FOR REVIEW:**
- User mentions different numbers/percentages than chunk (e.g., "50%" vs "40%")
- User cites a circular/date not mentioned in chunk
- User states something changed/updated that contradicts chunk
- User provides new information about the same topic as chunk
- User says "the latest circular", "new policy", "changed", "updated"

**BE INCLUSIVE:**
The goal is to show reviewers the **current policy text** so they can make informed decisions. When in doubt:
- If the claim is about the same topic as the chunk → Flag it (even at lower confidence)
- Reviewers need context to decide, so err on the side of including relevant chunks
- A 0.3+ confidence is sufficient if topics clearly overlap

**OUTPUT FORMAT (JSON only):**
{{
  "contradictions_found": true/false,
  "affected_chunks": [
    {{
      "chunk_index": 0,
      "doc_id": "document_name",
      "contradiction_score": 0.75,
      "specific_conflict": "User claims CA is 50% but chunk states 40%"
    }}
  ],
  "overall_confidence": 0.75,
  "reasoning": "Brief explanation of why these chunks need review"
}}

**IMPORTANT:**
- Include chunk_index (0-based) for each affected chunk
- contradiction_score should reflect confidence that chunk needs review (0.0-1.0)
- If NO chunks are affected, return empty affected_chunks array
- Be helpful to reviewers - include any chunk that might be relevant"""
        
        return prompt
    
    async def analyze_contradiction(
        self,
        claim_text: str,
        retrieved_chunks: List[Dict]
    ) -> Dict:
        """
        Analyze contradiction between claim and retrieved chunks
        
        Args:
            claim_text: The user's claim text
            retrieved_chunks: List of retrieved policy chunks from RAG
            
        Returns:
            {
                "contradictions_found": bool,
                "affected_chunks": List[{
                    "chunk_id": str,
                    "doc_id": str,
                    "current_text": str,
                    "contradiction_score": float,
                    "specific_conflict": str
                }],
                "overall_confidence": float
            }
        """
        if not self.enabled:
            print("Contradiction analysis disabled (feature flag off)")
            return {
                "contradictions_found": False,
                "affected_chunks": [],
                "overall_confidence": 0.0,
                "reasoning": "Feature disabled"
            }
        
        if not claim_text or not retrieved_chunks:
            return {
                "contradictions_found": False,
                "affected_chunks": [],
                "overall_confidence": 0.0,
                "reasoning": "Missing claim or chunks"
            }
        
        try:
            # Build contradiction analysis prompt
            prompt = self._build_contradiction_prompt(claim_text, retrieved_chunks)
            
            # Call LLM for analysis
            if self.llm_provider:
                print(f"🔍 Using {self.llm_provider.upper()} for contradiction analysis")
                response = await self._call_llm(prompt)
                result = self._parse_llm_response(response, retrieved_chunks)
            else:
                # Fallback: Use heuristic contradiction detection
                print("🔍 Using heuristic fallback for contradiction analysis")
                result = self._heuristic_contradiction(claim_text, retrieved_chunks)
            
            print(f"✅ Contradiction analysis: {len(result['affected_chunks'])} affected chunks identified")
            return result
            
        except Exception as e:
            print(f"Error in contradiction analysis: {e}")
            return {
                "contradictions_found": False,
                "affected_chunks": [],
                "overall_confidence": 0.0,
                "reasoning": f"Analysis failed: {str(e)}"
            }
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM for contradiction analysis"""
        try:
            if self.llm_provider == "groq":
                response = self.groq_client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,  # Lower temperature for more deterministic analysis
                    max_tokens=2000
                )
                result_text = response.choices[0].message.content.strip()
            else:  # gemini
                response = self.gemini_model.generate_content(prompt)
                result_text = response.text.strip()
            
            print(f"📄 LLM contradiction analysis result: {result_text[:150]}...")
            return result_text
            
        except Exception as e:
            print(f"LLM call failed: {e}")
            raise
    
    def _parse_llm_response(self, response: str, retrieved_chunks: List[Dict]) -> Dict:
        """Parse LLM JSON response and map chunk indices to actual chunks"""
        try:
            # Clean response if wrapped in markdown code blocks or has headers
            result_text = response.strip()
            
            # Remove markdown code blocks if present
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            # Strip any text before the first { (like markdown headers)
            json_start = result_text.find("{")
            if json_start > 0:
                result_text = result_text[json_start:]
            
            # Strip any text after the last }
            json_end = result_text.rfind("}")
            if json_end > 0:
                result_text = result_text[:json_end + 1]
            
            result = json.loads(result_text)
            
            # Map chunk indices to actual chunk IDs and include chunk text
            affected_chunks = []
            for chunk_info in result.get("affected_chunks", []):
                chunk_index = chunk_info.get("chunk_index", 0)
                if 0 <= chunk_index < len(retrieved_chunks):
                    actual_chunk = retrieved_chunks[chunk_index]
                    chunk_text = actual_chunk.get("text", "")
                    print(f"📋 Chunk {chunk_index}: id={actual_chunk.get('id')}, text_len={len(chunk_text)}, doc_id={actual_chunk.get('metadata', {}).get('doc_id')}")
                    affected_chunks.append({
                        "chunk_id": actual_chunk.get("id", f"chunk_{chunk_index}"),
                        "doc_id": chunk_info.get("doc_id") or actual_chunk.get("metadata", {}).get("doc_id", "unknown"),
                        "current_text": chunk_text,  # CRITICAL: Include full chunk text for reviewer
                        "contradiction_score": chunk_info.get("contradiction_score", 0.5),
                        "specific_conflict": chunk_info.get("specific_conflict", "Requires review")
                    })
            
            result["affected_chunks"] = affected_chunks
            print(f"✅ Parsed {len(affected_chunks)} affected chunks from LLM response")
            return result
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response: {e}\nResponse: {response[:200]}")
            return {
                "contradictions_found": False,
                "affected_chunks": [],
                "overall_confidence": 0.0,
                "reasoning": "Parse error"
            }
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            return {
                "contradictions_found": False,
                "affected_chunks": [],
                "overall_confidence": 0.0,
                "reasoning": f"Error: {str(e)}"
            }
    
    def _heuristic_contradiction(
        self,
        claim_text: str,
        retrieved_chunks: List[Dict]
    ) -> Dict:
        """
        Fallback heuristic contradiction detection (only used if LLM unavailable)
        For policy unlearning: Be inclusive - show reviewers relevant chunks
        """
        claim_lower = claim_text.lower()
        affected_chunks = []
        
        # Extract dates and numbers from claim
        import re
        claim_dates = re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', claim_text)
        claim_numbers = re.findall(r'\b\d+%?', claim_text)  # Include percentages
        
        # Policy change indicators
        policy_keywords = [
            "circular", "new policy", "updated", "latest", "passed",
            "will be", "will not", "now", "from now", "changed", "different"
        ]
        
        has_policy_signal = any(kw in claim_lower for kw in policy_keywords)
        
        # Analyze each chunk
        for i, chunk in enumerate(retrieved_chunks[:5]):
            chunk_text = chunk.get("text", "").lower()
            chunk_id = chunk.get("id", f"chunk_{i}")
            doc_id = chunk.get("metadata", {}).get("doc_id", "unknown")
            
            contradiction_score = 0.2  # Start with base score for retrieved relevance
            conflicts = []
            
            # Check for date mismatches
            chunk_dates = re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', chunk.get("text", ""))
            if claim_dates and chunk_dates:
                if not any(cd in chunk_dates for cd in claim_dates):
                    contradiction_score += 0.3
                    conflicts.append("Different dates mentioned")
            
            # Check for number/percentage mismatches
            chunk_numbers = re.findall(r'\b\d+%?', chunk.get("text", ""))
            if claim_numbers and chunk_numbers:
                mismatched_numbers = [n for n in claim_numbers if n not in chunk_numbers]
                if mismatched_numbers:
                    contradiction_score += 0.3
                    conflicts.append(f"Different values: {', '.join(mismatched_numbers)}")
            
            # Calculate topic relevance
            claim_words = set(w for w in claim_lower.split() if len(w) > 3)
            chunk_words = set(w for w in chunk_text.split() if len(w) > 3)
            overlap = len(claim_words & chunk_words) / max(len(claim_words), 1)
            
            # If mentions new policy about same topic
            if has_policy_signal and overlap > 0.2:
                contradiction_score += 0.3
                conflicts.append("Policy update claim about related topic")
            
            # Include relevant chunks (reviewers need context)
            if contradiction_score > 0.15 or overlap > 0.15:
                affected_chunks.append({
                    "chunk_id": chunk_id,
                    "doc_id": doc_id,
                    "current_text": chunk.get("text", ""),
                    "contradiction_score": min(contradiction_score, 1.0),
                    "specific_conflict": "; ".join(conflicts) if conflicts else "Retrieved relevant policy content"
                })
        
        contradictions_found = len(affected_chunks) > 0
        overall_confidence = sum(c["contradiction_score"] for c in affected_chunks) / max(len(affected_chunks), 1) if affected_chunks else 0.0
        
        reasoning = f"Heuristic analysis: {len(affected_chunks)} relevant chunks" if contradictions_found else "No relevant chunks detected"
        
        return {
            "contradictions_found": contradictions_found,
            "affected_chunks": affected_chunks,
            "overall_confidence": overall_confidence,
            "reasoning": reasoning
        }


# Singleton instance
contradiction_analyzer = ContradictionAnalyzer()
