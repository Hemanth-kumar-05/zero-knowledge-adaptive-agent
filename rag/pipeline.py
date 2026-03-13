import sys
from pathlib import Path
from typing import Dict, List, Optional
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from rag.retrieve import Retriever
from rag.generate import Generator
from rag.query_rewriter import QueryRewriter


class RAGPipeline:
    """Complete RAG pipeline orchestration"""
    
    def __init__(
        self,
        persist_directory: str = "data/chroma_db",
        collection_name: str = "academic_docs",
        llm_model: str = None,  # Will be determined by provider
        verbose: bool = True
    ):
        self.verbose = verbose
        
        # Initialize retriever
        if self.verbose:
            print("Initializing retriever...")
        self.retriever = Retriever(persist_directory, collection_name)
        
        # Initialize generator (it will auto-detect provider and set correct model)
        if self.verbose:
            print("Initializing generator...")
        self.generator = Generator(model=llm_model)  # Pass None to use provider defaults
        
        # Initialize query rewriter
        if self.verbose:
            print("Initializing query rewriter...")
        self.query_rewriter = QueryRewriter(
            self.generator.client,
            provider=self.generator.provider
        )
        
        if self.verbose:
            print("RAG Pipeline initialized")
    
    def query(
        self,
        question: str,
        top_k: int = 5,
        min_similarity: float = 0.3,
        conversation_history: list = None,
        conversation_metadata: dict = None,
        user_preferences: list = None,
        preference_instructions: str = None,
        user_context: str = None,
        extension_system_prompt: str = None
    ) -> Dict:
        
        conversation_history = conversation_history or []
        conversation_metadata = conversation_metadata or {}
        user_preferences = user_preferences or []
        
        start_time = time.time()
        
        # Log if extension is being used
        if extension_system_prompt and self.verbose:
            print(f"\n🧩 EXTENSION MODE ACTIVE")
            print(f"  Using specialized extension prompt")
        
        # Log if preferences are being applied
        if preference_instructions and self.verbose:
            print(f"\n🎯 PERSONALIZATION ENABLED")
            print(f"  Applying {len(user_preferences)} user preferences")
        
        # Log if user context is available
        if user_context and self.verbose:
            print(f"\n🧠 USER MEMORY ENABLED")
            print(f"  User context: {user_context[:100]}..." if len(user_context) > 100 else f"  User context: {user_context}")
        
        # First attempt with original query
        if self.verbose:
            print(f"\n🎯 ATTEMPT 1: Original query")
        
        result = self._execute_query(
            question=question,
            top_k=top_k,
            min_similarity=min_similarity,
            conversation_history=conversation_history,
            conversation_metadata=conversation_metadata,
            preference_instructions=preference_instructions,
            user_context=user_context,
            extension_system_prompt=extension_system_prompt
        )
        
        # If refused AND we have conversation context, try rewriting
        if result['refused'] and conversation_history and len(conversation_history) >= 2:
            if self.verbose:
                print(f"\n⚠️ First attempt refused - trying with contextualized query...")
                print(f"🔄 ATTEMPT 2: Query rewriting")
            
            # Rewrite query with context
            rewritten_question = self.query_rewriter.contextualize_if_needed(
                question,
                conversation_history
            )
            
            # Only retry if query actually changed
            if rewritten_question != question:
                if self.verbose:
                    print(f"  📝 Original: '{question}'")
                    print(f"  ✨ Enhanced: '{rewritten_question}'")
                    print(f"\n🎯 Retrying with enhanced query...")
                
                # Retry with rewritten query
                result = self._execute_query(
                    question=rewritten_question,
                    top_k=top_k,
                    min_similarity=min_similarity,
                    conversation_history=conversation_history,
                    conversation_metadata=conversation_metadata,
                    preference_instructions=preference_instructions,
                    user_context=user_context
                )
                
                # Keep original question in result for user
                result['question'] = question
                
                if self.verbose:
                    if result['refused']:
                        print(f"  ❌ Still refused after rewriting")
                    else:
                        print(f"  ✅ Success with rewritten query!")
            else:
                if self.verbose:
                    print(f"  ℹ️ Query unchanged, skipping retry")
        
        total_time = (time.time() - start_time) * 1000
        result['total_time_ms'] = total_time
        
        return result
    
    def _execute_query(
        self,
        question: str,
        top_k: int,
        min_similarity: float,
        conversation_history: list,
        conversation_metadata: dict,
        preference_instructions: str = None,
        user_context: str = None,
        extension_system_prompt: str = None
    ) -> Dict:
        """Execute a single query attempt."""
        
        # Step 1: Retrieval
        if self.verbose:
            print(f"  🔍 Retrieving relevant chunks...")
        
        retrieval_start = time.time()
        retrieved_chunks = self.retriever.retrieve(
            query=question,
            top_k=top_k,
            min_similarity=min_similarity
        )
        retrieval_time = (time.time() - retrieval_start) * 1000
        
        if self.verbose:
            print(f"  📦 Retrieved {len(retrieved_chunks)} chunks in {retrieval_time:.0f}ms")
            if conversation_metadata.get("has_context"):
                print(f"  💬 Using conversation context: {conversation_metadata.get('total_messages', 0)} messages")
        
        # Step 2: Format context
        if self.verbose:
            print(f"  📝 Formatting context...")
        
        context = self.retriever.format_context_for_llm(retrieved_chunks)
        
        if self.verbose:
            print(f"  📄 Context size: {len(context)} characters")
        
        # Step 3: Generate answer with conversation history and preferences
        if self.verbose:
            print(f"  🤖 Generating answer...")
        
        generation_start = time.time()
        generation_result = self.generator.generate_with_validation(
            query=question,
            context=context,
            conversation_history=conversation_history,
            preference_instructions=preference_instructions,
            user_context=user_context,
            extension_system_prompt=extension_system_prompt
        )
        generation_time = (time.time() - generation_start) * 1000
        
        if self.verbose:
            if generation_result['refused']:
                print(f"  ❌ Refused - insufficient context")
            else:
                print(f"  ✅ Generated answer in {generation_time:.0f}ms")
        
        # Step 4: Package results with source information
        # IMPORTANT: Always include sources, even when refused, for Phase 3 policy claim detection
        sources = []
        for chunk in retrieved_chunks:
            sources.append({
                'id': chunk.get('id', 'unknown'),  # Chunk ID for Phase 3
                'text': chunk.get('text', ''),  # Full chunk text for Phase 3
                'doc_id': chunk['metadata'].get('doc_id', 'unknown'),
                'section': chunk['metadata'].get('section', 'unknown'),
                'similarity': chunk.get('similarity', 0.0),
                'confidence': chunk['metadata'].get('confidence', 1.0),
                'metadata': chunk.get('metadata', {})  # Full metadata
            })
        
        result = {
            'question': question,
            'answer': generation_result['answer'],
            'sources': sources,
            'refused': generation_result['refused'],
            'retrieval_count': len(retrieved_chunks),
            'retrieval_time_ms': retrieval_time,
            'generation_time_ms': generation_time,
            'total_time_ms': 0,  # Will be set by main query method
            'confidence': generation_result.get('confidence', 'unknown')
        }
        
        return result
    
    # def batch_query(
    #     self,
    #     questions: List[str],
    #     **kwargs
    # ) -> List[Dict]:
    #     results = []
        
    #     for i, question in enumerate(questions, 1):
    #         if self.verbose:
    #             print(f"\n{'='*60}")
    #             print(f"Processing query {i}/{len(questions)}")
    #             print(f"{'='*60}")
            
    #         try:
    #             result = self.query(question, **kwargs)
    #             results.append(result)
    #         except Exception as e:
    #             if self.verbose:
    #                 print(f"Error processing query: {e}")
    #             # Add error result
    #             results.append({
    #                 'question': question,
    #                 'answer': 'Error processing query',
    #                 'sources': [],
    #                 'refused': True,
    #                 'error': str(e)
    #             })
        
    #     return results
    
    def evaluate_answer_quality(
        self,
        result: Dict,
        check_sources: bool = True
    ) -> Dict:
        
        metrics = {
            'answer_length': len(result.get('answer', '')),
            'source_count': len(result.get('sources', [])),
            'refused': result.get('refused', False),
            'response_time_ms': result.get('total_time_ms', 0),
        }
        
        # Calculate quality score (0-100)
        quality_score = 0.0
        
        # Factor 1: Answer length (0-30 points)
        answer_len = metrics['answer_length']
        if answer_len > 200:
            quality_score += 30
        elif answer_len > 100:
            quality_score += 20
        elif answer_len > 50:
            quality_score += 10
        
        # Factor 2: Source count (0-30 points)
        source_count = metrics['source_count']
        if source_count >= 3:
            quality_score += 30
        elif source_count >= 2:
            quality_score += 20
        elif source_count >= 1:
            quality_score += 10
        
        # Factor 3: Not refused (0-20 points)
        if not metrics['refused']:
            quality_score += 20
        
        # Factor 4: Response time (0-20 points)
        response_time = metrics['response_time_ms']
        if response_time < 2000:
            quality_score += 20
        elif response_time < 5000:
            quality_score += 10
        elif response_time < 10000:
            quality_score += 5
        
        metrics['quality_score'] = quality_score
        
        # Add interpretation
        if quality_score >= 80:
            metrics['quality_rating'] = 'excellent'
        elif quality_score >= 60:
            metrics['quality_rating'] = 'good'
        elif quality_score >= 40:
            metrics['quality_rating'] = 'fair'
        else:
            metrics['quality_rating'] = 'poor'
        
        return metrics
    
    def interactive_mode(self):
        print("\n" + "="*60)
        print("🎓 NCIE Academic Advisor RAG System")
        print("="*60)
        print("\nAsk questions about academic policies and procedures.")
        print("Type 'quit' or 'exit' to stop.\n")
        
        while True:
            # Get user input
            try:
                question = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\nGoodbye!")
                break
            
            if not question:
                continue
            
            if question.lower() in ['quit', 'exit', 'bye']:
                print("\nGoodbye!")
                break
            
            # Process query
            try:
                result = self.query(question, top_k=5, min_similarity=0.2)
                
                # Display answer
                print(f"\nAssistant: {result['answer']}")
                
                # Show sources if available
                if result.get('sources') and not result['refused']:
                    print(f"\nSources ({len(result['sources'])} documents):")
                    for i, source in enumerate(result['sources'][:3], 1):
                        print(f"   {i}. {source['section']} (from {source['doc_id']})")
                        print(f"      Relevance: {source['similarity']:.2f}")
                
                # Show performance metrics
                if self.verbose:
                    print(f"\nResponse time: {result['total_time_ms']:.0f}ms")
                    
            except Exception as e:
                print(f"\nError: {e}")
                print("Please try again or rephrase your question.")
            
            print()  # Empty line for readability


# ============================================================================
# MODULE-LEVEL INSTANCE (Singleton for imports)
# ============================================================================

# Create a module-level instance that can be imported by other modules
# This is initialized lazily to avoid startup overhead
_rag_pipeline_instance = None

def get_rag_pipeline(verbose: bool = False) -> RAGPipeline:
    """Get or create the RAG pipeline singleton instance"""
    global _rag_pipeline_instance
    if _rag_pipeline_instance is None:
        # Construct absolute path to ChromaDB (project_root/data/chroma_db)
        project_root = Path(__file__).parent.parent
        chroma_path = str(project_root / "data" / "chroma_db")
        _rag_pipeline_instance = RAGPipeline(
            persist_directory=chroma_path,
            verbose=verbose
        )
    return _rag_pipeline_instance

# For backward compatibility, expose as rag_pipeline
rag_pipeline = get_rag_pipeline()


# ============================================================================
# TESTING SECTION
# ============================================================================

if __name__ == "__main__":
    print("🧪 Testing RAG Pipeline...\n")
    
    # # Test 1: Initialize pipeline
    print("1️⃣ Initializing RAG pipeline...")
    try:
        pipeline = RAGPipeline(verbose=True)
        print("   ✓ Pipeline ready")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print("   💡 Make sure vector database and LLM are configured")
        exit(1)
    
    # # Test 2: Single query
    # print("\n2️⃣ Testing single query...")
    # test_question = "How do I register for exams?"
    
    # try:
    #     result = pipeline.query(test_question, top_k=3)
        
    #     print(f"\n   📊 Results:")
    #     print(f"   Question: {result['question']}")
    #     print(f"   Answer: {result['answer'][:200]}...")
    #     print(f"   Sources: {result.get('retrieval_count', 0)} chunks")
    #     print(f"   Refused: {result['refused']}")
    #     print(f"   Time: {result['total_time_ms']:.0f}ms")
    # except Exception as e:
    #     print(f"   ⚠️  Query failed: {e}")
    
    # # Test 3: Batch queries
    # print("\n3️⃣ Testing batch queries...")
    # test_questions = [
    #     "What is the grading system?",
    #     "Tell me about final year projects",
    #     "How do I withdraw from a course?"
    # ]
    
    # try:
    #     results = pipeline.batch_query(test_questions, top_k=3)
    #     print(f"\n   ✓ Processed {len(results)} queries")
        
    #     for i, result in enumerate(results, 1):
    #         print(f"\n   Query {i}: {result['question']}")
    #         print(f"   Answer preview: {result['answer'][:100]}...")
    # except Exception as e:
    #     print(f"   ⚠️  Batch query failed: {e}")
    
    # # Test 4: Quality evaluation
    # print("\n4️⃣ Testing quality evaluation...")
    # if result:
    #     metrics = pipeline.evaluate_answer_quality(result)
    #     print(f"   Quality metrics:")
    #     for key, value in metrics.items():
    #         print(f"      {key}: {value}")
    
    # print("\n" + "="*60)
    # print("✅ Pipeline tests complete!")
    # print("="*60)
    # print("\n💡 Next steps:")
    # print("   1. Test with more queries")
    # print("   2. Adjust retrieval parameters (top_k, min_similarity)")
    # print("   3. Tune prompt engineering in generate.py")
    # print("   4. Build a REST API backend (FastAPI/Flask)")
    # print("   5. Create a simple frontend")
    # print("\n💡 To test interactively, uncomment below:")
    pipeline.interactive_mode()
