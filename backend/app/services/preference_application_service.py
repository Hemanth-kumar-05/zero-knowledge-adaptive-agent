"""
Preference Application Service
Applies user preferences to RAG response generation
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class PreferenceApplier:
    """Applies user preferences to customize RAG responses"""
    
    def __init__(self):
        """Initialize preference applier"""
        pass
    
    def build_preference_instructions(self, preferences: List[Dict]) -> str:
        """
        Convert user preferences into instruction text for LLM
        
        Args:
            preferences: List of user preference objects
            
        Returns:
            Formatted instruction string
        """
        if not preferences:
            return ""
        
        # Separate custom (freeform) and categorized preferences
        custom_prefs = []
        pref_by_category = {}
        
        for pref in preferences:
            category = pref.get("category", "")
            value = pref.get("value", "")
            confidence = pref.get("confidence", 0)
            locked = pref.get("locked", False)
            custom_instruction = pref.get("custom_instruction")
            
            # CRITICAL: Only apply LOCKED preferences
            # Unlocked preferences are just tracked, not enforced
            if not locked:
                continue
            
            # Locked preferences are user-confirmed, so apply regardless of confidence
            # (User manually locked them, so we trust the preference)
            
            # If has custom instruction, treat as freeform
            if custom_instruction:
                custom_prefs.append(custom_instruction)
                continue
            
            # Otherwise, categorize it
            if category not in pref_by_category:
                pref_by_category[category] = []
            
            pref_by_category[category].append({
                "value": value,
                "confidence": confidence,
                "locked": locked
            })
        
        if not pref_by_category and not custom_prefs:
            return ""
        
        # Build instruction text
        instructions = ["**CRITICAL USER PREFERENCES - MUST FOLLOW EXACTLY:**"]
        
        # Add custom freeform preferences first
        if custom_prefs:
            instructions.append("")
            instructions.append("**CUSTOM USER INSTRUCTIONS:**")
            for custom in custom_prefs:
                instructions.append(f"- {custom}")
            instructions.append("")
        
        # Communication Style
        if "communication_style" in pref_by_category:
            styles = pref_by_category["communication_style"]
            top_style = max(styles, key=lambda x: x["confidence"])
            style_map = {
                "concise": "CONCISE MODE: Give ONLY the essential answer. No elaboration unless asked. Maximum 2-3 sentences or bullet points. NO descriptions unless explicitly needed.",
                "detailed": "DETAILED MODE: Provide thorough explanations with context, background, and implications. Include all relevant details.",
                "bullet_points": "BULLET POINT MODE: Format ALL answers as bullet points. NO paragraphs. Each point should be one clear statement.",
                "conversational": "CONVERSATIONAL MODE: Write naturally as if speaking to a friend. Use contractions and casual phrasing.",
                "step_by_step": "STEP-BY-STEP MODE: Break every answer into numbered steps. Each step must be clear and actionable."
            }
            if top_style["value"] in style_map:
                instructions.append(f"- {style_map[top_style['value']]}")
        
        # Detail Level
        if "detail_level" in pref_by_category:
            levels = pref_by_category["detail_level"]
            top_level = max(levels, key=lambda x: x["confidence"])
            level_map = {
                "brief": "BRIEF MODE: ONE sentence per point. NO explanations. Just the core facts. Think Twitter-length responses.",
                "moderate": "MODERATE MODE: Balance brevity with clarity. 1-2 sentences per point. Only essential context.",
                "comprehensive": "COMPREHENSIVE MODE: Include full context, explanations, and relevant background for each point.",
                "exhaustive": "EXHAUSTIVE MODE: Cover EVERYTHING. Include all details, edge cases, exceptions, and related information."
            }
            if top_level["value"] in level_map:
                instructions.append(f"- {level_map[top_level['value']]}")
        
        # Tone
        if "tone" in pref_by_category:
            tones = pref_by_category["tone"]
            top_tone = max(tones, key=lambda x: x["confidence"])
            tone_map = {
                "formal": "FORMAL TONE: Use complete sentences, proper grammar, no contractions. Professional language only.",
                "friendly": "FRIENDLY TONE: Be warm and approachable. Use 'you' and 'I'. Casual but respectful.",
                "professional": "PROFESSIONAL TONE: Clear, respectful, and competent. Balance formality with accessibility.",
                "casual": "CASUAL TONE: Relax the language. Use contractions, everyday words. Like talking to a classmate.",
                "academic": "ACADEMIC TONE: Use precise terminology. Formal structure. Citation-ready language."
            }
            if top_tone["value"] in tone_map:
                instructions.append(f"- {tone_map[top_tone['value']]}")
        
        # Example Preference
        if "example_preference" in pref_by_category:
            examples = pref_by_category["example_preference"]
            top_example = max(examples, key=lambda x: x["confidence"])
            example_map = {
                "with_examples": "EXAMPLES REQUIRED: Always include at least one concrete example for each concept.",
                "without_examples": "NO EXAMPLES: Skip examples entirely. Concepts and definitions only.",
                "minimal_examples": "MINIMAL EXAMPLES: One example only if absolutely necessary for clarity.",
                "many_examples": "MULTIPLE EXAMPLES: Provide 2-3 different examples for each major point."
            }
            if top_example["value"] in example_map:
                instructions.append(f"- {example_map[top_example['value']]}")
        
        # Technical Level
        if "technical_level" in pref_by_category:
            levels = pref_by_category["technical_level"]
            top_level = max(levels, key=lambda x: x["confidence"])
            tech_map = {
                "beginner": "BEGINNER LEVEL: Explain like to someone new. Avoid jargon. Define any technical terms used.",
                "intermediate": "INTERMEDIATE LEVEL: Use standard terms but explain complex concepts. Assume basic knowledge.",
                "advanced": "ADVANCED LEVEL: Use technical terminology freely. Assume strong background knowledge.",
                "expert": "Use specialized terminology without basic explanations"
            }
            if top_level["value"] in tech_map:
                instructions.append(f"- {tech_map[top_level['value']]}")
        
        # Response Format
        if "response_format" in pref_by_category:
            formats = pref_by_category["response_format"]
            top_format = max(formats, key=lambda x: x["confidence"])
            format_map = {
                "paragraphs": "PARAGRAPH FORMAT: Write in flowing paragraphs. No bullet points.",
                "lists": "LIST FORMAT: Use bullet points or numbered lists. NO paragraphs.",
                "mixed": "MIXED FORMAT: Combine paragraphs and lists as needed for clarity.",
                "tables": "TABLE FORMAT: Present information in table format when showing structured data.",
                "structured": "STRUCTURED FORMAT: Use clear headings, sections, and organization."
            }
            if top_format["value"] in format_map:
                instructions.append(f"- {format_map[top_format['value']]}")
        
        # Check if we have any instructions beyond the header
        if len(instructions) == 1 and not custom_prefs:
            return ""  # Only header, no actual instructions
        
        # Add critical reminder
        instructions.append("")
        instructions.append("**THESE PREFERENCES ARE MANDATORY. They override default behavior. Follow them EXACTLY.**")
        
        logger.info(f"📝 Built preference instructions with {len(pref_by_category)} categories + {len(custom_prefs)} custom")
        return "\n".join(instructions)
    
    def get_applied_preferences_metadata(self, preferences: List[Dict]) -> List[Dict]:
        """
        Extract metadata about which preferences were applied
        
        Args:
            preferences: List of preference objects
            
        Returns:
            List of applied preference metadata
        """
        applied = []
        
        for pref in preferences:
            if pref.get("confidence", 0) >= 0.6:
                applied.append({
                    "category": pref.get("category"),
                    "value": pref.get("value"),
                    "confidence": pref.get("confidence"),
                    "locked": pref.get("locked", False)
                })
        
        return applied
    
    def should_apply_preferences(
        self,
        preferences: List[Dict],
        min_confidence: float = 0.6
    ) -> bool:
        """
        Determine if preferences should be applied to response
        
        Args:
            preferences: User's preference list
            min_confidence: Minimum confidence threshold
            
        Returns:
            True if preferences should be applied
        """
        if not preferences:
            return False
        
        # Check if there are any high-confidence preferences
        high_confidence_prefs = [
            p for p in preferences
            if p.get("confidence", 0) >= min_confidence
        ]
        
        return len(high_confidence_prefs) > 0


# Global instance
preference_applier = PreferenceApplier()
