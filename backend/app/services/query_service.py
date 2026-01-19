from app.core.rag_adapter import rag_adapter
from app.api.schemas.query import QueryRequest, QueryResponse, Source
from app.db.mongo import MongoDB
from app.db.repositories.log_queries_repo import QueryLogRepository
from app.db.repositories.sessions_repo import SessionRepository
from app.db.repositories.messages_repo import MessageRepository
from datetime import datetime

class QueryService:
    def __init__(self):
        self.rag_adapter = rag_adapter
        self.log_repo = None
        self.session_repo = None
        self.message_repo = None

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

    async def query(self, request: QueryRequest) -> QueryResponse | str:
        """Handle user query and return answer with sources."""
        if not request.question or not request.session_id:
            return "Invalid request"

        # Check if session exists
        session_exists = await self._get_session_repo().session_exists(request.session_id)
        if not session_exists:
            return "Session not found. Please create a new session first."

        rag_response = self.rag_adapter.query(request.question)

        log_data = {
            "session_id": request.session_id,  # Will be converted to ObjectId in repository
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

        try:
            # Save user message
            await self._get_message_repo().create_message(
                session_id=request.session_id,
                role="user",
                content=request.question
            )
            await self._get_session_repo().increment_message_count(request.session_id)
            
            # Save assistant message with metadata
            metadata = {
                "sources": rag_response.get("sources", []),
                "confidence": rag_response.get("confidence"),
                "retrieval_time_ms": rag_response.get("retrieval_time_ms"),
                "generation_time_ms": rag_response.get("generation_time_ms"),
                "total_time_ms": rag_response.get("total_time_ms")
            }
            await self._get_message_repo().create_message(
                session_id=request.session_id,
                role="assistant",
                content=rag_response.get("answer", ""),
                metadata=metadata
            )
            await self._get_session_repo().increment_message_count(request.session_id)
            
            # Log query for analytics
            await self._get_log_repo().log_query(log_data)
            
            # Update session (timestamp and message_count incremented by message creation)
            await self._get_session_repo().update_session_timestamp(request.session_id)
        except Exception as e:
            print(f"Error logging query: {e}")

        sources = [
            Source(
                doc_id=src["doc_id"],
                section=src["section"],
                similarity=src["similarity"],
                confidence=src["confidence"]
            ) for src in rag_response.get("sources", [])
        ]

        response = QueryResponse(
            question=rag_response.get("question", request.question),
            answer=rag_response.get("answer", "Error generating answer."),
            sources=sources if sources else None,
            refused=rag_response.get("refused", False),
            session_id=request.session_id,
            confidence=rag_response.get("confidence")
        )

        return response if response.answer else "Error generating answer."
    
# Global query service instance
query_service = QueryService()