"""
AI Preference Extraction Service
Automatically extracts user preferences from conversation messages
"""

import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
from groq import Groq
from google import genai
import os

logger = logging.getLogger(__name__)


class AIPreferenceExtractor:
    """Extracts user preferences from conversations using LLM"""
    
    # Preference categories that can be extracted
    PREFERENCE_CATEGORIES = {
        "communication_style": {
            "description": "How user prefers responses (concise, detailed, bullet points, conversational)",
            "values": ["concise", "detailed", "bullet_points", "conversational", "step_by_step"]
        },
        "detail_level": {
            "description": "Depth of information user prefers",
            "values": ["brief", "moderate", "comprehensive", "exhaustive"]
        },
        "tone": {
            "description": "Preferred tone of responses",
            "values": ["formal", "friendly", "professional", "casual", "academic"]
        },
        "example_preference": {
            "description": "User's preference for examples",
            "values": ["with_examples", "without_examples", "minimal_examples", "many_examples"]
        },
        "technical_level": {
            "description": "Technical depth user can handle",
            "values": ["beginner", "intermediate", "advanced", "expert"]
        },
        "response_format": {
            "description": "Preferred response structure",
            "values": ["paragraphs", "lists", "mixed", "tables", "structured"]
        }
    }
    
    def __init__(self):
        """Initialize LLM client based on environment configuration"""
        self.llm_provider = os.getenv("LLM_PROVIDER", "groq").lower()
        
        if self.llm_provider == "groq":
            self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            self.model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
            logger.info("🤖 AIPreferenceExtractor initialized with Groq")
        else:
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            self.gemini_model = genai.GenerativeModel("gemini-1.5-flash-8b")
            self.model = "gemini-1.5-flash-8b"
            logger.info("🤖 AIPreferenceExtractor initialized with Gemini")
    
    def _build_extraction_prompt(self, messages: List[Dict]) -> str:
        """
        Build prompt for extracting preferences from conversation
        
        Args:
            messages: List of user and assistant messages
            
        Returns:
            Formatted prompt string
        """
        # Format conversation history - ONLY USER MESSAGES
        user_messages = []
        for msg in messages:
            if msg["role"] == "user":
                user_messages.append(f"User: {msg['content']}")
        
        if not user_messages:
            return ""
        
        # Focus on the LAST user message
        last_message = user_messages[-1]
        prev_context = "\n".join(user_messages[:-1]) if len(user_messages) > 1 else "No previous context"
        
        # Build category descriptions
        category_descriptions = []
        for category, info in self.PREFERENCE_CATEGORIES.items():
            values_str = ", ".join(info["values"])
            category_descriptions.append(
                f"  - {category}: {info['description']} (possible values: {values_str})"
            )
        
        categories_text = "\n".join(category_descriptions)
        
        prompt = f"""You are an EXTREMELY STRICT preference analyzer. Only extract preferences from USER statements, NEVER from assistant responses.

**CRITICAL RULES:**
1. ONLY analyze the LAST USER message shown below
2. NEVER extract preferences from what the assistant said
3. 95% of messages have NO preferences - that's NORMAL
4. Only extract if user EXPLICITLY says "I prefer", "I want", "Please always", "From now on"
5. IGNORE one-time requests, acknowledgments, or normal questions
6. Match preferences to the valid categories below - if it doesn't fit, DON'T extract

**Previous Context (for reference only):**
{prev_context}

**LAST USER MESSAGE (analyze THIS ONLY):**
{last_message}

**Valid Preference Categories:**
{categories_text}

**When to Extract:**
✓ "I prefer brief/detailed/concise answers"
✓ "Please always include/exclude examples"  
✓ "I want formal/casual tone from now on"
✓ "Keep responses short" or "Give me comprehensive explanations"

**When NOT to Extract:**
✗ Normal questions ("What's the deadline?")
✗ Acknowledgments ("Got it", "Thanks", "OK")
✗ One-time requests ("Can you explain this briefly?")
✗ Assistant statements ("I'll keep it brief") - NEVER EXTRACT THESE

**Output JSON Format:**
{{
  "preferences": [
    {{
      "category": "detail_level",
      "value": "comprehensive",
      "confidence": 0.95,
      "explanation": "User explicitly said 'I prefer comprehensive answers' in this message",
      "source": "conversation_analysis"
    }}
  ]
}}

**REMINDER:**
- 95% of messages will have NO preferences - that's NORMAL
- Return {{"preferences": []}} unless the CURRENT message explicitly states a preference
- Do NOT extract the same preference twice
- Better to miss a preference than extract incorrectly

Analyze ONLY the current message with EXTREME STRICTNESS and respond with JSON only:"""
        
        return prompt
    
    async def extract_preferences(
        self, 
        messages: List[Dict],
        min_confidence: float = 0.75  # Increased from 0.6 to 0.75 for stricter extraction
    ) -> List[Dict]:
        """
        Extract preferences from conversation messages
        
        Args:
            messages: List of conversation messages with 'role' and 'content'
            min_confidence: Minimum confidence threshold (0.0-1.0)
            
        Returns:
            List of extracted preferences with metadata
        """
        try:
            # Need at least 2 messages (user + assistant) to detect patterns
            if len(messages) < 2:
                logger.info("📊 Not enough messages for preference extraction")
                return []
            
            logger.info(f"📊 Extracting preferences from {len(messages)} messages")
            
            # Build extraction prompt
            prompt = self._build_extraction_prompt(messages)
            
            # Call LLM based on provider
            if self.llm_provider == "groq":
                response = self.groq_client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,  # Low temperature for consistent extraction
                    max_tokens=1000
                )
                result_text = response.choices[0].message.content.strip()
            else:
                response = self.gemini_model.generate_content(prompt)
                result_text = response.text.strip()
            
            logger.info(f"🔍 Raw extraction result: {result_text[:200]}...")
            
            # Parse JSON response
            # Clean up any markdown code blocks
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            result = json.loads(result_text)
            preferences = result.get("preferences", [])
            
            # Filter by confidence threshold
            filtered_preferences = [
                pref for pref in preferences 
                if pref.get("confidence", 0) >= min_confidence
            ]
            
            # Add extraction metadata
            for pref in filtered_preferences:
                pref["extracted_at"] = datetime.utcnow()
                pref["extraction_method"] = "llm_analysis"
                pref["llm_provider"] = self.llm_provider
                pref["llm_model"] = self.model
                pref["locked"] = True  # Auto-lock preferences learned from conversation
            
            logger.info(f"✅ Extracted {len(filtered_preferences)} preferences (min confidence: {min_confidence})")
            for pref in filtered_preferences:
                logger.info(
                    f"  - {pref['category']}: {pref['value']} "
                    f"(confidence: {pref['confidence']:.2f})"
                )
            
            return filtered_preferences
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response text: {result_text}")
            return []
        except Exception as e:
            logger.error(f"❌ Error extracting preferences: {e}", exc_info=True)
            return []
    
    def merge_preferences(
        self,
        existing_preferences: List[Dict],
        new_preferences: List[Dict],
        max_preferences: int = 50
    ) -> List[Dict]:
        """
        Merge new extracted preferences with existing ones
        
        Args:
            existing_preferences: Current user preferences
            new_preferences: Newly extracted preferences
            max_preferences: Maximum number of preferences to keep
            
        Returns:
            Merged preferences list with updated confidence scores
        """
        # Create dict for easy lookup
        prefs_dict = {}
        
        # Add existing preferences
        for pref in existing_preferences:
            key = pref["key"]
            prefs_dict[key] = pref
        
        # Process new preferences
        for new_pref in new_preferences:
            key = f"{new_pref['category']}:{new_pref['value']}"
            
            if key in prefs_dict:
                # Update existing preference
                existing = prefs_dict[key]
                
                # Don't update if locked
                if existing.get("locked", False):
                    logger.info(f"🔒 Skipping locked preference: {key}")
                    continue
                
                # Boost confidence if detected again
                old_confidence = existing.get("confidence", 0.5)
                new_confidence = new_pref["confidence"]
                
                # Weighted average favoring new evidence
                updated_confidence = min(
                    (old_confidence * 0.4 + new_confidence * 0.6),
                    0.99  # Cap at 0.99
                )
                
                existing["confidence"] = round(updated_confidence, 2)
                existing["last_updated"] = datetime.utcnow()
                existing["update_count"] = existing.get("update_count", 0) + 1
                existing["last_extracted_at"] = new_pref["extracted_at"]
                
                logger.info(
                    f"🔄 Updated preference {key}: "
                    f"{old_confidence:.2f} → {updated_confidence:.2f}"
                )
            else:
                # Add new preference
                prefs_dict[key] = {
                    "key": key,
                    "category": new_pref["category"],
                    "value": new_pref["value"],
                    "confidence": new_pref["confidence"],
                    "source": new_pref.get("source", "extracted"),
                    "created_at": new_pref["extracted_at"],
                    "last_updated": new_pref["extracted_at"],
                    "locked": new_pref.get("locked", True),  # Respect the locked status from extraction
                    "update_count": 0,
                    "explanation": new_pref.get("explanation", ""),
                    "llm_provider": new_pref.get("llm_provider", ""),
                    "llm_model": new_pref.get("llm_model", "")
                }
                
                logger.info(
                    f"➕ Added new preference: {key} "
                    f"(confidence: {new_pref['confidence']:.2f})"
                )
        
        # Convert back to list and sort by confidence (descending)
        merged_preferences = list(prefs_dict.values())
        merged_preferences.sort(key=lambda x: x["confidence"], reverse=True)
        
        # Enforce max preferences limit
        if len(merged_preferences) > max_preferences:
            logger.warning(
                f"⚠️ Preference limit exceeded ({len(merged_preferences)} > {max_preferences}), "
                f"removing lowest confidence preferences"
            )
            merged_preferences = merged_preferences[:max_preferences]
        
        return merged_preferences
    
    def should_extract_preferences(
        self,
        user_data: Dict,
        current_session_messages: int,
        last_user_message: str = None
    ) -> bool:
        """
        Determine if preferences should be extracted for this interaction
        Requires minimum 4 messages and filters out very short responses
        
        Args:
            user_data: User document from database
            current_session_messages: Number of messages in current session
            last_user_message: Content of the last user message
            
        Returns:
            True if extraction should be performed
        """
        # Check if extraction is disabled by user
        metadata = user_data.get("personalization_metadata", {})
        if metadata.get("auto_extract_disabled", False):
            return False
        
        # Require at least 4 messages (2 exchanges) for better context
        if current_session_messages < 4:
            return False
        
        # Filter out very short user messages (less than 10 characters)
        # These are likely just acknowledgments like "ok", "thanks", etc.
        if last_user_message and len(last_user_message.strip()) < 10:
            logger.info(
                f"⏭️  Skipping extraction - message too short ({len(last_user_message)} chars)"
            )
            return False
        
        # Extract every 2 user messages (4 messages total = 2 exchanges)
        # This gives better signal while not over-extracting
        if current_session_messages % 4 == 0:
            logger.info(
                f"✅ Extraction triggered (message {current_session_messages})"
            )
            return True
        
        return False
    
    def detect_conflicts(
        self,
        existing_preferences: List[Dict],
        new_preference: Dict
    ) -> Optional[Dict]:
        """
        Detect if a new preference conflicts with existing ones
        
        Args:
            existing_preferences: List of current user preferences
            new_preference: New preference to check
            
        Returns:
            Conflicting preference dict if found, None otherwise
        """
        new_category = new_preference.get("category")
        new_value = new_preference.get("value", "").lower()
        
        # Define opposing values for each category
        conflicts = {
            "communication_style": {
                "concise": ["detailed", "comprehensive"],
                "detailed": ["concise", "brief"],
                "conversational": ["formal", "professional"],
                "formal": ["casual", "conversational"]
            },
            "detail_level": {
                "brief": ["comprehensive", "exhaustive", "detailed"],
                "moderate": ["brief", "exhaustive"],
                "comprehensive": ["brief", "concise"],
                "exhaustive": ["brief", "concise", "moderate"]
            },
            "tone": {
                "formal": ["casual", "friendly"],
                "casual": ["formal", "professional"],
                "friendly": ["formal"],
                "professional": ["casual"]
            }
        }
        
        # Check existing preferences in the same category
        for existing in existing_preferences:
            if existing.get("category") == new_category:
                existing_value = existing.get("value", "").lower()
                
                # Check if values are different
                if existing_value != new_value:
                    # Check if they're explicitly conflicting
                    category_conflicts = conflicts.get(new_category, {})
                    conflicting_values = category_conflicts.get(new_value, [])
                    
                    if existing_value in conflicting_values:
                        logger.warning(
                            f"⚠️  Conflict detected: {new_category}.{new_value} "
                            f"conflicts with existing {existing_value}"
                        )
                        return existing
                    
                    # Even if not explicitly defined as conflicting,
                    # different values in same category might be conflicts
                    logger.info(
                        f"ℹ️  Possible conflict: {new_category} has both "
                        f"{existing_value} and {new_value}"
                    )
                    return existing
        
        return None
    
    async def extract_from_text(
        self,
        text: str,
        user_id: str = None,
        min_confidence: float = 0.6
    ) -> Dict:
        """
        Extract preferences from a single natural language text input
        (for manual preference input by users)
        
        Args:
            text: Natural language preference description
            user_id: Optional user ID for logging
            min_confidence: Minimum confidence threshold
            
        Returns:
            Dict with extracted preferences
        """
        try:
            logger.info(f"📝 Extracting preferences from manual text input (user: {user_id})")
            
            # Build category descriptions
            category_descriptions = []
            for category, info in self.PREFERENCE_CATEGORIES.items():
                values_str = ", ".join(info["values"])
                category_descriptions.append(
                    f"  - {category}: {info['description']} (possible values: {values_str})"
                )
            
            categories_text = "\n".join(category_descriptions)
            
            prompt = f"""You are an expert at parsing user preferences from natural language.

The user has provided the following preference statement:
"{text}"

**Preference Categories:**
{categories_text}

**Instructions:**
1. Parse the user's statement and identify which preferences they're expressing
2. Match each preference to the appropriate category
3. Choose the most appropriate value from the allowed values for each category
4. Provide a confidence score (0.6-1.0) for each preference
5. Include an explanation that quotes or paraphrases the relevant part of the user's statement

**Output Format (JSON only, no additional text):**
{{
  "preferences": [
    {{
      "category": "communication_style",
      "value": "detailed",
      "confidence": 0.90,
      "explanation": "User stated: 'I prefer detailed explanations'",
      "source": "manual_input"
    }}
  ]
}}

**Important:**
- Return ONLY valid JSON
- Extract ALL preferences mentioned in the statement
- If no clear preferences, return {{"preferences": []}}
- Confidence should be high (0.8+) for explicitly stated preferences

Analyze and respond with JSON only:"""
            
            # Call LLM based on provider
            if self.llm_provider == "groq":
                response = self.groq_client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,  # Very low temperature for consistent parsing
                    max_tokens=800
                )
                result_text = response.choices[0].message.content.strip()
            else:
                response = self.gemini_model.generate_content(prompt)
                result_text = response.text.strip()
            
            logger.info(f"🔍 Manual extraction result: {result_text[:200]}...")
            
            # Clean up markdown code blocks if present
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            result = json.loads(result_text)
            preferences = result.get("preferences", [])
            
            # Filter by confidence threshold
            filtered_preferences = [
                pref for pref in preferences 
                if pref.get("confidence", 0) >= min_confidence
            ]
            
            # Add extraction metadata
            for pref in filtered_preferences:
                pref["extracted_at"] = datetime.utcnow()
                pref["extraction_method"] = "manual_text_input"
                pref["llm_provider"] = self.llm_provider
                pref["llm_model"] = self.model
                pref["locked"] = True  # Auto-lock manually stated preferences
            
            logger.info(f"✅ Extracted {len(filtered_preferences)} preferences from manual input")
            
            return {"preferences": filtered_preferences}
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse LLM response as JSON: {e}")
            logger.error(f"Raw response: {result_text}")
            return {"preferences": []}
        except Exception as e:
            logger.error(f"❌ Error in extract_from_text: {str(e)}", exc_info=True)
            return {"preferences": []}

