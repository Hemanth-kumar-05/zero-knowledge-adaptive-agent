import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

from google import genai
from groq import Groq

# Load environment variables
load_dotenv()

class Generator:
    """Handles LLM-based answer generation with multiple providers"""
    
    def __init__(
        self,
        model: str = None,
        temperature: float = 0.3,
        provider: str = None
    ):
        # Determine provider from env or parameter
        self.provider = provider or os.getenv("LLM_PROVIDER", "gemini")
        self.temperature = temperature
        
        # Initialize based on provider
        if self.provider == "groq":
            self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            self.model = model or "llama-3.1-8b-instant"  # Updated to latest model
            print(f"🚀 Using Groq with model: {self.model}")
        else:
            self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
            self.model = model or "gemini-1.5-flash-8b"
            print(f"🤖 Using Gemini with model: {self.model}")
    
    def create_rag_prompt(
        self,
        query: str,
        context: str,
        system_instructions: Optional[str] = None,
        conversation_history: List[Dict[str, str]] = None,
        preference_instructions: Optional[str] = None
    ) -> str:
        if system_instructions is None:
            system_instructions = self._get_default_system_instructions()
        
        # Add preference instructions if provided
        if preference_instructions:
            system_instructions = f"{system_instructions}\n\n{preference_instructions}"
            print(f"\n🎯 APPLYING USER PREFERENCES")
            print(f"  Preference instructions added to system prompt")
        
        # Build conversation history section if available
        history_section = ""
        if conversation_history:
            print(f"\n💬 BUILDING PROMPT WITH HISTORY")
            print(f"  Including {len(conversation_history)} history entries")
            history_section = "\n\nPrevious Conversation:\n"
            for msg in conversation_history[-6:]:  # Last 6 messages for context
                role_label = "Student" if msg.get("role") == "user" else "Advisor"
                content_preview = msg.get('content', '')[:60] + '...' if len(msg.get('content', '')) > 60 else msg.get('content', '')
                print(f"    {role_label}: {content_preview}")
                history_section += f"{role_label}: {msg.get('content', '')}\n"
            history_section += "\n"
        else:
            print(f"\n💬 NO CONVERSATION HISTORY - First message in session")
        
        # Build the complete RAG prompt with history
        prompt = f"""{system_instructions}
{history_section}
Context:
{context}

Current Question (answer THIS question specifically): {query}

Provide a clear, direct answer to the current question above:"""
        
        print(f"\n📤 Final prompt length: {len(prompt)} characters")
        print(f"🎯 Current Question: {query}")
        
        return prompt
    
    def _get_default_system_instructions(self) -> str:
        instructions = """
        You are an academic advisor assistant for Nova Crest Institute of Engineering (NCIE).
        
        Your role is to help students understand academic policies and procedures.
        
        CRITICAL CONSTRAINTS:
        - Answer ONLY the CURRENT QUESTION being asked, not previous questions
        - Use ONLY information from the provided context
        - If the context does not contain relevant information, you MUST respond with: 
          "I don't have information about that in the academic documents I have access to. Please contact the academic office directly or check the student portal for more information."
        - Do NOT use external knowledge or make assumptions
        - Do NOT answer questions from the conversation history - ONLY answer the current question
        - Keep answers concise, natural, and conversational
        - Do NOT include source citations, references, or document names in your answer
        - Do NOT add "(Source: ...)" or similar references in your response
        - Provide direct, clean answers without metadata
        
        SPECIAL CASES - Conversational Closings:
        - If the user says "bye", "goodbye", or similar closing: respond with ONLY "Goodbye! Feel free to return if you have more questions."
        - If the user says "no", "no thanks", "that's all" after you offered help: respond with ONLY "Alright! Let me know if you need anything else."
        - Keep closing responses very brief - do NOT ask follow-up questions
        - Do NOT repeat the same response multiple times in a row
        
        FORMATTING RULES:
        - Write in a friendly, helpful tone
        - Use natural language without technical annotations
        - Answer as if you're having a conversation with a student
        - Never mention document names, sections, or source identifiers in your response
        - Use very simple markdown for formatting (e.g., bullet points, bold) if needed
        
        Remember: You are a zero-knowledge baseline system. Accuracy is more important than coverage.
        """
        
        return instructions
    
    def generate(
        self,
        query: str,
        context: str,
        conversation_history: List[Dict[str, str]] = None,
        preference_instructions: Optional[str] = None
    ) -> str:
        try:
            # Create the prompt with history and preferences
            prompt = self.create_rag_prompt(
                query, 
                context, 
                conversation_history=conversation_history,
                preference_instructions=preference_instructions
            )
            
            # Call appropriate API based on provider
            if self.provider == "groq":
                # Groq uses OpenAI-compatible API
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                    max_tokens=1024
                )
                return response.choices[0].message.content
            else:
                # Gemini API
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config={
                        'temperature': self.temperature
                    }
                )
                return response.text
            
        except Exception as e:
            # Handle errors gracefully - show full error for debugging
            print(f"❌ Error in {self.provider}: {e}")
            return "I apologize, but I encountered an error while generating a response."
    
    def should_refuse(self, context: str, query: str) -> bool:
        
        # Check if context is empty or too short
        if not context or len(context.strip()) < 50:
            return True
        return False
    
    def get_refusal_message(self) -> str:
        return (
            "I don't have information about that in the academic documents "
            "I have access to. Please contact the academic office directly "
            "or check the student portal for more information."
        )
    
    def generate_with_validation(
        self,
        query: str,
        context: str,
        conversation_history: List[Dict[str, str]] = None,
        preference_instructions: Optional[str] = None
    ) -> Dict[str, any]:
        
        # Check if should refuse
        if self.should_refuse(context, query):
            return {
                'answer': self.get_refusal_message(),
                'refused': True,
                'context_used': False,
                'sources_count': 0,
                'confidence': 'none'
            }
        
        # Generate answer with history and preferences
        try:
            answer = self.generate(
                query, 
                context, 
                conversation_history=conversation_history,
                preference_instructions=preference_instructions
            )
            
            # Check if LLM generated a refusal response (even when we didn't explicitly refuse)
            # This catches cases where LLM decides to refuse based on irrelevant context
            refusal_indicators = [
                "I don't have information",
                "I don't have that information",
                "not in the academic documents",
                "cannot find information",
                "no information about that"
            ]
            
            is_refusal = any(indicator.lower() in answer.lower() for indicator in refusal_indicators)
            
            if is_refusal:
                return {
                    'answer': self.get_refusal_message(),
                    'refused': True,
                    'context_used': False,
                    'sources_count': 0,
                    'confidence': 'none'
                }
            
            # Count sources (simple heuristic: number of [Source:...] markers)
            import re
            sources_count = len(re.findall(r'\[Source:', context))
            
            # Determine if context was actually used
            context_used = len(answer) > 0 and answer != self.get_refusal_message()
            
            # Estimate confidence based on answer length and source count
            if sources_count >= 3 and len(answer) > 100:
                confidence = 'high'
            elif sources_count >= 1 and len(answer) > 50:
                confidence = 'medium'
            else:
                confidence = 'low'
            
            return {
                'answer': answer,
                'refused': False,
                'context_used': context_used,
                'confidence': confidence
            }
            
        except Exception as e:
            print(f"Error in generate_with_validation: {e}")
            return {
                'answer': self.get_refusal_message(),
                'refused': True,
                'context_used': False,
                'confidence': 'none'
            }


# ============================================================================
# TESTING SECTION
# ============================================================================

# if __name__ == "__main__":
#     print("🧪 Testing Answer Generation...\n")
    
#     # Test 1: Initialize generator
#     print("1️⃣ Initializing generator...")
#     try:
#         generator = Generator()
#         print("   ✓ Generator initialized")
#     except Exception as e:
#         print(f"   ⚠️  Error: {e}")
#         print("   💡 Make sure to set up your LLM client (OpenAI API key, etc.)")
#         exit(1)
    
#     # Test 2: Test prompt creation
#     print("\n2️⃣ Testing prompt creation...")
#     test_query = "How do I register for exams?"
#     test_context = """
#     [Source: ncie_exam_registration - Registration Process]
#     Students must register for exams at least two weeks before the exam date.
#     Registration is done through the student portal. Late registrations may
#     incur a penalty fee.
#     """
    
#     prompt = generator.create_rag_prompt(test_query, test_context)
#     print(f"   ✓ Created prompt ({len(prompt)} characters)")
#     print(f"\n   Prompt preview:")
#     print("   " + "-" * 50)
#     print("   " + prompt[:300] + "...")
#     print("   " + "-" * 50)
    
#     # Test 3: Test refusal logic
#     print("\n3️⃣ Testing refusal logic...")
    
#     # Should refuse: empty context
#     should_refuse_empty = generator.should_refuse("", test_query)
#     print(f"   Empty context → Refuse: {should_refuse_empty} ✓")
    
#     # Should NOT refuse: good context
#     should_refuse_good = generator.should_refuse(test_context, test_query)
#     print(f"   Good context → Refuse: {should_refuse_good} ✓")
    
#     # Test 4: Test generation (if LLM is configured)
#     print("\n4️⃣ Testing answer generation...")
#     try:
#         result = generator.generate_with_validation(test_query, test_context)
#         print(f"   ✓ Generation successful")
#         print(f"   Refused: {result.get('refused', 'N/A')}")
#         print(f"   Answer preview: {result.get('answer', 'N/A')[:150]}...")
#     except Exception as e:
#         print(f"   ⚠️  Generation failed: {e}")
#         print("   💡 This is expected if LLM client isn't configured yet")
    
#     print("\n" + "="*60)
#     print("✅ Generator tests complete!")
#     print("="*60)
#     print("\n💡 Next: Implement pipeline.py to orchestrate retrieval + generation")
