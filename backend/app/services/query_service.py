from app.core.rag_adapter import rag_adapter
from app.api.schemas.query import QueryRequest, QueryResponse, Source, RiskAlert
from app.db.mongo import MongoDB
from app.db.repositories.log_queries_repo import QueryLogRepository
from app.db.repositories.sessions_repo import SessionRepository
from app.db.repositories.messages_repo import MessageRepository
from app.db.repositories.users_repo import UsersRepository
from app.utils.context_builder import ConversationContextBuilder
from app.services.preference_extraction_service import AIPreferenceExtractor
from app.services.preference_application_service import preference_applier
from app.services.risk_prediction_service import risk_predictor
from app.services.fact_extraction_service import fact_extractor
from app.services.memory_control_service import create_memory_controller
from datetime import datetime
from bson import ObjectId
import logging

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
    
    def _get_context_builder(self) -> ConversationContextBuilder:
        if self.context_builder is None:
            # We'll pass the OpenAI client later, for now use None
            self.context_builder = ConversationContextBuilder(None)
        return self.context_builder

    async def query(self, request: QueryRequest, user_id: str = None) -> QueryResponse | str:
        """Handle user query and return answer with sources."""
        if not request.question or not request.session_id:
            return "Invalid request"

        # Check if session exists
        session_exists = await self._get_session_repo().session_exists(request.session_id)
        if not session_exists:
            return "Session not found. Please create a new session first."
        
        # Fetch conversation history for this session
        conversation_history = await self._get_message_repo().get_session_messages(request.session_id)
        print(f"\n{'='*60}")
        print(f"📚 CONVERSATION HISTORY ANALYSIS")
        print(f"{'='*60}")
        print(f"Total messages in session: {len(conversation_history)}")
        
        # Build smart context from history
        context_builder = self._get_context_builder()
        formatted_history = context_builder.build_context(conversation_history, request.question)
        
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
                    
                    logger.info(
                        f"🎯 Applying {len(applied_preferences)} preferences for user {user_id}"
                    )
                
                # Build user context from stored facts
                memory_controller = create_memory_controller(self._get_users_repo())
                user_context = await memory_controller.build_user_context(user_id)
                
                if user_context:
                    logger.info(f"🧠 User context built from memory: {len(user_context)} characters")

        # Pass history, preferences, and user context to RAG adapter
        rag_response = self.rag_adapter.query(
            request.question,
            conversation_history=formatted_history,
            conversation_metadata=conversation_metadata,
            user_preferences=user_preferences,
            preference_instructions=preference_instructions,
            user_context=user_context
        )

        log_data = {
            "session_id": request.session_id,  # Will be converted to ObjectId in repository
            "user_id": user_id,  # Add user_id to query logs
            "question": request.question,
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
                is_simple = request.question.lower().strip() in simple_greetings
                
                should_analyze = (
                    message_count >= 2 and 
                    not is_simple and
                    len(request.question.split()) > 2
                )
                
                if should_analyze:
                    detected_risks = await risk_predictor.analyze_risks(
                        conversation_history=conversation_history,
                        current_question=request.question
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
            # Save user message
            await self._get_message_repo().create_message(
                session_id=request.session_id,
                role="user",
                content=request.question,
                user_id=user_id  # Add user_id to messages
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
                last_user_msg = request.question
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
        
        response = QueryResponse(
            question=rag_response.get("question", request.question),
            answer=rag_response.get("answer", "Error generating answer."),
            sources=sources if sources else None,
            refused=rag_response.get("refused", False),
            session_id=request.session_id,
            confidence=rag_response.get("confidence"),
            risk_alerts=risk_alerts_for_response,
            session_limit_warning=session_warning
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
    
# Global query service instance
query_service = QueryService()