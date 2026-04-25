"""
Query Rewriter - Contextualizes vague queries using conversation history
"""
from typing import List, Dict, Optional
import os


class QueryRewriter:
    """Rewrites user queries to include context from conversation history."""
    
    def __init__(self, llm_client, provider: str = "groq"):
        """
        Initialize query rewriter.
        
        Args:
            llm_client: The LLM client (Groq or Gemini)
            provider: "groq" or "gemini"
        """
        self.llm_client = llm_client
        self.provider = provider
    
    def needs_rewriting(self, query: str, conversation_history: List[Dict[str, str]]) -> bool:
        """
        Intelligently determine if query needs contextualization using LLM.
        
        Args:
            query: The user's query
            conversation_history: Recent messages for context
            
        Returns:
            True if query needs rewriting
        """
        # No history = can't rewrite
        if not conversation_history or len(conversation_history) < 2:
            return False
        
        # Build recent context
        recent_context = ""
        for msg in conversation_history[-3:]:
            role = "Student" if msg.get("role") == "user" else "Advisor"
            content = msg.get("content", "")[:150]
            recent_context += f"{role}: {content}\n"
        
        # Ask LLM to judge
        judgment_prompt = f"""Analyze if this message is a REAL QUESTION that needs contextualization.

Recent conversation:
{recent_context}

New message: "{query}"

IMPORTANT: Determine if this is a real question or just a conversational acknowledgment.

This message is NOT a question if it's ONLY:
- Pure acknowledgment with no request: "ok", "thanks", "got it" (alone)
- Pure deferral: "not now", "maybe later" (alone)
- Pure closing: "bye", "that's all" (alone)

This message IS a question if it contains:
- A request: "explain", "tell me", "how", "what", "why"
- A question marker: "?"
- Combination like "okay, but explain..." or "thanks, now tell me..."

This message NEEDS rewriting if it's a real question AND:
- References previous topics without naming them ("it", "that", "them", "this")
- Would be unclear without conversation history
- Uses vague pronouns or references

Examples:
- "okay thanks" → NO (pure acknowledgment)
- "not for now" → NO (pure deferral)
- "okay, explain me bit better" → YES (question needing context)
- "can you elaborate on that?" → YES (vague reference)
- "what about the grading?" → NO (already clear)

Answer with ONLY "YES" if it needs rewriting, or "NO" otherwise.

Answer:"""

        try:
            if self.provider == "groq":
                response = self.llm_client.chat.completions.create(
                    model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
                    messages=[{"role": "user", "content": judgment_prompt}],
                    temperature=0.1,
                    max_tokens=10
                )
                judgment = response.choices[0].message.content.strip().upper()
            else:
                response = self.llm_client.models.generate_content(
                    model="gemini-1.5-flash-8b",
                    contents=judgment_prompt,
                    config={'temperature': 0.1}
                )
                judgment = response.text.strip().upper()
            
            needs_rewrite = "YES" in judgment
            return needs_rewrite
            
        except Exception as e:
            print(f"  ⚠️ Judgment failed: {e}, assuming no rewrite needed")
            return False
    
    def rewrite_query(
        self,
        current_query: str,
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """
        Rewrite vague query to include explicit context.
        
        Args:
            current_query: The user's current query
            conversation_history: Recent conversation messages
            
        Returns:
            Rewritten, explicit query
        """
        print(f"  🔄 Rewriting query: '{current_query}'")
        
        # Build conversation context (last 4 messages)
        recent_context = ""
        for msg in conversation_history[-4:]:
            role = "Student" if msg.get("role") == "user" else "Advisor"
            content = msg.get("content", "")[:200]  # Limit length
            recent_context += f"{role}: {content}\n"
        
        # Create rewriting prompt
        rewrite_prompt = f"""You are helping to rewrite a vague query into an explicit, searchable query for a knowledge base.

Recent conversation:
{recent_context}

Current query: "{current_query}"

Task: Rewrite this query to be explicit and self-contained by including the context from the conversation.
- Replace ALL pronouns and vague references with the actual subjects from conversation
- Make the query standalone and clear for someone who hasn't seen the conversation
- Keep it concise (1-2 sentences max)
- Focus on the key information needed for search
- Make it suitable for semantic search in a knowledge base

Rewritten query:"""

        try:
            # Call LLM to rewrite query
            if self.provider == "groq":
                response = self.llm_client.chat.completions.create(
                    model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
                    messages=[{"role": "user", "content": rewrite_prompt}],
                    temperature=0.3,
                    max_tokens=150
                )
                rewritten = response.choices[0].message.content.strip()
            else:
                # Gemini
                response = self.llm_client.models.generate_content(
                    model="gemini-1.5-flash-8b",
                    contents=rewrite_prompt,
                    config={'temperature': 0.3}
                )
                rewritten = response.text.strip()
            
            # Clean up common artifacts
            rewritten = rewritten.replace('"', '').replace("'", '').strip()
            
            print(f"  ✅ Rewritten: '{rewritten}'")
            return rewritten
            
        except Exception as e:
            print(f"  ⚠️ Query rewriting failed: {e}")
            print(f"  ↪️ Using original query")
            return current_query
    
    def contextualize_if_needed(
        self,
        query: str,
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """
        Rewrite query with conversation context.
        Called only when initial query was refused.
        
        Args:
            query: Current user query
            conversation_history: Recent messages
            
        Returns:
            Rewritten query with context
        """
        # If no history, can't contextualize
        if not conversation_history or len(conversation_history) < 2:
            return query
        
        print(f"  🔄 Attempting query rewrite with conversation context...")
        
        return self.rewrite_query(query, conversation_history)
