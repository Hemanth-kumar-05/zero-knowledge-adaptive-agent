# Zero-Knowledge Adaptive AI Agent

An academic policy assistant for Nova Crest Institute of Engineering (NCIE). The system uses Retrieval-Augmented Generation over curated policy documents, with a FastAPI backend, a React frontend, ChromaDB for policy chunks, and MongoDB for users, sessions, messages, preferences, memory facts, extensions, and policy-update workflows.

## What This App Does

- Answers academic-policy questions only from retrieved institutional documents.
- Supports multi-turn chat, source citations, and refusal when evidence is missing.
- Stores operational data in MongoDB and policy chunks in ChromaDB.
- Supports controlled knowledge evolution through policy-update review flows when enabled.
- Includes preference-aware and memory-aware features for authenticated users.

## Project Layout

- `backend/` - FastAPI app, API routes, services, and MongoDB access.
- `frontend/` - React + Vite user interface.
- `data/raw/` - Canonical markdown policy documents.
- `data/chroma_db/` - Persistent ChromaDB vector store.
- `embeddings/` - Chunking and embedding pipeline.
- `rag/` - Document ingestion, retrieval, and query helpers.
- `scripts/` - Maintenance utilities such as Chroma reset and visualization helpers.

## Requirements

- Python 3.10+.
- Node.js 18+.
- MongoDB connection string.
- Google Gemini API key.
- Optional: Groq, OAuth, Cloudinary, and policy-unlearning flags, depending on the features you want to enable.

## Setup

### 1. Configure the environment

Copy `.env.example` to `.env` and fill in the values for your environment.

Required values for the core app:

- `MONGODB_URI`
- `GOOGLE_API_KEY`

Useful runtime values:

- `FRONTEND_URL=http://localhost:5173`
- `BACKEND_URL=http://localhost:8000`
- `ENABLE_POLICY_UNLEARNING=true` if you want the policy update routes to be active.

### 2. Install Python dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Install frontend dependencies

```bash
cd frontend
npm install
```

## Start the Application

### Backend

Run the API from the repository root:

```bash
uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`.

Useful backend URLs:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health check: `http://localhost:8000/api/v1/health/`
- Liveness: `http://localhost:8000/api/v1/health/live`
- Readiness: `http://localhost:8000/api/v1/health/ready`

What happens on backend startup:

- MongoDB connects automatically.
- Required MongoDB indexes are created.
- If policy-unlearning is enabled, the policy update collections are initialized too.

### Frontend

Run the UI from the frontend folder:

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:5173`.

## Policy Chunk Rebuild and Database Sync

### Rebuild policy chunks

If you edit any markdown files in `data/raw/`, rebuild the ChromaDB index so the new content is embedded and searchable:

```bash
python embeddings/build_index.py
```

This reloads the markdown corpus, re-chunks the documents, recreates the `academic_docs` collection, and stores fresh embeddings in `data/chroma_db/`.

### Reset ChromaDB before a clean rebuild

If you want to delete the current vector collections first, run:

```bash
python scripts/reset_chromadb.py
```

Then rerun the build command above.

### MongoDB sync

There is no separate MongoDB sync script for the core app. MongoDB is connected and prepared automatically when the backend starts, and the readiness endpoint confirms whether MongoDB and ChromaDB are both reachable.

## Maintenance Workflow

Use this sequence when policy content changes:

1. Update the source markdown file under `data/raw/`.
2. Optionally reset ChromaDB if you want a fully clean rebuild.
3. Run `python embeddings/build_index.py`.
4. Restart the backend if it is already running.
5. Check `http://localhost:8000/api/v1/health/ready` before opening the frontend.

## API Surface

Core routes exposed by the backend include:

- `POST /api/v1/query` - Submit a policy question.
- `POST /api/v1/sessions/` - Create a session.
- `GET /api/v1/sessions/` - List sessions.
- `GET /api/v1/sessions/{id}` - Get session details.
- `GET /api/v1/sessions/{id}/messages` - Get session messages.
- `GET /api/v1/health/` - Full health check.
- `GET /api/v1/health/live` - Liveness probe.
- `GET /api/v1/health/ready` - Readiness probe.

If policy-unlearning is enabled, the backend also exposes policy update and proof-related routes under `/api/v1/policy-updates` and `/api/v1`.

## Key Capabilities

- Grounded zero-knowledge policy answering.
- Session-based conversation history.
- Source citation and confidence-oriented responses.
- Preference and memory management for authenticated users.
- Extension support for faculty and administrative workflows.
- Human-reviewed policy update handling when enabled.

## Documentation

- [Report Creation Reference](docs/REPORT_CREATION_REFERENCE.md)
- [Backend README](backend/README.md)
- [Frontend README](frontend/README.md)
- [Project Work II Report](reports/Project%20Work%20II%20-%20Report.md)

## Tech Stack

- Backend: FastAPI, Motor, MongoDB, ChromaDB.
- Frontend: React 18, Vite, Axios.
- AI/ML: Google Gemini and sentence-transformer-based embeddings.
- Storage: MongoDB for application data, ChromaDB for policy chunks.
- Language: Python 3.10+, JavaScript (ES modules).

## Contributors

- Adish Kumar S (adish9056@gmail.com)
- Hemanthkumar V (hemanthlaxvel@gmail.com)
- Jayavarshini S S (jayavarshini2805@gmail.com)
- Prateekshaa T (prateekshaa04@gmail.com)
- Praneeth M (praneethsparta@gmail.com)

## Notes

- The assistant is intended to answer from the curated academic corpus only.
- If a query is outside the indexed policy documents, the system should refuse instead of inventing an answer.
