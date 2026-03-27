# Message service - manages chat messages
from app.db.mongo import MongoDB
from app.db.repositories.messages_repo import MessageRepository
from app.db.repositories.sessions_repo import SessionRepository
from app.db.repositories.users_repo import UsersRepository
from app.services.preference_extraction_service import AIPreferenceExtractor
from typing import Optional, Literal
import logging

logger = logging.getLogger(__name__)

class MessageService:
    def __init__(self):
        self.message_repo = None
        self.session_repo = None
        self.users_repo = None
        self.preference_extractor = AIPreferenceExtractor()

    def _get_message_repo(self) -> MessageRepository:
        if self.message_repo is None:
            self.message_repo = MessageRepository(MongoDB.get_db())
        return self.message_repo

    def _get_session_repo(self) -> SessionRepository:
        if self.session_repo is None:
            self.session_repo = SessionRepository(MongoDB.get_db())
        return self.session_repo
    
    def _get_users_repo(self) -> UsersRepository:
        if self.users_repo is None:
            self.users_repo = UsersRepository(MongoDB.get_db())
        return self.users_repo

    async def create_message(
        self,
        session_id: str,
        role: Literal["user", "assistant"],
        content: str,
        metadata: Optional[dict] = None,
        user_id: Optional[str] = None
    ) -> dict:
        """Create a new message and update session. Optionally extract preferences."""
        # Check if session exists
        session_exists = await self._get_session_repo().session_exists(session_id)
        if not session_exists:
            return {"error": "Session not found"}

        try:
            message_id = await self._get_message_repo().create_message(
                session_id, role, content, metadata
            )
            # Increment session message count
            await self._get_session_repo().increment_message_count(session_id)
            
            result = {
                "message_id": message_id,
                "message": "Message created successfully"
            }
            
            # Extract preferences if this is an assistant message and user is authenticated
            if role == "assistant" and user_id:
                await self._extract_preferences_if_needed(session_id, user_id)
            
            return result
        except Exception as e:
            logger.error(f"❌ Failed to create message: {e}", exc_info=True)
            return {"error": f"Failed to create message: {str(e)}"}
    
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
            
            # Check if we should extract
            should_extract = self.preference_extractor.should_extract_preferences(
                user, message_count
            )
            
            if not should_extract:
                return
            
            logger.info(f"🔍 Extracting preferences for user {user_id} (session: {session_id})")
            
            # Format messages for extraction
            formatted_messages = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in messages[-10:]  # Last 10 messages for context
            ]
            
            # Extract new preferences
            extracted_prefs = await self.preference_extractor.extract_preferences(
                formatted_messages,
                min_confidence=0.65
            )
            
            if not extracted_prefs:
                logger.info("📊 No new preferences extracted")
                return
            
            # Get existing preferences
            existing_prefs = await self._get_users_repo().get_preferences_for_extraction(user_id)
            
            # Merge preferences
            merged_prefs = self.preference_extractor.merge_preferences(
                existing_prefs,
                extracted_prefs,
                max_preferences=50
            )
            
            # Update user preferences in database
            success = await self._get_users_repo().update_preferences_bulk(
                user_id, merged_prefs
            )
            
            if success:
                logger.info(
                    f"✅ Updated preferences for user {user_id}: "
                    f"{len(merged_prefs)} total preferences"
                )
            
            # Increment interaction count
            await self._get_users_repo().increment_interactions(user_id)
            
        except Exception as e:
            logger.error(f"❌ Error in preference extraction: {e}", exc_info=True)

    async def get_session_messages(self, session_id: str, requester_user_id: Optional[str] = None) -> dict:
        """Get all messages for a session with optional owner check."""
        # Check if session exists
        session_exists = await self._get_session_repo().session_exists(session_id)
        if not session_exists:
            return {"error": "Session not found"}

        # Enforce ownership when requester context is provided.
        if requester_user_id:
            session = await self._get_session_repo().get_session(session_id)
            if not session:
                return {"error": "Session not found"}
            if session.get("user_id") != requester_user_id:
                return {"error": "Access denied"}

        try:
            messages = await self._get_message_repo().get_session_messages(session_id)
            return {
                "messages": messages,
                "count": len(messages)
            }
        except Exception as e:
            return {"error": f"Failed to retrieve messages: {str(e)}"}

    async def update_execution_cache(
        self,
        message_id: str,
        execution_cache: dict,
        requester_user_id: Optional[str] = None,
    ) -> dict:
        """Persist execution cache metadata for an assistant message."""
        try:
            message = await self._get_message_repo().get_message_by_id(message_id)
            if not message:
                return {"error": "Message not found"}

            session = await self._get_session_repo().get_session(message["session_id"])
            if not session:
                return {"error": "Session not found"}

            if requester_user_id and session.get("user_id") != requester_user_id:
                return {"error": "Access denied"}

            success = await self._get_message_repo().update_message_metadata(
                message_id,
                {"execution_cache": execution_cache}
            )
            if not success:
                return {"error": "Failed to update execution cache"}

            return {"message": "Execution cache updated successfully"}
        except Exception as e:
            return {"error": f"Failed to update execution cache: {str(e)}"}

# Global message service instance
message_service = MessageService()
