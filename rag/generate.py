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
        self.last_generation_error = None
        
        # Initialize based on provider
        if self.provider == "groq":
            self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            self.model = model or "llama-3.1-8b-instant"  # Updated to latest model
            print(f"🚀 Using Groq with model: {self.model}")
        else:
            self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
            self.model = model or "gemini-1.5-flash-8b"
            print(f"🤖 Using Gemini with model: {self.model}")
    
    def _classify_generation_exception(self, error: Exception) -> Dict[str, any]:
        message = str(error)
        status_code = getattr(error, "status_code", None)
        error_type = None
        error_code = None
        retry_after_seconds = None
        retryable = False
        category = "provider_error"

        body = getattr(error, "body", None)
        if isinstance(body, dict):
            payload_error = body.get("error", {})
            error_type = payload_error.get("type")
            error_code = payload_error.get("code")
            message = payload_error.get("message") or message

        if status_code == 429:
            retryable = True
            category = "provider_rate_limit"
        elif status_code == 413 and "rate_limit_exceeded" in (error_code or ""):
            category = "provider_rate_limit"
        elif "rate limit" in message.lower() or "rate_limit_exceeded" in message.lower():
            category = "provider_rate_limit"
            retryable = status_code == 429

        if "Please try again in" in message:
            try:
                retry_fragment = message.split("Please try again in", 1)[1].split(".", 1)[0].strip()
                if retry_fragment.endswith("ms"):
                    retry_after_seconds = max(0.0, float(retry_fragment[:-2].strip()) / 1000.0)
                elif retry_fragment.endswith("s"):
                    retry_after_seconds = max(0.0, float(retry_fragment[:-1].strip()))
            except Exception:
                retry_after_seconds = None

        return {
            "category": category,
            "provider": self.provider,
            "model": self.model,
            "status_code": status_code,
            "error_type": error_type,
            "error_code": error_code,
            "message": message,
            "retryable": retryable,
            "retry_after_seconds": retry_after_seconds,
        }

    def create_rag_prompt(
        self,
        query: str,
        context: str,
        system_instructions: Optional[str] = None,
        conversation_history: List[Dict[str, str]] = None,
        preference_instructions: Optional[str] = None,
        user_context: Optional[str] = None,
        extension_system_prompt: Optional[str] = None
    ) -> str:
        # Use extension system prompt if provided, otherwise use default
        if extension_system_prompt:
            system_instructions = extension_system_prompt
            print(f"\n🧩 USING EXTENSION SYSTEM PROMPT")
            print(f"  Extension prompt: {extension_system_prompt[:100]}..." if len(extension_system_prompt) > 100 else f"  Extension prompt: {extension_system_prompt}")
        elif system_instructions is None:
            system_instructions = self._get_default_system_instructions()
        
        # Add preference instructions if provided
        if preference_instructions:
            system_instructions = f"{system_instructions}\n\n{preference_instructions}"
            print(f"\n🎯 APPLYING USER PREFERENCES")
            print(f"  Preference instructions added to system prompt")
        
        # Add user context (memory) if provided
        if user_context:
            system_instructions = f"{system_instructions}\n\n{user_context}"
            print(f"\n🧠 APPLYING USER MEMORY")
            print(f"  User context: {user_context[:100]}..." if len(user_context) > 100 else f"  User context: {user_context}")
        
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

        # Extension mode should not inherit the strict RAG refusal scaffold,
        # especially when no policy-doc context is provided.
        if extension_system_prompt:
            extension_context = context if context and context.strip() else "(none provided)"
            prompt = f"""{system_instructions}
{history_section}
Extension Context:
{extension_context}

Current User Request:
{query}

INSTRUCTIONS FOR EXTENSION RESPONSE:
1. Complete the user's request directly.
2. Do not refuse only because policy-document context is empty.
3. If requirements are missing, make reasonable assumptions and state them briefly.
4. When asked for code/lab content, provide concrete, actionable output.

Return the best possible response for the extension task."""

            print(f"\n📤 Final extension prompt length: {len(prompt)} characters")
            print(f"🎯 Current Extension Request: {query}")
            return prompt
        
        # Build the complete RAG prompt with history
        prompt = f"""{system_instructions}
{history_section}
Context:
{context}

Current Question (answer THIS question specifically): {query}

INSTRUCTIONS FOR ANSWERING:
1. First, review the context above carefully
2. Identify which specific parts of the context (if any) are relevant to the question
3. If you cannot find explicit information to answer the question, you MUST refuse - do not guess or extrapolate
4. Only include information that is directly stated in the context
5. If the context only provides vague information (e.g., "may influence"), answer ONLY with that vague information - do NOT add specifics

Provide a clear, direct answer to the current question above:"""
        
        print(f"\n📤 Final prompt length: {len(prompt)} characters")
        print(f"🎯 Current Question: {query}")
        
        return prompt
    
    def _get_default_system_instructions(self) -> str:
        instructions = """
        You are an academic advisor assistant for Nova Crest Institute of Engineering (NCIE).
        
        Your role is to help students understand academic policies and procedures.
        
        MEMORY & PERSONALIZATION:
        - If you receive a CONTEXT section with user information (name, year, courses, etc.), use it naturally in your responses
        - For greetings ("Hey", "Hello", etc.), respond warmly and casually - you can use their name if available but don't make it awkward
        - ONLY explicitly mention "remembering" when directly asked ("do you remember me?", "what do you know about me?", etc.)
        - Incorporate remembered details naturally and helpfully when relevant to the conversation
        - Be conversational and friendly, not robotic about using memory
        
        CRITICAL CONSTRAINTS - ANTI-HALLUCINATION RULES:
        ⚠️ ABSOLUTE RULE: Every single fact, number, percentage, threshold, deadline, or policy detail in your answer MUST appear verbatim in the provided context. If it's not in the context, DO NOT include it in your answer.
        
        - Answer ONLY the CURRENT QUESTION being asked, not previous questions
        - Use ONLY information explicitly stated in the provided context below
        - NEVER use your general knowledge, common sense, or make educated guesses
        - NEVER invent numbers, percentages, thresholds, or specific policy details (e.g., "75%", "two weeks", "five steps")
        - NEVER extrapolate or infer consequences that aren't explicitly stated in the context
        - NEVER add procedural steps or requirements not mentioned in the context
        - NEVER mention specific courses, departments, or entities unless they appear in the context
        
        ⚠️ VERIFICATION CHECKLIST (check before responding):
        1. Is EVERY specific detail in my answer explicitly present in the context?
        2. Did I invent any numbers, percentages, or thresholds? If yes, REFUSE.
        3. Did I extrapolate consequences not stated in the context? If yes, REFUSE.
        4. Did I use phrases like "typically", "usually", "may lead to" without explicit context? If yes, REFUSE.
        5. If the context only says something "may" happen, do NOT provide specific details about what happens.
        
        WHEN TO REFUSE (STRICT REFUSAL POLICY):
        - If the context is vague (e.g., "may influence eligibility") - Answer ONLY what's stated, do NOT elaborate
        - If specific numbers/thresholds are asked but not in context - REFUSE IMMEDIATELY
        - Questions about clubs/societies unless explicitly mentioned in context
        - Questions about campus facilities, locations, or infrastructure
        - Questions about specific people (faculty, staff, students) unless in context
        - Questions about events, schedules, or activities not in the documents
        - Anything requiring real-world knowledge beyond the provided academic policies
        - Any question where the answer would require you to invent details
        
        REFUSAL RESPONSE:
        If the context does not contain sufficient specific information, you MUST respond with: 
        "I don't have specific information about that in the academic documents I have access to. The documents mention [summarize ONLY what's actually stated], but don't provide the specific details you're asking about. Please contact the academic office directly or check the student portal for more precise information."
        
        SPECIAL CASES - Conversational Closings:
        - If the user says "bye", "goodbye", or similar closing: respond with ONLY "Goodbye! Feel free to return if you have more questions."
        - If the user says "no", "no thanks", "that's all" after you offered help: respond with ONLY "Alright! Let me know if you need anything else."
        - Keep closing responses very brief - do NOT ask follow-up questions
        - Do NOT repeat the same response multiple times in a row
        
        FORMATTING RULES:
        - Use natural language without technical annotations
        - Answer as if you're having a conversation with a student
        - Never mention document names, sections, or source identifiers in your response
        - Use very simple markdown for formatting (e.g., bullet points, bold) if needed
        - If you can only partially answer, clearly state what information is missing
        
        Remember: You are a zero-knowledge baseline system. Accuracy is more important than coverage. When in doubt, refuse. Better to say "I don't know" than to provide incorrect information.
        
        ⛔ HALLUCINATION = FAILURE. If you cannot answer using ONLY the provided context, you MUST refuse.
        """
        
        return instructions
    
    def generate(
        self,
        query: str,
        context: str,
        conversation_history: List[Dict[str, str]] = None,
        preference_instructions: Optional[str] = None,
        user_context: Optional[str] = None,
        extension_system_prompt: Optional[str] = None,
        max_tokens: int = 4096
    ) -> str:
        self.last_generation_error = None
        try:
            # Create the prompt with history, preferences, user context, and extension
            prompt = self.create_rag_prompt(
                query, 
                context, 
                conversation_history=conversation_history,
                preference_instructions=preference_instructions,
                user_context=user_context,
                extension_system_prompt=extension_system_prompt
            )
            
            # Call appropriate API based on provider
            if self.provider == "groq":
                # Groq uses OpenAI-compatible API
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
            else:
                # Gemini API
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config={
                        'temperature': self.temperature,
                        'max_output_tokens': max_tokens
                    }
                )
                return response.text
            
        except Exception as e:
            # Handle errors gracefully - show full error for debugging
            print(f"❌ Error in {self.provider}: {e}")
            self.last_generation_error = self._classify_generation_exception(e)
            return "I apologize, but I encountered an error while generating a response."
    
    def should_refuse(self, context: str, query: str) -> bool:
        """
        Enhanced refusal logic that checks if context is sufficient to answer the query.
        Returns True if we should refuse to answer.
        """
        import re
        
        # Check if context is empty or too short
        if not context or len(context.strip()) < 50:
            return True
        
        # If query asks about specific numbers/thresholds, check if context has them
        number_queries = ['how many', 'how much', 'percentage', '%', 'threshold', 'minimum', 'maximum']
        asks_for_numbers = any(phrase in query.lower() for phrase in number_queries)
        
        if asks_for_numbers:
            # Check if context has actual numbers
            has_percentages = bool(re.search(r'\d+%', context))
            has_numbers = bool(re.search(r'\b\d+\s+(weeks?|days?|months?|credits?|points?|hours?)\b', context))
            
            # If query asks for numbers but context doesn't have them, refuse
            if not (has_percentages or has_numbers):
                print(f"   ⚠️ Query asks for specific numbers but context lacks them - refusing")
                return True
        
        # Check if context is just generic/vague and doesn't actually answer the question
        # If context is very short and only has vague language, it's probably not sufficient
        vague_only_phrases = ['may be', 'may influence', 'potentially', 'could', 'might']
        vague_count = sum(1 for phrase in vague_only_phrases if phrase in context.lower())
        
        # If context is short AND mostly vague, consider refusing
        if len(context.strip()) < 200 and vague_count >= 2:
            print(f"   ⚠️ Context is too vague ({vague_count} vague phrases in short context) - refusing")
            return True
        
        return False
    
    def detect_hallucination(self, answer: str, context: str) -> Dict[str, any]:
        """
        Detect potential hallucinations by checking if specific facts in answer appear in context.
        Returns dict with 'is_hallucinating' bool and 'hallucination_indicators' list.
        """
        import re
        
        hallucination_indicators = []
        
        # Extract percentages from answer (e.g., "75%", "80%")
        answer_percentages = set(re.findall(r'\b\d+%', answer))
        context_percentages = set(re.findall(r'\b\d+%', context))
        
        # Check if answer has percentages not in context
        invented_percentages = answer_percentages - context_percentages
        if invented_percentages:
            hallucination_indicators.append(f"Invented percentages: {', '.join(invented_percentages)}")
        
        # Extract specific numbers followed by common units/words
        # Pattern: number + (weeks|days|months|years|steps|points|courses|credits)
        number_pattern = r'\b(\d+)\s+(weeks?|days?|months?|years?|steps?|points?|courses?|credits?|semesters?)\b'
        answer_numbers = set(re.findall(number_pattern, answer.lower()))
        context_numbers = set(re.findall(number_pattern, context.lower()))
        
        invented_numbers = answer_numbers - context_numbers
        if invented_numbers:
            hallucination_indicators.append(f"Invented specific counts: {', '.join([f'{num} {unit}' for num, unit in invented_numbers])}")
        
        # Check for suspicious patterns that indicate extrapolation
        suspicious_patterns = [
            (r'step \d+:', 'numbered steps'),
            (r'consequence', 'consequences'),
            (r'will be required to', 'specific requirements'),
            (r'must meet with', 'specific procedures'),
            (r'may lead to', 'extrapolated outcomes'),
        ]
        
        for pattern, description in suspicious_patterns:
            if re.search(pattern, answer.lower()) and not re.search(pattern, context.lower()):
                # Only flag if the answer is being very specific about something vague in context
                if 'may' in answer.lower() and ('must' in answer.lower() or 'will' in answer.lower()):
                    hallucination_indicators.append(f"Extrapolation detected: {description}")
        
        # Check for invented policy details
        # If answer mentions very specific procedures but context only has vague language
        vague_context_indicators = ['may influence', 'may be considered', 'typically', 'generally']
        has_vague_context = any(indicator in context.lower() for indicator in vague_context_indicators)
        
        specific_answer_indicators = ['you must', 'you will', 'you are required', 'it will', 'this will lead to']
        has_specific_answer = any(indicator in answer.lower() for indicator in specific_answer_indicators)
        
        if has_vague_context and has_specific_answer:
            hallucination_indicators.append("Converted vague context into specific claims")
        
        is_hallucinating = len(hallucination_indicators) > 0
        
        return {
            'is_hallucinating': is_hallucinating,
            'hallucination_indicators': hallucination_indicators,
            'confidence': 'low' if is_hallucinating else 'medium'
        }
    
    def get_refusal_message(self, context: str = None) -> str:
        """
        Generate a refusal message, optionally summarizing what IS in the context.
        """
        base_message = (
            "I don't have specific information about that in the academic documents "
            "I have access to."
        )
        
        # If context is provided and has some content, try to summarize what's actually there
        if context and len(context.strip()) > 50:
            # Check if context mentions the topic vaguely
            if 'attendance' in context.lower():
                base_message += (
                    " The documents mention that attendance records may be considered "
                    "as part of the Continuous Assessment framework and may influence eligibility, "
                    "but don't provide specific thresholds or consequences."
                )
            elif 'may' in context.lower() or 'generally' in context.lower():
                base_message += (
                    " The documents provide some general information but lack the specific "
                    "details needed to fully answer your question."
                )
        
        base_message += (
            " Please contact the academic office directly or check the student portal "
            "for more precise information."
        )
        
        return base_message
    
    def generate_with_validation(
        self,
        query: str,
        context: str,
        conversation_history: List[Dict[str, str]] = None,
        preference_instructions: Optional[str] = None,
        user_context: Optional[str] = None,
        extension_system_prompt: Optional[str] = None,
        max_tokens: int = 4096
    ) -> Dict[str, any]:
        
        # Check if should refuse
        if self.should_refuse(context, query):
            return {
                'answer': self.get_refusal_message(context),
                'refused': True,
                'context_used': False,
                'sources_count': 0,
                'confidence': 'none',
                'generation_error': None
            }
        
        # Generate answer with history, preferences, user context, and extension
        try:
            answer = self.generate(
                query, 
                context, 
                conversation_history=conversation_history,
                preference_instructions=preference_instructions,
                user_context=user_context,
                extension_system_prompt=extension_system_prompt,
                max_tokens=max_tokens
            )
            
            # Check if LLM generated a refusal response (even when we didn't explicitly refuse)
            # This catches cases where LLM decides to refuse based on irrelevant context
            refusal_indicators = [
                "I don't have information",
                "I don't have that information",
                "I don't have specific information",
                "not in the academic documents",
                "cannot find information",
                "no information about that"
            ]
            
            is_refusal = any(indicator.lower() in answer.lower() for indicator in refusal_indicators)
            
            if is_refusal:
                return {
                    'answer': self.get_refusal_message(context),
                    'refused': True,
                    'context_used': False,
                    'sources_count': 0,
                    'confidence': 'none',
                    'generation_error': self.last_generation_error
                }
            
            # ⚠️ NEW: Detect hallucinations in the generated answer
            hallucination_check = self.detect_hallucination(answer, context)
            
            if hallucination_check['is_hallucinating']:
                print(f"\n🚨 HALLUCINATION DETECTED!")
                for indicator in hallucination_check['hallucination_indicators']:
                    print(f"   ⚠️ {indicator}")
                print(f"   → Forcing refusal response")
                
                # Force refusal if hallucination detected
                return {
                    'answer': self.get_refusal_message(context),
                    'refused': True,
                    'context_used': False,
                    'sources_count': 0,
                    'confidence': 'none',
                    'generation_error': self.last_generation_error,
                    'hallucination_detected': True,
                    'hallucination_indicators': hallucination_check['hallucination_indicators']
                }
            
            # Count sources (simple heuristic: number of [Source:...] markers)
            import re
            sources_count = len(re.findall(r'\[Source:', context))
            
            # Determine if context was actually used
            context_used = len(answer) > 0 and answer != self.get_refusal_message(context)
            
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
                'confidence': confidence,
                'hallucination_detected': False,
                'generation_error': self.last_generation_error
            }
            
        except Exception as e:
            print(f"Error in generate_with_validation: {e}")
            return {
                'answer': self.get_refusal_message(context),
                'refused': True,
                'context_used': False,
                'confidence': 'none',
                'generation_error': self._classify_generation_exception(e)
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
