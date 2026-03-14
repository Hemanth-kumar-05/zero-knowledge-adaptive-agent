"""
Risk Prediction Service
Analyzes conversation patterns to detect potential academic risks using AI
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import logging
from groq import Groq
from google import genai
import os

logger = logging.getLogger(__name__)


class RiskAlert:
    """Represents a detected risk alert"""
    
    def __init__(
        self,
        risk_type: str,
        severity: str,
        confidence: float,
        message: str,
        indicators: List[str],
        detected_at: datetime
    ):
        self.risk_type = risk_type  # 'attendance', 'deadline', 'policy_confusion'
        self.severity = severity  # 'low', 'medium', 'high'
        self.confidence = confidence  # 0.0 to 1.0
        self.message = message
        self.indicators = indicators
        self.detected_at = detected_at
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API response"""
        return {
            "risk_type": self.risk_type,
            "severity": self.severity,
            "confidence": self.confidence,
            "message": self.message,
            "indicators": self.indicators,
            "detected_at": self.detected_at.isoformat()
        }


class RiskPredictor:
    """Main risk prediction engine using AI"""
    
    # Risk types we can detect
    RISK_TYPES = {
        "attendance": {
            "description": "Concerns about attendance requirements, eligibility, or shortages",
            "examples": ["multiple questions about 75% attendance", "worried about attendance shortage", "asking about medical leave"]
        },
        "deadline": {
            "description": "Concerns about missed deadlines, late submissions, or time-sensitive requirements",
            "examples": ["asking about registration deadlines repeatedly", "worried about missing exam registration", "asking about extensions"]
        },
        "policy_confusion": {
            "description": "Repeated questions about the same policy or explicit confusion",
            "examples": ["asking the same question multiple times", "explicitly saying 'I don't understand'", "asking for clarification repeatedly"]
        }
    }
    
    def __init__(self):
        """Initialize LLM client based on environment configuration"""
        self.time_window_days = 7  # Analyze last 7 days
        self.llm_provider = os.getenv("LLM_PROVIDER", "groq").lower()
        
        if self.llm_provider == "groq":
            self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            self.model = "llama-3.1-8b-instant"
            logger.info("🚨 RiskPredictor initialized with Groq")
        else:
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            self.gemini_model = genai.GenerativeModel("gemini-1.5-flash-8b")
            self.model = "gemini-1.5-flash-8b"
            logger.info("🚨 RiskPredictor initialized with Gemini")
    
    def _build_risk_analysis_prompt(self, messages: List[Dict], current_question: str) -> str:
        """Build prompt for AI-based risk analysis"""
        
        # Format conversation history
        conversation = []
        for msg in messages[-10:]:  # Last 10 messages for context
            role = "User" if msg.get("role") == "user" else "Assistant"
            content = msg.get("content", "")
            conversation.append(f"{role}: {content}")
        
        conversation.append(f"User: {current_question}")
        conversation_text = "\n".join(conversation)
        
        # Build risk type descriptions
        risk_descriptions = []
        for risk_type, info in self.RISK_TYPES.items():
            examples_str = ", ".join(info["examples"])
            risk_descriptions.append(
                f"  - **{risk_type}**: {info['description']}\n    Examples: {examples_str}"
            )
        
        risks_text = "\n".join(risk_descriptions)
        
        prompt = f"""You are an AI academic advisor analyzing student conversation patterns for potential risks.

**CONVERSATION HISTORY (recent messages):**
{conversation_text}

**YOUR TASK:**
Analyze the ENTIRE conversation history to detect patterns indicating academic risks. Consider:
1. **Frequency**: How many times has the user asked about the same/similar topic?
2. **Urgency**: Are there signs of stress, worry, or time pressure?
3. **Confusion**: Is the user asking the same question repeatedly or expressing confusion?
4. **Context**: What does the pattern suggest about the student's situation?

**RISK TYPES TO DETECT:**
{risks_text}

**SEVERITY LEVELS:**
- **low**: 1-2 mentions, general inquiry, no urgency
- **medium**: 3-4 mentions, some concern, or confusion indicators
- **high**: 5+ mentions, urgent language, repeated questions, or clear panic  

**CRITICAL RULES:**
- Look at the ENTIRE conversation history for patterns
- Consider frequency, urgency, and confusion together
- A single question is usually NOT a risk (unless highly urgent)
- Repeated questions about the same topic = higher risk
- Explicit confusion signals ("I don't understand") = policy_confusion risk
- Only return risks with confidence >= 0.60
- It's okay to return NO risks if patterns don't indicate problems

**OUTPUT FORMAT (JSON only):**
{{
  "risks": [
    {{
      "risk_type": "attendance",
      "severity": "medium",
      "confidence": 0.75,
      "message": "You've asked about attendance policies 3 times. Based on the 75% requirement, you may be at risk. Consider checking your current attendance and meeting with your advisor.",
      "indicators": ["multiple attendance questions", "concern about eligibility"],
      "explanation": "User asked about attendance 3 times in conversation, suggesting genuine concern"
    }}
  ]
}}

**IMPORTANT:**
- If NO risks detected, return: {{"risks": []}}
- Craft helpful, actionable messages for students
- Be concise but empathetic
- Focus on genuine patterns, not one-off questions

Analyze the conversation and respond with JSON only:"""
        
        return prompt
    
    async def analyze_risks(
        self,
        conversation_history: List[Dict],
        current_question: str
    ) -> List[RiskAlert]:
        """
        Analyze conversation patterns using AI to detect risks
        
        Args:
            conversation_history: List of messages from the session
            current_question: The current user question
            
        Returns:
            List of detected risk alerts
        """
        try:
            # Need reasonable conversation history to detect patterns
            if len(conversation_history) < 1:
                logger.info("📊 Not enough conversation history for risk analysis")
                return []
            
            # Filter recent user messages (within time window)
            recent_messages = self._filter_recent_messages(conversation_history)
            
            if len(recent_messages) < 1:
                logger.info("📊 No recent messages within time window")
                return []
            
            logger.info(f"🚨 Analyzing risks from {len(recent_messages)} recent messages")
            
            # Build risk analysis prompt
            prompt = self._build_risk_analysis_prompt(recent_messages, current_question)
            
            # Call LLM based on provider
            if self.llm_provider == "groq":
                response = self.groq_client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4,  # Moderate temperature for consistent but nuanced analysis
                    max_tokens=1500
                )
                result_text = response.choices[0].message.content.strip()
            else:
                response = self.gemini_model.generate_content(prompt)
                result_text = response.text.strip()
            
            logger.info(f"🔍 Raw risk analysis result: {result_text[:200]}...")
            
            # Parse JSON response
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            result = json.loads(result_text)
            risks_data = result.get("risks", [])
            
            # Convert to RiskAlert objects
            alerts = []
            for risk in risks_data:
                if risk.get("confidence", 0) >= 0.60:  # Minimum confidence threshold
                    alert = RiskAlert(
                        risk_type=risk.get("risk_type"),
                        severity=risk.get("severity"),
                        confidence=risk.get("confidence"),
                        message=risk.get("message"),
                        indicators=risk.get("indicators", []),
                        detected_at=datetime.utcnow()
                    )
                    alerts.append(alert)
            
            logger.info(f"✅ Detected {len(alerts)} risk(s)")
            for alert in alerts:
                logger.info(
                    f"  - {alert.risk_type} ({alert.severity}): "
                    f"confidence={alert.confidence:.2f}"
                )
            
            return alerts
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response text: {result_text}")
            return []
        except Exception as e:
            logger.error(f"❌ Error analyzing risks: {e}", exc_info=True)
            return []
    
    def _filter_recent_messages(self, messages: List[Dict]) -> List[Dict]:
        """Filter messages within the time window"""
        cutoff_time = datetime.utcnow() - timedelta(days=self.time_window_days)
        recent = []
        
        for msg in messages:
            created_at = msg.get("created_at")
            if isinstance(created_at, datetime):
                if created_at >= cutoff_time:
                    recent.append(msg)
            else:
                # If no timestamp, include it (backwards compatibility)
                recent.append(msg)
        
        return recent


# Global instance
risk_predictor = RiskPredictor()
