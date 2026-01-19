# Message service - manages chat messages
from app.db.mongo import MongoDB
from app.db.repositories.messages_repo import MessageRepository
from app.db.repositories.sessions_repo import SessionRepository
from typing import Optional, Literal

class MessageService:
    def __init__(self):
        self.message_repo = None
        self.session_repo = None

    def _get_message_repo(self) -> MessageRepository:
        if self.message_repo is None:
            self.message_repo = MessageRepository(MongoDB.get_db())
        return self.message_repo

    def _get_session_repo(self) -> SessionRepository:
        if self.session_repo is None:
            self.session_repo = SessionRepository(MongoDB.get_db())
        return self.session_repo

    async def create_message(
        self,
        session_id: str,
        role: Literal["user", "assistant"],
        content: str,
        metadata: Optional[dict] = None
    ) -> dict:
        """Create a new message and update session."""
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
            
            return {
                "message_id": message_id,
                "message": "Message created successfully"
            }
        except Exception as e:
            return {"error": f"Failed to create message: {str(e)}"}

    async def get_session_messages(self, session_id: str) -> dict:
        """Get all messages for a session."""
        # Check if session exists
        session_exists = await self._get_session_repo().session_exists(session_id)
        if not session_exists:
            return {"error": "Session not found"}

        try:
            messages = await self._get_message_repo().get_session_messages(session_id)
            return {
                "messages": messages,
                "count": len(messages)
            }
        except Exception as e:
            return {"error": f"Failed to retrieve messages: {str(e)}"}

# Global message service instance
message_service = MessageService()