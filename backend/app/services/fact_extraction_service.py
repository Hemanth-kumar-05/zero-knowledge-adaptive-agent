"""
Fact Extraction Service
Extracts factual information about users from conversations using AI
"""

import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
from groq import Groq
from google import genai
import os

logger = logging.getLogger(__name__)


class AIFactExtractor:
    """Extracts user facts from conversations using LLM"""
    
    # Fact categories that can be extracted
    FACT_CATEGORIES = {
        "identity": {
            "description": "User's basic identity information",
            "keys": ["name", "student_id", "email", "year", "semester", "major", "department"],
            "examples": ["I'm Hemanth", "My ID is 22Z225", "I'm in 3rd year", "I study Computer Science"]
        },
        "academic_context": {
            "description": "User's academic information",
            "keys": ["current_courses", "advisor", "project_supervisor", "completed_courses", "cgpa"],
            "examples": ["I'm taking CS301 this semester", "Dr. Smith is my advisor", "I've completed Database course"]
        },
        "concern": {
            "description": "Temporary concerns or worries",
            "keys": ["attendance_concern", "grade_concern", "deadline_concern", "general_concern"],
            "examples": ["I'm worried about attendance", "Concerned about my CA marks", "Confused about withdrawal"]
        }
    }
    
    def __init__(self):
        """Initialize LLM client based on environment configuration"""
        self.llm_provider = os.getenv("LLM_PROVIDER", "groq").lower()
        
        if self.llm_provider == "groq":
            self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            self.model = "llama-3.3-70b-versatile"
            logger.info("🧠 AIFactExtractor initialized with Groq")
        else:
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            self.gemini_model = genai.GenerativeModel("gemini-1.5-flash-8b")
            self.model = "gemini-1.5-flash-8b"
            logger.info("🧠 AIFactExtractor initialized with Gemini")
    
    def _build_extraction_prompt(self, messages: List[Dict], current_message: str) -> str:
        """Build prompt for extracting facts from conversation"""
        
        # Format recent conversation (last 5 messages for context)
        conversation = []
        for msg in messages[-5:]:
            role = "User" if msg.get("role") == "user" else "Assistant"
            content = msg.get("content", "")
            conversation.append(f"{role}: {content}")
        
        conversation.append(f"User: {current_message}")
        conversation_text = "\n".join(conversation)
        
        # Build fact category descriptions
        category_descriptions = []
        for category, info in self.FACT_CATEGORIES.items():
            keys_str = ", ".join(info["keys"])
            examples_str = "; ".join(info["examples"])
            category_descriptions.append(
                f"  - **{category}**: {info['description']}\n"
                f"    Possible keys: {keys_str}\n"
                f"    Examples: {examples_str}"
            )
        
        categories_text = "\n".join(category_descriptions)
        
        prompt = f"""You are an AI assistant that extracts factual information about users from conversations.

**CONVERSATION:**
{conversation_text}

**YOUR TASK:**
Extract ONLY factual information about the USER from this conversation. Focus on the CURRENT message primarily.

**FACT CATEGORIES:**
{categories_text}

**EXTRACTION RULES:**
1. **ONLY extract if explicitly stated by the user**
   - ✓ "I'm Hemanth" → Extract name: Hemanth
   - ✓ "My student ID is 22Z225" → Extract student_id: 22Z225
   - ✓ "I'm taking course1, course2 this semester" → Extract current_courses: ["course1", "course2"]
   - ✗ Do NOT infer or guess information not explicitly stated

2. **Identity facts (permanent):**
   - Name, student ID, email, year, semester, major, department
   - These should persist across sessions
   - High confidence required (>0.85)

3. **Academic context (semi-permanent):**
   - Current courses, advisor, project supervisor, completed courses
   - May change per semester
   - Moderate confidence (>0.75)

4. **Concerns (temporary):**
   - Worries, confusion, specific concerns mentioned
   - Should expire after resolution
   - Lower confidence acceptable (>0.65)

5. **Confidence scoring:**
   - Explicit statements ("I am X") = 0.95 confidence
   - Clear context ("My advisor is Dr. Smith") = 0.85 confidence
   - Implied but clear = 0.75 confidence
   - Any uncertainty = below threshold, don't extract

**RETENTION POLICY:**
- Identity facts: "permanent"
- Academic context: "semester" (auto-expire after semester)
- Concerns: "session" (temporary, session-only)

**OUTPUT FORMAT (JSON only):**
{{
  "facts": [
    {{
      "category": "identity",
      "key": "name",
      "value": "Hemanth",
      "retention": "permanent",
      "confidence": 0.95,
      "explanation": "User explicitly said 'I'm Hemanth'",
      "source": "conversation"
    }},
    {{
      "category": "academic_context",
      "key": "current_courses",
      "value": ["course1", "course2"],
      "retention": "semester",
      "confidence": 0.90,
      "explanation": "User mentioned taking these courses this semester",
      "source": "conversation"
    }}
  ]
}}

**CRITICAL REMINDERS:**
- Only extract facts from THIS conversation
- Don't extract the same fact twice
- Only extract if confidence meets minimum threshold
- If NO facts detected, return: {{"facts": []}}
- Most messages will have NO facts - that's normal
- Better to miss a fact than extract incorrectly

Analyze the conversation and respond with JSON only:"""
        
        return prompt
    
    async def extract_facts(
        self,
        messages: List[Dict],
        current_message: str,
        min_confidence: float = 0.70
    ) -> List[Dict]:
        """
        Extract facts from conversation
        
        Args:
            messages: List of recent conversation messages
            current_message: The current user message
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of extracted facts with metadata
        """
        try:
            logger.info(f"🧠 Extracting facts from conversation")
            
            # Build extraction prompt
            prompt = self._build_extraction_prompt(messages, current_message)
            
            # Call LLM based on provider
            if self.llm_provider == "groq":
                response = self.groq_client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,  # Low temperature for accurate extraction
                    max_tokens=1000
                )
                result_text = response.choices[0].message.content.strip()
            else:
                response = self.gemini_model.generate_content(prompt)
                result_text = response.text.strip()
            
            logger.info(f"🔍 Raw extraction result: {result_text[:200]}...")
            
            # Parse JSON response
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            result = json.loads(result_text)
            facts = result.get("facts", [])
            
            # Filter by confidence threshold
            filtered_facts = [
                fact for fact in facts
                if fact.get("confidence", 0) >= min_confidence
            ]
            
            # Add extraction metadata
            for fact in filtered_facts:
                fact["extracted_at"] = datetime.utcnow()
                fact["extraction_method"] = "llm_analysis"
                fact["llm_provider"] = self.llm_provider
                fact["llm_model"] = self.model
                fact["confirmed_by_user"] = False  # Will be confirmed later
                # Auto-lock only permanent and semester facts, not session
                fact["locked"] = fact.get("retention") in ["permanent", "semester"]
            
            logger.info(f"✅ Extracted {len(filtered_facts)} fact(s)")
            for fact in filtered_facts:
                logger.info(
                    f"  - {fact['category']}.{fact['key']}: {fact['value']} "
                    f"(confidence: {fact['confidence']:.2f}, retention: {fact['retention']})"
                )
            
            return filtered_facts
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response text: {result_text}")
            return []
        except Exception as e:
            logger.error(f"❌ Error extracting facts: {e}", exc_info=True)
            return []
    
    def detect_memory_commands(self, message: str) -> Optional[Dict]:
        """
        Detect explicit memory commands in user message
        
        Commands:
        - "Remember that my advisor is Dr. Smith"
        - "Forget my major"
        - "Don't remember this conversation"
        - "What do you know about me?"
        
        Args:
            message: User message to analyze
            
        Returns:
            Dict with command type and parameters, or None
        """
        message_lower = message.lower().strip()
        
        # Remember command
        if any(phrase in message_lower for phrase in ["remember that", "remember my", "please remember"]):
            return {
                "command": "remember",
                "message": message,
                "requires_extraction": True
            }
        
        # Forget command
        if any(phrase in message_lower for phrase in ["forget my", "forget that", "don't remember", "remove my"]):
            # Try to extract what to forget
            forget_key = None
            for keyword in ["name", "advisor", "major", "courses", "email", "id", "year"]:
                if keyword in message_lower:
                    forget_key = keyword
                    break
            
            return {
                "command": "forget",
                "key": forget_key,
                "message": message
            }
        
        # View memory command
        if any(phrase in message_lower for phrase in ["what do you know about me", "what do you remember", "show my information", "my profile"]):
            return {
                "command": "view_memory",
                "message": message
            }
        
        # Reset memory command
        if any(phrase in message_lower for phrase in ["forget everything", "reset my profile", "delete all my information"]):
            return {
                "command": "reset_memory",
                "message": message
            }
        
        return None
    
    def should_request_confirmation(self, fact: Dict) -> bool:
        """
        Determine if user confirmation is needed for this fact
        
        Args:
            fact: Extracted fact dictionary
            
        Returns:
            True if confirmation required
        """
        # Always confirm identity facts (high importance)
        if fact.get("category") == "identity":
            return True
        
        # Confirm academic context if high confidence
        if fact.get("category") == "academic_context" and fact.get("confidence", 0) >= 0.85:
            return True
        
        # Don't confirm temporary concerns (too intrusive)
        if fact.get("category") == "concern":
            return False
        
        # Confirm if retention is permanent
        if fact.get("retention") == "permanent":
            return True
        
        return False


# Global instance
fact_extractor = AIFactExtractor()
