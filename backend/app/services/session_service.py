# Session service - manages session lifecycle
from app.db.mongo import MongoDB
from app.db.repositories.sessions_repo import SessionRepository
from app.db.repositories.messages_repo import MessageRepository
from app.db.repositories.log_queries_repo import QueryLogRepository
from app.api.schemas.sessions import SessionCreateRequest, SessionCreateResponse, SessionResponse, SessionsListResponse, SessionDeleteResponse
from typing import Optional

class SessionService:
    def __init__(self):
        self.session_repo = None
        self.message_repo = None
        self.log_repo = None

    def _get_session_repo(self) -> SessionRepository:
        if self.session_repo is None:
            self.session_repo = SessionRepository(MongoDB.get_db())
        return self.session_repo

    def _get_message_repo(self) -> MessageRepository:
        if self.message_repo is None:
            self.message_repo = MessageRepository(MongoDB.get_db())
        return self.message_repo

    def _get_log_repo(self) -> QueryLogRepository:
        if self.log_repo is None:
            self.log_repo = QueryLogRepository(MongoDB.get_db())
        return self.log_repo
    
    async def increment_message_count(self, session_id: str) -> None:
        """Increment the message count for a session."""
        await self._get_session_repo().increment_message_count(session_id)

    async def create_session(self, user_id: Optional[str] = None) -> SessionCreateResponse | str:
        """Create a new chat session."""
        try:
            session_id = await self._get_session_repo().create_session(user_id)
            return SessionCreateResponse(
                session_id=session_id,
                message="Session created successfully"
            )
        except Exception as e:
            return f"Failed to create session: {str(e)}"

    async def get_session(self, session_id: str) -> SessionResponse | str:
        """Get a specific session by ID."""
        session = await self._get_session_repo().get_session(session_id)
        if not session:
            return "Session not found"
        return SessionResponse(
            id=session["_id"],
            user_id=session.get("user_id"),
            created_at=session.get("created_at"),
            updated_at=session.get("updated_at"),
            message_count=session.get("message_count", 0)
        )

    async def get_all_sessions(self) -> SessionsListResponse | str:
        """Get all sessions, optionally filtered by user_id."""
        try:
            sessions = await self._get_session_repo().get_all_sessions()
            sessions = [
                SessionResponse(
                    id=session["_id"],
                    user_id=session.get("user_id"),
                    created_at=session.get("created_at"),
                    updated_at=session.get("updated_at"),
                    message_count=session.get("message_count", 0)
                ) for session in sessions
            ]
            return SessionsListResponse(
                sessions=sessions,
                count=len(sessions)
            )
        except Exception as e:
            return f"Failed to retrieve sessions: {str(e)}"

# Global session service instance
session_service = SessionService()