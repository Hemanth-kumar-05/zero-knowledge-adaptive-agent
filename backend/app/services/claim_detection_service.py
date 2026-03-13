"""
Claim Detection Agent Service (Phase 3)
Detects if user messages contain policy change claims or contradictions
"""

from typing import Dict, List, Optional
import logging
from config import config

logger = logging.getLogger(__name__)


class ClaimDetectionAgent:
    """
    AI-powered agent to detect policy change claims in user messages
    
    Detects patterns like:
    - "This rule is outdated"
    - "But the new circular says..."
    - "I heard this changed recently"
    - "The deadline was modified"
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize Claim Detection Agent
        
        Args:
            llm_client: LLM client (Gemini or OpenAI)
        """
        self.llm_client = llm_client
        self.enabled = config.ENABLE_POLICY_UNLEARNING
    
    def _build_detection_prompt(
        self,
        user_message: str,
        conversation_context: List[Dict]
    ) -> str:
        """Build prompt for claim detection"""
        
        # Format conversation context (last 3 messages)
        context_str = ""
        if conversation_context:
            recent_context = conversation_context[-3:]
            for msg in recent_context:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                context_str += f"{role}: {content}\n"
        
        prompt = f"""You are a policy claim detection expert. Analyze the user's message to determine if they are making a claim about policy changes or contradictions.

CONVERSATION CONTEXT:
{context_str if context_str else "No prior context"}

CURRENT USER MESSAGE:
{user_message}

DETECTION CRITERIA:
Look for patterns indicating:
1. POLICY_OUTDATED: User claims current policy is outdated
   - Examples: "this rule changed", "the policy was updated", "that's no longer valid"
   
2. CONTRADICTION: User states something that contradicts system response
   - Examples: "but the circular says...", "actually the deadline is...", "that's incorrect"
   
3. MISSING_INFO: User provides new policy information
   - Examples: "according to circular 2024-05", "the new rule states", "as per latest update"
   
4. NONE: No policy-related claim detected
   - Examples: Regular questions without challenging current information

ANALYSIS INSTRUCTIONS:
- Confidence should be 0.0 to 1.0
- Consider conversation context for contradiction detection
- Be conservative - only flag clear claims, not simple questions
- Provide reasoning for your assessment

Respond in JSON format:
{{
    "is_claim_detected": boolean,
    "claim_type": "policy_outdated" | "contradiction" | "missing_info" | "none",
    "confidence": float (0.0 to 1.0),
    "reasoning": "Brief explanation of why this was classified this way",
    "key_phrases": ["list", "of", "key", "phrases", "that", "triggered", "detection"]
}}"""
        
        return prompt
    
    async def detect_claim(
        self,
        user_message: str,
        conversation_context: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Detect if user message contains a policy change claim
        
        Args:
            user_message: The user's current message
            conversation_context: List of previous messages in conversation
            
        Returns:
            {
                "is_claim_detected": bool,
                "claim_type": str,  # "policy_outdated", "contradiction", "missing_info", "none"
                "confidence": float,
                "reasoning": str,
                "key_phrases": List[str]
            }
        """
        if not self.enabled:
            logger.info("Claim detection disabled (feature flag off)")
            return {
                "is_claim_detected": False,
                "claim_type": "none",
                "confidence": 0.0,
                "reasoning": "Feature disabled",
                "key_phrases": []
            }
        
        if not user_message or not user_message.strip():
            return {
                "is_claim_detected": False,
                "claim_type": "none",
                "confidence": 0.0,
                "reasoning": "Empty message",
                "key_phrases": []
            }
        
        conversation_context = conversation_context or []
        
        try:
            # Build detection prompt
            prompt = self._build_detection_prompt(user_message, conversation_context)
            
            # Call LLM for detection
            if self.llm_client:
                # Use provided LLM client
                response = await self._call_llm(prompt)
                result = self._parse_llm_response(response)
            else:
                # Fallback: Use keyword-based heuristic detection
                result = self._heuristic_detection(user_message)
            
            logger.info(f"Claim detection: {result['claim_type']} (confidence: {result['confidence']})")
            return result
            
        except Exception as e:
            logger.error(f"Error in claim detection: {e}")
            # Return safe default on error
            return {
                "is_claim_detected": False,
                "claim_type": "none",
                "confidence": 0.0,
                "reasoning": f"Detection failed: {str(e)}",
                "key_phrases": []
            }
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM for claim detection (placeholder for actual implementation)"""
        # TODO: Implement actual LLM call using Gemini or OpenAI
        # This is a placeholder that will be implemented when integrating with actual LLM
        
        # For now, return a mock response format
        import json
        return json.dumps({
            "is_claim_detected": False,
            "claim_type": "none",
            "confidence": 0.5,
            "reasoning": "LLM integration pending",
            "key_phrases": []
        })
    
    def _parse_llm_response(self, response: str) -> Dict:
        """Parse LLM JSON response"""
        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.error("Failed to parse LLM response as JSON")
            return {
                "is_claim_detected": False,
                "claim_type": "none",
                "confidence": 0.0,
                "reasoning": "Parse error",
                "key_phrases": []
            }
    
    def _heuristic_detection(self, user_message: str) -> Dict:
        """
        Fallback heuristic-based claim detection without LLM
        Uses keyword matching for basic detection
        """
        message_lower = user_message.lower()
        
        # Define trigger phrases for each claim type
        outdated_triggers = [
            "outdated", "old rule", "changed", "no longer", "not valid",
            "was updated", "modified recently", "different now"
        ]
        
        contradiction_triggers = [
            "but the circular", "actually", "that's incorrect", "that's wrong",
            "not what i heard", "contradicts", "different from"
        ]
        
        missing_info_triggers = [
            "circular", "new rule", "latest update", "according to",
            "as per", "recent announcement", "memo states"
        ]
        
        # Check for matches
        detected_phrases = []
        claim_type = "none"
        confidence = 0.0
        
        # Check outdated
        for trigger in outdated_triggers:
            if trigger in message_lower:
                detected_phrases.append(trigger)
                claim_type = "policy_outdated"
                confidence = max(confidence, 0.6)
        
        # Check contradiction
        for trigger in contradiction_triggers:
            if trigger in message_lower:
                detected_phrases.append(trigger)
                if claim_type == "none":
                    claim_type = "contradiction"
                confidence = max(confidence, 0.65)
        
        # Check missing info
        for trigger in missing_info_triggers:
            if trigger in message_lower:
                detected_phrases.append(trigger)
                if claim_type == "none":
                    claim_type = "missing_info"
                confidence = max(confidence, 0.7)
        
        is_detected = claim_type != "none"
        
        reasoning = f"Heuristic detection: found {len(detected_phrases)} trigger phrases" if is_detected else "No trigger phrases found"
        
        return {
            "is_claim_detected": is_detected,
            "claim_type": claim_type,
            "confidence": confidence,
            "reasoning": reasoning,
            "key_phrases": detected_phrases
        }


# Singleton instance
claim_detection_agent = ClaimDetectionAgent()
