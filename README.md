# Zero-Knowledge Adaptive Agent

Phase 1: Canonical RAG System - Academic advisor chatbot for Nova Crest Institute of Engineering (NCIE).

## 🎯 Project Overview

A Retrieval-Augmented Generation (RAG) system that provides academic policy guidance using **zero-knowledge baseline** approach - answering only from canonical documents with no external knowledge or learning.

## 🏗️ Architecture

- **Vector DB**: ChromaDB for document embeddings
- **Database**: MongoDB for chat history and logs
- **Backend**: FastAPI REST API
- **Frontend**: React + Vite ChatGPT-like interface
- **LLM**: Google Gemini (gemini-2.5-flash)
- **Embeddings**: Sentence Transformers (local)

## 📁 Project Structure

```
.
├── backend/          # FastAPI application
│   └── app/
│       ├── api/      # Routes and schemas
│       ├── core/     # RAG adapter
│       ├── db/       # MongoDB repositories
│       └── services/ # Business logic
├── frontend/         # React application
│   └── src/
│       ├── api/      # API client
│       └── components/
├── rag/              # RAG pipeline
│   ├── ingest.py     # Document processing
│   ├── retrieve.py   # Vector search
│   ├── generate.py   # LLM generation
│   └── pipeline.py   # Orchestration
├── embeddings/       # Vector index builder
├── data/
│   ├── raw/          # Canonical markdown documents
│   └── chroma_db/    # Vector database
└── docs/             # Documentation
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB (local or Atlas)
- Google Gemini API key

### 1. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and MongoDB URI

# Build vector index (one-time)
python embeddings/build_index.py

# Run backend
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at: http://localhost:5173

## 📋 Phase 1 Scope

### ✅ Implemented
- Canonical RAG over 10 academic policy documents
- Zero-knowledge constraint: answers only from retrieved context
- Vector similarity search with ChromaDB
- MongoDB chat history (UX only, not memory)
- REST API with FastAPI
- React frontend with session management
- Source citation and confidence scoring

### ❌ Not Implemented (by design)
- User authentication
- Long-term memory or personalization
- Knowledge correction or unlearning
- File uploads or external tools
- Chat history as context for learning

Phase 1 establishes a measurable zero-knowledge baseline for future enhancements.

## 🔧 Configuration

Edit `.env` file:

```env
# Required
GOOGLE_API_KEY=your_actual_api_key
MONGODB_URI=mongodb://localhost:27017

# Optional
MONGODB_DB_NAME=canonical_rag_db
API_VERSION=1.0.0
DEBUG=false
```

## 📊 API Endpoints

### Query
- `POST /api/v1/query` - Send query and get RAG response

### Sessions
- `POST /api/v1/sessions/` - Create new session
- `GET /api/v1/sessions/` - List all sessions
- `GET /api/v1/sessions/{id}` - Get session details
- `DELETE /api/v1/sessions/{id}` - Delete session

### Messages
- `GET /api/v1/sessions/{id}/messages` - Get session messages

### Health
- `GET /api/v1/health/` - System health check
- `GET /api/v1/health/live` - Liveness probe
- `GET /api/v1/health/ready` - Readiness probe

## 🧪 Testing

```bash
# Test document ingestion
python rag/ingest.py

# Test RAG pipeline
python rag/pipeline.py

# Check API health
curl http://localhost:8000/api/v1/health/
```

## 📚 Documentation

- [Phase 1 Instructions](docs/phase_1_instructions.md)
- [Backend README](backend/README.md)
- [Frontend README](frontend/README.md)

## 🎓 Academic Documents

The system contains knowledge about:
- Academic advising and mentorship
- Continuous assessment
- Course add/drop/withdrawal
- Exam registration
- Final year projects
- Grading components
- Internship evaluation
- Lab evaluation
- Project submission workflow
- Revaluation process

## 🔒 Phase 1 Constraints

The agent **strictly refuses** to answer questions outside canonical documents:

**Example refusal:**
> "I don't have information about that in the academic documents I have access to. Please contact the academic office directly or check the student portal."

This zero-knowledge baseline ensures measurable accuracy for future phases.

## 🛠️ Tech Stack

- **Backend**: FastAPI, Motor (async MongoDB), ChromaDB
- **Frontend**: React 18, Vite, Axios
- **AI/ML**: Google Gemini, Sentence Transformers
- **Database**: MongoDB, ChromaDB (SQLite)
- **Language**: Python 3.10+, JavaScript (ES6+)

## 👥 Contributors

- Hemanth Kumar (hemanthlaxvel@gmail.com)
- 22z225@psgtech.ac.in

## 📄 License

Academic Project - PSG Tech

## 🚧 Future Phases

- **Phase 2**: User-specific memory isolation
- **Phase 3**: Preference learning
- **Phase 4**: Knowledge correction and unlearning
- **Phase 5**: Multi-modal RAG with tool use

---

**Phase 1 Status**: ✅ Complete - Ready for Review
