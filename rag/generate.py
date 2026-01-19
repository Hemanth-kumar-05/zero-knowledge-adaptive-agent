import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

from google import genai

# Load environment variables
load_dotenv()

class Generator:
    """Handles LLM-based answer generation"""
    
    def __init__(
        self,
        model: str = "gemini-1.5-flash-8b",
        temperature: float = 0.3
    ):
        self.model = model
        self.temperature = temperature
        
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    
    def create_rag_prompt(
        self,
        query: str,
        context: str,
        system_instructions: Optional[str] = None
    ) -> str:
        if system_instructions is None:
            system_instructions = self._get_default_system_instructions()
        
        # Build the complete RAG prompt
        prompt = f"""{system_instructions}

Context:
{context}

Question: {query}

Answer:"""
        
        return prompt
    
    def _get_default_system_instructions(self) -> str:
        instructions = """
        You are an academic advisor assistant for Nova Crest Institute of Engineering (NCIE).
        
        Your role is to help students understand academic policies and procedures.
        
        CRITICAL CONSTRAINTS:
        - Answer ONLY using information from the provided context
        - If the context does not contain relevant information, you MUST respond with: 
          "I don't have information about that in the academic documents I have access to."
        - Do NOT use external knowledge or make assumptions
        - Be precise and cite the relevant policy section when possible
        - Keep answers concise and focused on the question
        
        Remember: You are a zero-knowledge baseline system. Accuracy is more important than coverage.
        """
        
        return instructions
    
    def generate(
        self,
        query: str,
        context: str
    ) -> str:
        try:
            # Create the prompt
            prompt = self.create_rag_prompt(query, context)
            
            # Call Gemini API with correct format
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    'temperature': self.temperature
                }
            )
            
            # Extract and return the text
            return response.text
            
        except Exception as e:
            # Handle errors gracefully - show full error for debugging
            print(e)
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
        context: str
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
        
        # Generate answer
        try:
            answer = self.generate(query, context)
            
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
