"""
Smart conversation context builder for history-aware responses.
Uses a hybrid approach: recent messages verbatim + summarized older context.
"""

from typing import List, Dict, Any
from datetime import datetime


class ConversationContextBuilder:
    """Builds optimized conversation context for LLM prompts."""
    
    # Configuration
    MAX_RECENT_MESSAGES = 8  # Keep last N messages verbatim
    MAX_TOTAL_MESSAGES = 50   # Maximum messages to consider
    SUMMARY_THRESHOLD = 10    # Summarize if more than this many messages
    
    def __init__(self, openai_client):
        """Initialize with OpenAI client for summarization."""
        self.openai_client = openai_client
    
    def build_context(self, messages: List[Dict[str, Any]], current_query: str) -> List[Dict[str, str]]:
        """
        Build smart context from conversation history.
        
        Args:
            messages: List of message dicts with 'role', 'content', 'timestamp'
            current_query: The current user query
            
        Returns:
            List of formatted messages for OpenAI API
        """
        if not messages:
            print("  ⚠️  No conversation history found")
            return []
        
        # Limit total messages to consider
        messages = messages[-self.MAX_TOTAL_MESSAGES:]
        
        total_messages = len(messages)
        print(f"\n🧠 HYBRID CONTEXT BUILDER")
        print(f"  Total messages: {total_messages}")
        
        # If few messages, return all verbatim
        if total_messages <= self.MAX_RECENT_MESSAGES:
            print(f"  Strategy: ALL VERBATIM (≤{self.MAX_RECENT_MESSAGES} messages)")
            return self._format_messages(messages)
        
        # Split into old (to summarize) and recent (keep verbatim)
        old_messages = messages[:-self.MAX_RECENT_MESSAGES]
        recent_messages = messages[-self.MAX_RECENT_MESSAGES:]
        
        print(f"  Strategy: HYBRID APPROACH")
        print(f"    - Old messages (to summarize): {len(old_messages)}")
        print(f"    - Recent messages (verbatim): {len(recent_messages)}")
        
        # Build context with summary
        context = []
        
        # Add summarized context if we have old messages
        if len(old_messages) >= 3:  # Only summarize if meaningful amount
            print(f"  📝 Summarizing {len(old_messages)} older messages...")
            summary = self._summarize_conversation(old_messages)
            if summary:
                print(f"  ✅ Summary created: {len(summary)} chars")
                print(f"  Summary preview: {summary[:100]}...")
                context.append({
                    "role": "system",
                    "content": f"Previous conversation context:\n{summary}"
                })
        
        # Add recent messages verbatim
        context.extend(self._format_messages(recent_messages))
        print(f"  ✅ Context built: {len(context)} entries")
        
        return context
    
    def _format_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Format messages for OpenAI API."""
        formatted = []
        for msg in messages:
            formatted.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        return formatted
    
    def _summarize_conversation(self, messages: List[Dict[str, Any]]) -> str:
        """
        Summarize older conversation messages into concise context.
        Uses extractive summarization - key facts and topics.
        """
        try:
            # Build conversation text
            conversation_text = self._build_conversation_text(messages)
            
            # Create summarization prompt
            summary_prompt = f"""Summarize this conversation into a concise context summary (2-4 sentences).
Focus on: key topics discussed, important facts mentioned, user preferences/needs, and any ongoing context.
Be extremely concise but preserve critical information.

Conversation:
{conversation_text}

Summary:"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",  # Use faster model for summarization
                messages=[{"role": "user", "content": summary_prompt}],
                max_tokens=150,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            # Fallback: create simple summary without LLM
            return self._create_simple_summary(messages)
    
    def _build_conversation_text(self, messages: List[Dict[str, Any]]) -> str:
        """Build readable conversation text from messages."""
        lines = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prefix = "User: " if role == "user" else "Assistant: "
            lines.append(f"{prefix}{content}")
        return "\n".join(lines)
    
    def _create_simple_summary(self, messages: List[Dict[str, Any]]) -> str:
        """Create simple summary without LLM (fallback)."""
        user_messages = [m for m in messages if m.get("role") == "user"]
        assistant_messages = [m for m in messages if m.get("role") == "assistant"]
        
        summary_parts = [
            f"Earlier in the conversation ({len(messages)} messages):",
            f"User asked {len(user_messages)} questions about academic topics.",
        ]
        
        # Extract key terms (simple approach)
        all_text = " ".join([m.get("content", "") for m in user_messages[:3]])
        if len(all_text) > 100:
            summary_parts.append(f"Topics included: {all_text[:100]}...")
        
        return " ".join(summary_parts)
    
    def build_system_context(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build metadata context for analytics and tracking.
        
        Returns:
            Dict with conversation statistics and metadata
        """
        if not messages:
            return {
                "total_messages": 0,
                "user_messages": 0,
                "assistant_messages": 0,
                "conversation_started": None,
                "last_message_time": None
            }
        
        user_msgs = [m for m in messages if m.get("role") == "user"]
        assistant_msgs = [m for m in messages if m.get("role") == "assistant"]
        
        timestamps = [m.get("timestamp") for m in messages if m.get("timestamp")]
        
        return {
            "total_messages": len(messages),
            "user_messages": len(user_msgs),
            "assistant_messages": len(assistant_msgs),
            "conversation_started": min(timestamps) if timestamps else None,
            "last_message_time": max(timestamps) if timestamps else None,
            "has_context": len(messages) > 1
        }


class TokenBudgetManager:
    """Manages token budgets for context windows."""
    
    # Approximate token limits
    GPT4_CONTEXT_WINDOW = 128000
    GPT35_CONTEXT_WINDOW = 16000
    
    # Reserved tokens
    RESPONSE_TOKENS = 1000
    SYSTEM_PROMPT_TOKENS = 500
    RAG_CONTEXT_TOKENS = 3000
    
    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 characters)."""
        return len(text) // 4
    
    @classmethod
    def get_available_tokens(cls, model: str = "gpt-4") -> int:
        """Calculate available tokens for conversation history."""
        base_limit = cls.GPT4_CONTEXT_WINDOW if "gpt-4" in model else cls.GPT35_CONTEXT_WINDOW
        reserved = cls.RESPONSE_TOKENS + cls.SYSTEM_PROMPT_TOKENS + cls.RAG_CONTEXT_TOKENS
        return base_limit - reserved
    
    @classmethod
    def trim_messages_to_budget(cls, messages: List[Dict[str, str]], model: str = "gpt-4") -> List[Dict[str, str]]:
        """Trim messages to fit within token budget."""
        available_tokens = cls.get_available_tokens(model)
        
        # Start from most recent and work backwards
        trimmed = []
        total_tokens = 0
        
        for message in reversed(messages):
            msg_tokens = cls.estimate_tokens(message.get("content", ""))
            if total_tokens + msg_tokens > available_tokens:
                break
            trimmed.insert(0, message)
            total_tokens += msg_tokens
        
        return trimmed
