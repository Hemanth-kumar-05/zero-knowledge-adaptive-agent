# RAG Chatbot Frontend

A clean ChatGPT-like interface for the RAG chatbot backend.

## Quick Start

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open http://localhost:3000 in your browser

## Features

- Clean ChatGPT-like UI
- Session management
- Real-time chat
- Message history
- Source citations
- Responsive design

## API Endpoints Used

- `POST /api/sessions/` - Create new session
- `GET /api/sessions/` - Get all sessions
- `GET /api/sessions/{session_id}` - Get specific session
- `GET /api/sessions/{session_id}/messages` - Get session messages
- `POST /api/query` - Send query and get response

## Tech Stack

- React 18
- Vite
- Axios
- CSS3
