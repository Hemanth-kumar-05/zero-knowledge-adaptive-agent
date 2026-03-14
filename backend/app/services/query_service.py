from app.core.rag_adapter import rag_adapter
from app.api.schemas.query import QueryRequest, QueryResponse, Source, RiskAlert
from app.db.mongo import MongoDB
from app.db.repositories.log_queries_repo import QueryLogRepository
from app.db.repositories.sessions_repo import SessionRepository
from app.db.repositories.messages_repo import MessageRepository
from app.db.repositories.users_repo import UsersRepository
from app.db.repositories.extensions_repo import ExtensionsRepository
from app.utils.context_builder import ConversationContextBuilder
from app.services.preference_extraction_service import AIPreferenceExtractor
from app.services.preference_application_service import preference_applier
from app.services.risk_prediction_service import risk_predictor
from app.services.fact_extraction_service import fact_extractor
from app.services.memory_control_service import create_memory_controller
from datetime import datetime
from bson import ObjectId
import logging
import asyncio

# Phase 3: Policy Unlearning imports (conditional)
try:
    from config import config
    if config.ENABLE_POLICY_UNLEARNING:
        from app.services.claim_detection_service import claim_detection_agent
        from app.services.contradiction_analyzer_service import contradiction_analyzer
        from app.services.evidence_extraction_service import evidence_extractor
        from app.services.trust_scoring_service import trust_scorer
        from app.db.repositories.policy_update_tickets_repo import PolicyUpdateTicketsRepository
        PHASE_3_ENABLED = True
    else:
        PHASE_3_ENABLED = False
except ImportError:
    PHASE_3_ENABLED = False

logger = logging.getLogger(__name__)

# Session limits for context window management
SESSION_SOFT_LIMIT = 20  # Suggest new session
SESSION_HARD_LIMIT = 30  # Strong warning

class QueryService:
    def __init__(self):
        self.rag_adapter = rag_adapter
        self.log_repo = None
        self.session_repo = None
        self.message_repo = None
        self.users_repo = None
        self.extension_repo = None
        self.context_builder = None
        self.preference_extractor = AIPreferenceExtractor()

    def _get_log_repo(self) -> QueryLogRepository:
        if self.log_repo is None:
            self.log_repo = QueryLogRepository(MongoDB.get_db())
        return self.log_repo

    def _get_session_repo(self) -> SessionRepository:
        if self.session_repo is None:
            self.session_repo = SessionRepository(MongoDB.get_db())
        return self.session_repo

    def _get_message_repo(self) -> MessageRepository:
        if self.message_repo is None:
            self.message_repo = MessageRepository(MongoDB.get_db())
        return self.message_repo
    
    def _get_users_repo(self) -> UsersRepository:
        if self.users_repo is None:
            self.users_repo = UsersRepository(MongoDB.get_db())
        return self.users_repo
    
    def _get_extension_repo(self) -> ExtensionsRepository:
        if self.extension_repo is None:
            self.extension_repo = ExtensionsRepository(MongoDB.get_db())
        return self.extension_repo
    
    def _get_context_builder(self) -> ConversationContextBuilder:
        if self.context_builder is None:
            # We'll pass the OpenAI client later, for now use None
            self.context_builder = ConversationContextBuilder(None)
        return self.context_builder

    async def query(self, request: QueryRequest, user_id: str = None, file_data: dict = None) -> QueryResponse | str:
        """Handle user query and return answer with sources."""
        if not request.question or not request.session_id:
            return "Invalid request"

        # Store original question for display/saving
        original_question = request.question

        # Check if session exists
        session_exists = await self._get_session_repo().session_exists(request.session_id)
        if not session_exists:
            return "Session not found. Please create a new session first."
        
        # Fetch session details to check for extension
        session = await self._get_session_repo().get_session(request.session_id)
        extension_system_prompt = None
        extension_type = None
        script_execution_result = None
        augmented_prompt = None  # For extensions - full prompt with data
        
        # If session has an extension, fetch its system prompt
        if session and session.get("extension_id"):
            extension_id = session.get("extension_id")
            extension = await self._get_extension_repo().get_extension_by_id(extension_id)
            if extension:
                extension_system_prompt = extension.get("system_prompt")
                extension_type = extension.get("extension_type", "prompt-based")
                print(f"\n🧩 EXTENSION MODE ACTIVE")
                print(f"Extension: {extension.get('name')}")
                print(f"Extension ID: {extension_id}")
                
                # Execute extension script if file was uploaded
                if file_data and extension.get("extension_type") == "script-based":
                    print(f"\n📁 FILE UPLOAD DETECTED - Executing extension script...")
                    from app.services.extension_executor import ExtensionExecutor
                    
                    executor = ExtensionExecutor(MongoDB.get_db())
                    script_result = await executor.execute_script(
                        extension=extension,
                        file_data=file_data["content"],  # Pass bytes content
                        session_id=request.session_id,
                        user_id=user_id or "anonymous"
                    )
                    
                    if script_result.get("success"):
                        script_execution_result = script_result.get("result")
                        print(f"✅ Script executed successfully")
                        print(f"Result type: {script_execution_result.get('result_type')}")
                        
                        # Build augmented prompt for LLM (don't modify request.question)
                        script_prompt = script_execution_result.get("mapping_prompt") or script_execution_result.get("prompt") or ""
                        if script_prompt:
                            augmented_prompt = f"{original_question}\n\n{script_prompt}"
                            print(f"📋 Built augmented prompt for LLM ({len(augmented_prompt)} chars)")
                    else:
                        print(f"❌ Script execution failed: {script_result.get('error')}")
                        # Return error to user
                        return QueryResponse(
                            question=original_question,
                            answer=f"Error processing file: {script_result.get('error')}",
                            sources=[],
                            refused=False,
                            session_id=request.session_id,
                            confidence="low"
                        )
        
        # Fetch conversation history for this session
        conversation_history = await self._get_message_repo().get_session_messages(request.session_id)
        print(f"\n{'='*60}")
        print(f"📚 CONVERSATION HISTORY ANALYSIS")
        print(f"{'='*60}")
        print(f"Total messages in session: {len(conversation_history)}")
        
        # Build smart context from history
        context_builder = self._get_context_builder()
        formatted_history = context_builder.build_context(conversation_history, original_question)
        
        # Get conversation metadata
        conversation_metadata = context_builder.build_system_context(conversation_history)
        
        print(f"\n📊 Context Metadata:")
        print(f"  - User messages: {conversation_metadata.get('user_messages', 0)}")
        print(f"  - Assistant messages: {conversation_metadata.get('assistant_messages', 0)}")
        print(f"  - Has context: {conversation_metadata.get('has_context', False)}")
        print(f"\n📝 Formatted history entries: {len(formatted_history)}")
        if formatted_history:
            print(f"\n🔍 History structure:")
            for i, msg in enumerate(formatted_history):
                role = msg.get('role', 'unknown')
                content_preview = msg.get('content', '')[:80] + '...' if len(msg.get('content', '')) > 80 else msg.get('content', '')
                print(f"  [{i+1}] {role}: {content_preview}")
        print(f"{'='*60}\n")

        # Fetch user preferences if authenticated
        user_preferences = []
        preference_instructions = None
        applied_preferences = []
        user_context = None  # User memory context
        
        if user_id:
            user = await self._get_users_repo().get_user_by_id(user_id)
            if user:
                user_preferences = user.get("preferences", [])
                
                # Check if we should apply preferences
                if preference_applier.should_apply_preferences(user_preferences):
                    preference_instructions = preference_applier.build_preference_instructions(
                        user_preferences
                    )
                    applied_preferences = preference_applier.get_applied_preferences_metadata(
                        user_preferences
                    )
                    
                    # logger.info(
                    #     f"🎯 Applying {len(applied_preferences)} preferences for user {user_id}"
                    # )
                
                # Build user context from stored facts
                memory_controller = create_memory_controller(self._get_users_repo())
                user_context = await memory_controller.build_user_context(user_id)
                
                # if user_context:
                    # logger.info(f"🧠 User context built from memory: {len(user_context)} characters")

        # === EXTENSION DIRECT GENERATION - BYPASS RAG ===
        # Prompt-based extensions use system prompt.
        # Script-based extensions bypass RAG when script execution produced augmented prompt data.
        use_extension_direct_mode = (
            bool(extension_system_prompt) or
            (extension_type == "script-based" and bool(augmented_prompt))
        )

        if use_extension_direct_mode:
            print(f"\n🎯 EXTENSION DIRECT GENERATION - Bypassing RAG pipeline")
            
            # Import Generator
            from rag.generate import Generator
            generator = Generator()
            
            # For script-based: use augmented prompt (with data)
            # For prompt-based: use original question
            query_for_llm = original_question
            context_for_llm = augmented_prompt or ""

            # If script-based extension has no explicit system prompt, provide a safe default.
            effective_extension_prompt = extension_system_prompt
            if extension_type == "script-based" and not effective_extension_prompt:
                effective_extension_prompt = (
                    "You are a specialized extension assistant. "
                    "Use ONLY the structured data provided in the context to answer the user's task. "
                    "Do not call external knowledge. "
                    "Return a clear, direct result in markdown."
                )

            print(f"Using Generator directly with {'script-augmented' if augmented_prompt else 'original'} prompt")

            # Script-based helpers may need a larger completion budget for full JSON payloads.
            extension_max_tokens = 4096
            if extension_type == "script-based":
                extension_max_tokens = 8192
            
            # Generate response directly (no RAG retrieval needed)
            try:
                answer = generator.generate(
                    query=query_for_llm,
                    context=context_for_llm,
                    conversation_history=formatted_history,
                    preference_instructions=None,  # Extensions don't use preferences
                    user_context=None,
                    extension_system_prompt=effective_extension_prompt,
                    max_tokens=extension_max_tokens
                )
            except Exception as ext_gen_err:
                print(f"⚠️ Extension generation failed with max_tokens={extension_max_tokens}: {ext_gen_err}")
                print("↩️ Retrying extension generation with max_tokens=4096")
                answer = generator.generate(
                    query=query_for_llm,
                    context=context_for_llm,
                    conversation_history=formatted_history,
                    preference_instructions=None,
                    user_context=None,
                    extension_system_prompt=effective_extension_prompt,
                    max_tokens=4096
                )
            
            # Build response without sources
            rag_response = {
                "answer": answer,
                "sources": [],
                "refused": False,
                "confidence": "high"
            }
            print(f"✅ Extension response generated ({len(answer)} chars)")
        else:
            # Standard RAG pipeline for regular queries
            # Pass history, preferences, and user context to RAG adapter
            rag_response = self.rag_adapter.query(
                original_question,  # Use original question for RAG
                conversation_history=formatted_history,
                conversation_metadata=conversation_metadata,
                user_preferences=user_preferences,
                preference_instructions=preference_instructions,
                user_context=user_context
            )

        print("🔍 RAG response received")
        print(f"🔍 RAG Response keys: {rag_response.keys()}")
        print(f"🔍 RAG Response sources count: {len(rag_response.get('sources', []))}")
        print(f"🔍 RAG Response refused: {rag_response.get('refused', False)}")

        # === PHASE 3: POLICY CLAIM DETECTION ===
        # Detect policy change claims and request proof from user
        policy_claim_detected = None
        print(f"🔍 Phase 3 check: ENABLED={PHASE_3_ENABLED}, user_id={user_id}")
        if PHASE_3_ENABLED and user_id:
            print(f"🔍 Phase 3 claim detection starting for user {user_id}")
            logger.info(f"🔍 Phase 3 claim detection starting for user {user_id}")
            try:
                policy_claim_detected = await self._detect_policy_claims(
                    user_id=user_id,
                    session_id=request.session_id,
                    user_message=original_question,
                    rag_sources=rag_response.get("sources", [])
                )
            except Exception as e:
                print(f"❌ Error in claim detection: {e}")
                logger.error(f"❌ Error in claim detection: {e}", exc_info=True)
        elif PHASE_3_ENABLED and not user_id:
            print(f"⚠️  Phase 3 enabled but no user_id - skipping")
            logger.warning(f"⚠️  Phase 3 enabled but no user_id - skipping policy claim detection")
        else:
            print(f"Phase 3 skipped (enabled={PHASE_3_ENABLED}, user_id={user_id})")
            logger.debug(f"Phase 3 claim detection skipped (enabled={PHASE_3_ENABLED}, user_id={user_id})")

        log_data = {
            "session_id": request.session_id,  # Will be converted to ObjectId in repository
            "user_id": user_id,  # Add user_id to query logs
            "question": original_question,
            "answer": rag_response.get("answer", ""),
            "sources": rag_response.get("sources", []),
            "refused": rag_response.get("refused", False),
            "timestamp": datetime.now(),
            "retrieval_time_ms": rag_response.get("retrieval_time_ms"),
            "generation_time_ms": rag_response.get("generation_time_ms"),
            "total_time_ms": rag_response.get("total_time_ms"),
            "confidence": rag_response.get("confidence")
        }

        # === RISK DETECTION (BEFORE saving messages) ===
        risk_alerts_list = []
        try:
            if user_id and conversation_history:
                message_count = len(conversation_history)
                simple_greetings = ["hi", "hey", "hello", "bye", "goodbye", "thanks", "thank you", "ok", "okay"]
                is_simple = original_question.lower().strip() in simple_greetings
                
                should_analyze = (
                    message_count >= 2 and 
                    not is_simple and
                    len(original_question.split()) > 2
                )
                
                if should_analyze:
                    detected_risks = await risk_predictor.analyze_risks(
                        conversation_history=conversation_history,
                        current_question=original_question
                    )
                    
                    if detected_risks:
                        risk_alerts_list = [
                            {
                                "risk_type": risk.risk_type,
                                "severity": risk.severity,
                                "confidence": risk.confidence,
                                "message": risk.message,
                                "indicators": risk.indicators,
                                "detected_at": risk.detected_at.isoformat()
                            } for risk in detected_risks
                        ]
        except Exception as e:
            logger.error(f"❌ Error in risk prediction: {e}", exc_info=True)

        try:
            user_message_metadata = {}
            if file_data:
                filename = file_data.get("filename")
                content_type = file_data.get("content_type")
                content_bytes = file_data.get("content") or b""
                file_kind = "other"
                lower_name = (filename or "").lower()

                if content_type and content_type.startswith("image/"):
                    file_kind = "image"
                elif content_type == "application/pdf" or lower_name.endswith(".pdf"):
                    file_kind = "pdf"
                elif (content_type and content_type.startswith("text/")) or lower_name.endswith((".json", ".txt", ".md", ".py", ".js", ".jsx", ".ts", ".tsx", ".sql", ".yaml", ".yml")):
                    file_kind = "text"

                persisted_file = {
                    "name": filename,
                    "type": content_type,
                    "size": len(content_bytes),
                    "preview_kind": file_kind,
                }

                # Persist text snippet for text-like uploads so preview remains useful after reload.
                if file_kind == "text" and len(content_bytes) <= 1024 * 1024:
                    try:
                        raw_text = content_bytes.decode("utf-8", errors="replace")
                        persisted_file["preview_text"] = raw_text[:25000]
                        persisted_file["preview_text_truncated"] = len(raw_text) > 25000
                    except Exception:
                        pass

                user_message_metadata["file"] = persisted_file

            # Save user message
            await self._get_message_repo().create_message(
                session_id=request.session_id,
                role="user",
                content=original_question,
                user_id=user_id,  # Add user_id to messages
                metadata=user_message_metadata
            )
            await self._get_session_repo().increment_message_count(request.session_id)
            
            # Save assistant message with metadata, applied preferences, and risk alerts
            metadata = {
                "sources": rag_response.get("sources", []),
                "confidence": rag_response.get("confidence"),
                "retrieval_time_ms": rag_response.get("retrieval_time_ms"),
                "generation_time_ms": rag_response.get("generation_time_ms"),
                "total_time_ms": rag_response.get("total_time_ms"),
                "risk_alerts": risk_alerts_list if risk_alerts_list else []
            }
            await self._get_message_repo().create_message(
                session_id=request.session_id,
                role="assistant",
                content=rag_response.get("answer", ""),
                metadata=metadata,
                user_id=user_id,  # Add user_id to messages
                applied_preferences=applied_preferences  # Store which preferences were applied
            )
            await self._get_session_repo().increment_message_count(request.session_id)
            
            # Log query for analytics
            await self._get_log_repo().log_query(log_data)
            
            # Update session (timestamp and message_count incremented by message creation)
            await self._get_session_repo().update_session_timestamp(request.session_id)
            
            # Extract preferences and facts if user is authenticated
            if user_id:
                messages = await self._get_message_repo().get_session_messages(request.session_id)
                message_count = len(messages)
                
                # Skip on very short messages (greetings, single words)
                last_user_msg = original_question
                is_substantial = len(last_user_msg.split()) > 2  # At least 3 words
                
                if is_substantial:
                    # Preferences: Extract every 2 messages or in first 4 messages
                    should_extract_preferences = (message_count % 2 == 0 or message_count <= 4)
                    
                    # Facts: Extract every 5 messages or in first 4 messages
                    should_extract_facts = (message_count % 5 == 0 or message_count <= 4)
                    
                    if should_extract_preferences or should_extract_facts:
                        logger.info(f"🔍 Running extractions at message {message_count} (prefs: {should_extract_preferences}, facts: {should_extract_facts})")
                        
                        if should_extract_preferences:
                            await self._extract_preferences_if_needed(request.session_id, user_id)
                        
                        if should_extract_facts:
                            await self._extract_facts_if_needed(request.session_id, user_id)
        except Exception as e:
            logger.error(f"❌ Error logging query: {e}", exc_info=True)

        sources = [
            Source(
                doc_id=src["doc_id"],
                section=src["section"],
                similarity=src["similarity"],
                confidence=src["confidence"]
            ) for src in rag_response.get("sources", [])
        ]

        # Analyze risks from conversation patterns (optimized - only every 3 messages after 3rd message)
        risk_alerts_list = None
        session_warning = None
        
        # Check session message count for context window management
        if conversation_history:
            msg_count = len(conversation_history)
            
            if msg_count >= SESSION_HARD_LIMIT:
                session_warning = {
                    "severity": "high",
                    "message": f"Your conversation has {msg_count} messages. For optimal performance and relevance, we strongly recommend starting a new session.",
                    "current_count": msg_count,
                    "suggestion": "Start a new session to maintain conversation quality and avoid context overload."
                }
                logger.warning(f"⚠️ Session {request.session_id} reached hard limit: {msg_count} messages")
            
            elif msg_count >= SESSION_SOFT_LIMIT:
                session_warning = {
                    "severity": "medium",
                    "message": f"You have {msg_count} messages in this session. Consider starting a new session for better performance.",
                    "current_count": msg_count,
                    "suggestion": "Starting a new session helps maintain conversation clarity and system performance."
                }
                logger.info(f"ℹ️ Session {request.session_id} approaching limit: {msg_count} messages")
        
        # Convert risk alert dicts to RiskAlert objects for response
        risk_alerts_for_response = None
        if risk_alerts_list:
            risk_alerts_for_response = [
                RiskAlert(
                    risk_type=alert["risk_type"],
                    severity=alert["severity"],
                    confidence=alert["confidence"],
                    message=alert["message"],
                    indicators=alert["indicators"],
                    detected_at=alert["detected_at"]
                ) for alert in risk_alerts_list
            ]
        
        # Prepare policy claim data if detected
        policy_claim_response = None
        if policy_claim_detected:
            from app.api.schemas.query import PolicyClaimDetected
            policy_claim_response = PolicyClaimDetected(
                claim_detected=True,
                ticket_id_pending=policy_claim_detected["ticket_id_pending"],
                claim_text=policy_claim_detected["claim_text"],
                claim_type=policy_claim_detected["claim_type"],
                confidence_level=policy_claim_detected["confidence_level"],
                trust_score=policy_claim_detected["trust_score"],
                requires_proof=True,
                message_to_user=(
                    f"I noticed you mentioned a policy change. To help verify this information, "
                    f"could you please upload supporting documents (circular, official notice, or screenshot)? "
                    f"This will help our team  review and update the policy database if needed."
                )
            )
        
        response = QueryResponse(
            question=rag_response.get("question", original_question),
            answer=rag_response.get("answer", "Error generating answer."),
            sources=sources if sources else None,
            refused=rag_response.get("refused", False),
            session_id=request.session_id,
            confidence=rag_response.get("confidence"),
            risk_alerts=risk_alerts_for_response,
            session_limit_warning=session_warning,
            policy_claim_detected=policy_claim_response
        )

        return response if response.answer else "Error generating answer."
    
    async def _extract_preferences_if_needed(self, session_id: str, user_id: str):
        """
        Check if preferences should be extracted and perform extraction
        
        Args:
            session_id: Current session ID
            user_id: Authenticated user ID
        """
        try:
            # Get user data to check extraction settings
            user = await self._get_users_repo().get_user_by_id(user_id)
            if not user:
                return
            
            # Get current session messages to count
            messages = await self._get_message_repo().get_session_messages(session_id)
            message_count = len(messages)
            
            # Already checked in main query method - skip redundant checks
            
            logger.info(f"🔍 Extracting preferences for user {user_id} (session: {session_id})")
            
            # Get the most recent user message for source tracking
            recent_user_msg = None
            for msg in reversed(messages):
                if msg["role"] == "user":
                    recent_user_msg = msg
                    break
            
            # Format ONLY user messages for extraction to avoid analyzing assistant responses
            # Only pass last 3 USER messages for context
            user_messages = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in messages
                if msg["role"] == "user"
            ][-3:]  # Last 3 user messages only
            
            if not user_messages:
                logger.info("📊 No user messages to analyze")
                return
            
            # Extract new preferences (analyzing user messages only)
            extracted_prefs = await self.preference_extractor.extract_preferences(
                user_messages,
                min_confidence=0.80  # Stricter confidence threshold (increased from 0.75)
            )
            
            # Add source tracking to extracted preferences
            if extracted_prefs and recent_user_msg:
                for pref in extracted_prefs:
                    pref["source_session_id"] = session_id
                    pref["source_message_id"] = str(recent_user_msg.get("_id", ""))
                    pref["source_message_preview"] = recent_user_msg["content"][:100]
                    pref["extracted_from_message"] = recent_user_msg["content"]
            
            if not extracted_prefs:
                logger.info("📊 No new preferences extracted")
                return
            
            # Get existing preferences
            existing_prefs = await self._get_users_repo().get_preferences_for_extraction(user_id)
            
            # Check for conflicts before adding
            conflicting_prefs = []
            non_conflicting_prefs = []
            
            for new_pref in extracted_prefs:
                conflict = self.preference_extractor.detect_conflicts(existing_prefs, new_pref)
                if conflict:
                    logger.info(
                        f"⚠️  Conflict detected: {new_pref['category']}.{new_pref['value']} "
                        f"conflicts with existing {conflict['value']}"
                    )
                    # Update the existing preference instead of adding a new one
                    if new_pref.get("confidence", 0) > conflict.get("confidence", 0):
                        # New preference has higher confidence, update the old one
                        for existing in existing_prefs:
                            if existing.get("key") == conflict.get("key"):
                                existing["value"] = new_pref["value"]
                                existing["confidence"] = new_pref["confidence"]
                                existing["explanation"] = new_pref.get("explanation", "")
                                existing["updated_at"] = new_pref.get("extracted_at")
                                logger.info(
                                    f"🔄 Updated conflicting preference with higher confidence value"
                                )
                                break
                    conflicting_prefs.append(new_pref)
                else:
                    non_conflicting_prefs.append(new_pref)
            
            # Only merge non-conflicting preferences
            if non_conflicting_prefs:
                merged_prefs = self.preference_extractor.merge_preferences(
                    existing_prefs,
                    non_conflicting_prefs,
                    max_preferences=50
                )
            else:
                # If all preferences conflicted, just use existing (possibly updated)
                merged_prefs = existing_prefs
            
            # Update user preferences in database
            success = await self._get_users_repo().update_preferences_bulk(
                user_id, merged_prefs
            )
            
            if success:
                logger.info(
                    f"✅ Updated preferences for user {user_id}: "
                    f"{len(merged_prefs)} total preferences "
                    f"({len(non_conflicting_prefs)} new, {len(conflicting_prefs)} conflicts resolved)"
                )                
                # Mark the message as having extracted preferences
                if recent_user_msg and extracted_prefs:
                    message_id = str(recent_user_msg.get("_id", ""))
                    if message_id:
                        await self._get_message_repo().collection.update_one(
                            {"_id": ObjectId(message_id)},
                            {"$set": {"extracted_preferences": extracted_prefs}}
                        )            
            # Increment interaction count
            await self._get_users_repo().increment_interactions(user_id)
            
        except Exception as e:
            logger.error(f"❌ Error in preference extraction: {e}", exc_info=True)
    
    async def _extract_facts_if_needed(self, session_id: str, user_id: str):
        """
        Extract factual information about user from conversation
        
        Args:
            session_id: Current session ID
            user_id: Authenticated user ID
        """
        try:
            # Get user data to check memory settings
            user = await self._get_users_repo().get_user_by_id(user_id)
            if not user:
                return
            
            memory_settings = user.get("memory_settings", {})
            if not memory_settings.get("auto_extract_enabled", True):
                logger.info(f"📊 Fact extraction disabled for user {user_id}")
                return
            
            # Get session messages
            messages = await self._get_message_repo().get_session_messages(session_id)
            if not messages:
                return
            
            # Get last user message
            last_user_message = None
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    last_user_message = msg.get("content", "")
                    break
            
            if not last_user_message:
                return
            
            # Check for explicit memory commands
            memory_command = fact_extractor.detect_memory_commands(last_user_message)
            if memory_command:
                logger.info(f"🧠 Detected memory command: {memory_command['command']}")
                return
            
            # Already checked in main query method - proceed with extraction
            logger.info(f"🧠 Extracting facts for user {user_id}")
            
            # Format recent messages for extraction
            formatted_msgs = [
                {"role": msg.get("role", "user"), "content": msg.get("content", "")}
                for msg in messages[-5:]  # Last 5 messages for context
            ]
            
            # Extract facts
            extracted_facts = await fact_extractor.extract_facts(
                messages=formatted_msgs,
                current_message=last_user_message,
                min_confidence=0.70
            )
            
            if not extracted_facts:
                logger.info("📊 No new facts extracted")
                return
            
            # Store facts using memory controller
            memory_controller = create_memory_controller(self._get_users_repo())
            
            counts = await memory_controller.store_facts_bulk(
                user_id,
                extracted_facts,
                require_confirmation=memory_settings.get("require_confirmation", True)
            )
            
            logger.info(
                f"✅ Fact extraction completed for user {user_id}: "
                f"{counts['stored']} new, {counts['updated']} updated, "
                f"{counts['failed']} failed"
            )
            
        except Exception as e:
            logger.error(f"❌ Error in fact extraction: {e}", exc_info=True)
    
    async def _should_analyze_for_claims(self, user_message: str) -> bool:
        """
        Use LLM to quickly determine if the message warrants policy claim detection.
        Returns True if the message appears to be making a policy claim, False otherwise.
        """
        from groq import Groq
        import os
        
        try:
            client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            
            prompt = f"""You are a classifier that determines if a user message contains a policy claim or update.

A policy claim would be statements like:
- "The new circular says CA is 50%"
- "According to the latest update, internships are now mandatory"
- "The policy changed - ESE is now 60%"
- "I heard that the add/drop deadline is extended"

NOT policy claims:
- Simple greetings: "Hi", "Hello", "Thanks"
- Questions about existing policy: "What is the CA weightage?"
- Acknowledgments: "Ok", "Got it", "Thanks"
- Short responses: "Yes", "No", "Sure"

User message: "{user_message}"

Does this message contain a policy claim or update? Answer with ONLY "yes" or "no"."""

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=10
            )
            
            answer = response.choices[0].message.content.strip().lower()
            print(f"🤖 LLM decision for '{user_message[:50]}': {answer}")
            
            return "yes" in answer
            
        except Exception as e:
            print(f"❌ Error in LLM pre-check: {e}")
            # On error, default to analyzing (safer to check than miss)
            return True
    
    async def _detect_policy_claims(
        self,
        user_id: str,
        session_id: str,
        user_message: str,
        rag_sources: list
    ):
        """
        Phase 3: Detect policy change claims and create review tickets
        Runs as non-blocking background task
        
        Args:
            user_id: Authenticated user ID
            session_id: Current session ID
            user_message: User's message to analyze
            rag_sources: Retrieved chunks from RAG
        """
        try:
            if not PHASE_3_ENABLED:
                print("📊 Phase 3 not enabled, returning")
                return
            
            # Use LLM to quickly check if message warrants claim detection
            should_analyze = await self._should_analyze_for_claims(user_message)
            if not should_analyze:
                print(f"📊 LLM decided to skip claim detection for: '{user_message[:50]}'")
                return
            
            print(f"🔍 Phase 3: Analyzing message for policy claims")
            logger.info(f"🔍 Phase 3: Analyzing message for policy claims")
            
            # Step 1: Detect claim
            claim_result = await claim_detection_agent.detect_claim(user_message)
            
            if not claim_result or claim_result.get("claim_detected") is False:
                logger.info("📊 No policy claim detected")
                return
            
            claim_confidence = claim_result.get("confidence", 0.0)
            claim_type = claim_result.get("claim_type", "unknown")
            
            logger.info(
                f"🎯 Policy claim detected: {claim_type} "
                f"(confidence: {claim_confidence:.2f})"
            )
            
            # Step 2: Extract evidence FIRST (to check if user provides proof)
            evidence_result = await evidence_extractor.extract_evidence(
                claim_text=claim_result.get("claim_text", user_message),
                user_message=user_message
            )
            
            evidence_strength = evidence_result.get("evidence_strength", "weak")
            # Collect evidence fields that have values
            evidence_fields = {
                k: v for k, v in evidence_result.items()
                if k in ["circular_number", "date_mentioned", "policy_reference"] and v is not None
            }
            
            has_evidence = len(evidence_fields) > 0
            
            logger.info(
                f"📄 Evidence extracted: strength={evidence_strength}, "
                f"fields={list(evidence_fields.keys())}"
            )
            
            # Step 3: Analyze contradictions with retrieved chunks
            print(f"🔍 About to call contradiction_analyzer with {len(rag_sources)} rag_sources")
            contradiction_result = await contradiction_analyzer.analyze_contradiction(
                claim_text=user_message,
                retrieved_chunks=rag_sources
            )
            print(f"🔍 Contradiction analysis returned: {contradiction_result.get('contradictions_found')}")
            
            contradictions_found = contradiction_result.get("contradictions_found", False)
            overall_confidence = contradiction_result.get("overall_confidence", 0.0)
            affected_chunks = contradiction_result.get("affected_chunks", [])
            print(f"🔍 Affected chunks count: {len(affected_chunks)}")
            
            # If no contradictions found BUT user provides evidence (circular, date),
            # still proceed as it might be a new policy we don't know about yet
            if not contradictions_found and not has_evidence:
                logger.info("✅ No contradictions or evidence found - skipping claim")
                return
            
            if contradictions_found:
                logger.info(
                    f"⚠️  Contradictions detected: {len(affected_chunks)} chunks affected "
                    f"(confidence: {overall_confidence:.2f})"
                )
            elif has_evidence:
                logger.info(
                    f"📋 No contradictions detected, but user provided evidence - "
                    f"treating as potential new/updated policy"
                )
            
            # Step 4: Compute trust score (not async)
            trust_result = trust_scorer.compute_trust_score(
                claim_confidence=claim_confidence,
                contradiction_confidence=contradiction_result.get("overall_confidence", 0.0),
                evidence_strength=evidence_result.get("evidence_strength", "weak"),
                user_history=None  # Future enhancement
            )
            
            trust_score = trust_result.get("trust_score", 0.0)
            requires_approval = trust_result.get("requires_approval", True)
            confidence_level = trust_result.get("confidence_level", "low")
            
            logger.info(
                f"⭐ Trust score computed: {trust_score:.2f} "
                f"(level: {confidence_level}, requires_approval: {requires_approval})"
            )
            
            # Step 5: Store claim data for proof upload (don't auto-create ticket)
            # Return claim detection data to prompt user for proof upload
            claim_data = {
                "claim_detected": True,
                "ticket_id_pending": f"PENDING-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                "user_id": user_id,
                "session_id": session_id,
                "claim_text": user_message,
                "claim_type": claim_type,
                "claim_confidence": claim_confidence,
                "confidence_level": confidence_level,
                "extracted_fields": evidence_result,
                "affected_chunks": affected_chunks,
                "trust_score": trust_score,
                "requires_proof": True,  # Always require proof
                "claim_detection_result": claim_result,
                "contradiction_analysis": contradiction_result
            }
            
            # Store in session metadata for later retrieval
            session_repo = SessionRepository(MongoDB.get_db())
            await session_repo.update_metadata(
                session_id, 
                {"pending_policy_claim": claim_data}
            )
            
            logger.info(
                f"🔔 Policy claim detected - requesting proof from user "
                f"(trust: {trust_score:.2f}, confidence: {confidence_level})"
            )
            
            return claim_data
            
        except Exception as e:
            logger.error(f"❌ Error in policy claim detection: {e}", exc_info=True)
            return None
    
# Global query service instance
query_service = QueryService()