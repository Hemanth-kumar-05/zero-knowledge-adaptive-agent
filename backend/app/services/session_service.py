# Session service - manages session lifecycle
from app.db.mongo import MongoDB
from app.db.repositories.sessions_repo import SessionRepository
from app.db.repositories.messages_repo import MessageRepository
from app.db.repositories.log_queries_repo import QueryLogRepository
from app.db.repositories.extensions_repo import ExtensionsRepository
from app.api.schemas.sessions import SessionCreateRequest, SessionCreateResponse, SessionResponse, SessionsListResponse, SessionDeleteResponse
from typing import Optional

class SessionService:
    def __init__(self):
        self.session_repo = None
        self.message_repo = None
        self.log_repo = None
        self.extension_repo = None

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
    
    def _get_extension_repo(self) -> ExtensionsRepository:
        if self.extension_repo is None:
            self.extension_repo = ExtensionsRepository(MongoDB.get_db())
        return self.extension_repo
    
    async def increment_message_count(self, session_id: str) -> None:
        """Increment the message count for a session."""
        await self._get_session_repo().increment_message_count(session_id)

    async def create_session(
        self, 
        user_id: Optional[str] = None,
        extension_id: Optional[str] = None
    ) -> SessionCreateResponse | str:
        """Create a new chat session, optionally with an extension."""
        try:
            extension_name = None
            extension_icon = None
            extension_welcome_message = None
            extension_input_placeholder = None
            requires_files = False
            required_file_types = None
            
            # Fetch extension details if extension_id is provided
            if extension_id:
                extension = await self._get_extension_repo().get_extension_by_id(extension_id)
                if extension:
                    extension_name = extension.get("name")
                    extension_icon = extension.get("icon")
                    extension_welcome_message = extension.get("welcome_message")
                    extension_input_placeholder = extension.get("input_placeholder")
                    required_files = extension.get("required_files", [])
                    if required_files:
                        requires_files = True
                        required_file_types = required_files
            
            session_id = await self._get_session_repo().create_session(
                user_id=user_id,
                extension_id=extension_id,
                extension_name=extension_name,
                extension_icon=extension_icon,
                extension_welcome_message=extension_welcome_message,
                extension_input_placeholder=extension_input_placeholder
            )
            
            return SessionCreateResponse(
                session_id=session_id,
                user_id=user_id,
                message="Session created successfully",
                extension_id=extension_id,
                requires_files=requires_files,
                required_file_types=required_file_types
            )
        except Exception as e:
            return f"Failed to create session: {str(e)}"

    async def get_session(self, session_id: str, requester_user_id: Optional[str] = None) -> SessionResponse | str:
        """Get a specific session by ID with optional owner check."""
        session = await self._get_session_repo().get_session(session_id)
        if not session:
            return "Session not found"

        # Enforce ownership when requester context is provided.
        if requester_user_id and session.get("user_id") != requester_user_id:
            return "Access denied"

        return SessionResponse(
            id=session["_id"],
            user_id=session.get("user_id"),
            created_at=session.get("created_at"),
            updated_at=session.get("updated_at"),
            message_count=session.get("message_count", 0),
            extension_id=session.get("extension_id"),
            extension_name=session.get("extension_name"),
            extension_icon=session.get("extension_icon"),
            extension_welcome_message=session.get("extension_welcome_message"),
            extension_input_placeholder=session.get("extension_input_placeholder")
        )

    async def get_all_sessions(self, user_id: Optional[str] = None) -> SessionsListResponse | str:
        """Get all sessions, optionally filtered by user_id."""
        try:
            sessions = await self._get_session_repo().get_all_sessions(user_id=user_id)
            sessions = [
                SessionResponse(
                    id=session["_id"],
                    user_id=session.get("user_id"),
                    created_at=session.get("created_at"),
                    updated_at=session.get("updated_at"),
                    message_count=session.get("message_count", 0),
                    extension_id=session.get("extension_id"),
                    extension_name=session.get("extension_name"),
                    extension_icon=session.get("extension_icon"),
                    extension_welcome_message=session.get("extension_welcome_message"),
                    extension_input_placeholder=session.get("extension_input_placeholder")
                ) for session in sessions
            ]
            return SessionsListResponse(
                sessions=sessions,
                count=len(sessions)
            )
        except Exception as e:
            return f"Failed to retrieve sessions: {str(e)}"

    async def delete_session(self, session_id: str, requester_user_id: Optional[str] = None) -> dict | str:
        """Delete a session and all its related data (messages and query logs)."""
        try:
            session = await self._get_session_repo().get_session(session_id)
            if not session:
                return "Session not found"

            # Enforce ownership when requester context is provided.
            if requester_user_id and session.get("user_id") != requester_user_id:
                return "Access denied"

            # Delete all messages for this session
            messages_deleted = await self._get_message_repo().delete_session_messages(session_id)
            
            # Delete all query logs for this session
            logs_deleted = await self._get_log_repo().delete_session_logs(session_id)
            
            # Delete the session itself
            session_deleted = await self._get_session_repo().delete_session(session_id)
            
            if not session_deleted:
                return "Session not found"
            
            return {
                "message": "Session deleted successfully",
                "session_id": session_id,
                "messages_deleted": messages_deleted,
                "logs_deleted": logs_deleted
            }
        except Exception as e:
            return f"Failed to delete session: {str(e)}"

# Global session service instance
session_service = SessionService()