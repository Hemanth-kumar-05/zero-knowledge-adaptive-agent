"""
Evidence Extraction Service (Phase 3)
Extracts structured evidence from policy change claims
"""

from typing import Dict, Optional
import logging
import re
from datetime import datetime
from config import config

logger = logging.getLogger(__name__)


class EvidenceExtractor:
    """
    AI-powered service to extract structured evidence from policy claims
    
    Extracts:
    - Circular numbers (e.g., "Circular 2024-03")
    - Dates mentioned (e.g., "January 15, 2025")
    - Policy references (e.g., "Section 4.2")
    - Specific claims (normalized text)
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize Evidence Extractor
        
        Args:
            llm_client: LLM client (Gemini or OpenAI)
        """
        self.llm_client = llm_client
        self.enabled = config.ENABLE_POLICY_UNLEARNING
    
    def _build_extraction_prompt(
        self,
        claim_text: str,
        user_message: str
    ) -> str:
        """Build prompt for evidence extraction"""
        
        prompt = f"""You are an evidence extraction expert for policy documents. Extract structured information from the user's claim.

USER MESSAGE:
{user_message}

IDENTIFIED CLAIM:
{claim_text}

EXTRACT THE FOLLOWING:
1. CIRCULAR_NUMBER: Any circular, memo, or document reference
   - Examples: "Circular 2024-03", "NCIE/ACAD/2024/015", "Memo dated 15-Jan-2024"
   
2. DATE_MENTIONED: Any specific dates mentioned
   - Examples: "January 15, 2025", "15/01/2025", "next semester"
   
3. POLICY_REFERENCE: Section, article, or rule references
   - Examples: "Section 4.2", "Article 5", "Rule 3.1.2"
   
4. SPECIFIC_CLAIM: The core claim in clear, concise language
   - Normalize to clear statement
   
5. EVIDENCE_STRENGTH: Assess strength of evidence
   - "weak": Vague claim, no specifics
   - "moderate": Some details but incomplete
   - "strong": Specific references and details

Respond in JSON format:
{{
    "circular_number": "extracted value or null",
    "date_mentioned": "extracted value or null",
    "policy_reference": "extracted value or null",
    "specific_claim": "normalized claim statement",
    "evidence_strength": "weak" | "moderate" | "strong",
    "extraction_notes": "Brief notes on what was found"
}}"""
        
        return prompt
    
    async def extract_evidence(
        self,
        claim_text: str,
        user_message: str
    ) -> Dict:
        """
        Extract structured evidence from claim
        
        Args:
            claim_text: The identified claim text
            user_message: Full user message for context
            
        Returns:
            {
                "circular_number": str | None,
                "date_mentioned": str | None,
                "policy_reference": str | None,
                "specific_claim": str,
                "evidence_strength": str,  # "weak", "moderate", "strong"
                "extraction_notes": str
            }
        """
        if not self.enabled:
            logger.info("Evidence extraction disabled (feature flag off)")
            return {
                "circular_number": None,
                "date_mentioned": None,
                "policy_reference": None,
                "specific_claim": claim_text,
                "evidence_strength": "weak",
                "extraction_notes": "Feature disabled"
            }
        
        if not claim_text:
            return {
                "circular_number": None,
                "date_mentioned": None,
                "policy_reference": None,
                "specific_claim": "",
                "evidence_strength": "weak",
                "extraction_notes": "Empty claim"
            }
        
        try:
            # Build extraction prompt
            prompt = self._build_extraction_prompt(claim_text, user_message)
            
            # Call LLM for extraction
            if self.llm_client:
                response = await self._call_llm(prompt)
                result = self._parse_llm_response(response)
            else:
                # Fallback: Use regex-based heuristic extraction
                result = self._heuristic_extraction(claim_text, user_message)
            
            logger.info(f"Evidence extraction: {result['evidence_strength']} strength")
            return result
            
        except Exception as e:
            logger.error(f"Error in evidence extraction: {e}")
            return {
                "circular_number": None,
                "date_mentioned": None,
                "policy_reference": None,
                "specific_claim": claim_text,
                "evidence_strength": "weak",
                "extraction_notes": f"Extraction failed: {str(e)}"
            }
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM for evidence extraction (placeholder)"""
        # TODO: Implement actual LLM call
        import json
        return json.dumps({
            "circular_number": None,
            "date_mentioned": None,
            "policy_reference": None,
            "specific_claim": "LLM integration pending",
            "evidence_strength": "weak",
            "extraction_notes": "LLM integration pending"
        })
    
    def _parse_llm_response(self, response: str) -> Dict:
        """Parse LLM JSON response"""
        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.error("Failed to parse LLM response for evidence extraction")
            return {
                "circular_number": None,
                "date_mentioned": None,
                "policy_reference": None,
                "specific_claim": "Parse error",
                "evidence_strength": "weak",
                "extraction_notes": "Parse error"
            }
    
    def _heuristic_extraction(
        self,
        claim_text: str,
        user_message: str
    ) -> Dict:
        """
        Fallback regex-based evidence extraction
        Uses pattern matching for common evidence types
        """
        combined_text = f"{user_message} {claim_text}"
        
        # Extract circular numbers
        circular_number = None
        circular_patterns = [
            r'[Cc]ircular\s*[:#]?\s*([A-Za-z0-9/-]+)',
            r'[Mm]emo\s*[:#]?\s*([A-Za-z0-9/-]+)',
            r'NCIE/[A-Z]+/\d{4}/\d+',
            r'[Dd]ocument\s*[:#]?\s*([A-Za-z0-9/-]+)'
        ]
        for pattern in circular_patterns:
            match = re.search(pattern, combined_text)
            if match:
                circular_number = match.group(0) if '/' in match.group(0) else match.group(1)
                break
        
        # Extract dates
        date_mentioned = None
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # 15/01/2025, 15-01-2025
            r'\b\d{4}-\d{2}-\d{2}\b',  # 2025-01-15
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',  # January 15, 2025
            r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b'  # 15 Jan 2025
        ]
        for pattern in date_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                date_mentioned = match.group(0)
                break
        
        # Extract policy references
        policy_reference = None
        policy_patterns = [
            r'[Ss]ection\s+\d+\.?\d*',
            r'[Aa]rticle\s+\d+',
            r'[Rr]ule\s+\d+\.?\d*\.?\d*',
            r'[Cc]hapter\s+\d+',
            r'[Pp]aragraph\s+\d+\.?\d*'
        ]
        for pattern in policy_patterns:
            match = re.search(pattern, combined_text)
            if match:
                policy_reference = match.group(0)
                break
        
        # Specific claim (first 200 chars of claim_text, cleaned)
        specific_claim = claim_text[:200].strip()
        
        # Determine evidence strength
        evidence_count = sum([
            circular_number is not None,
            date_mentioned is not None,
            policy_reference is not None
        ])
        
        if evidence_count >= 2:
            evidence_strength = "strong"
        elif evidence_count == 1:
            evidence_strength = "moderate"
        else:
            evidence_strength = "weak"
        
        extraction_notes = f"Heuristic extraction: {evidence_count} evidence types found"
        
        return {
            "circular_number": circular_number,
            "date_mentioned": date_mentioned,
            "policy_reference": policy_reference,
            "specific_claim": specific_claim,
            "evidence_strength": evidence_strength,
            "extraction_notes": extraction_notes
        }


# Singleton instance
evidence_extractor = EvidenceExtractor()
