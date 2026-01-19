# Phase 1 – Canonical RAG Agent (Zero-Knowledge Baseline)

This phase implements a strict Retrieval-Augmented Generation (RAG) pipeline
using only canonical academic documents as the knowledge source.

## Scope
- Build a RAG pipeline over canonical markdown documents
- Expose the agent via a REST backend
- Provide a simple ChatGPT-like frontend
- Maintain chat history for UX only (not learning)
- Enforce zero-knowledge behavior

## Core Constraints (IMPORTANT)
- The agent must answer ONLY from retrieved documents
- If retrieval returns no relevant chunks, the agent must explicitly refuse
- No personalization or long-term memory in Phase 1
- Chat history must NOT be treated as memory
- No summarization or embedding of chat history
- No file uploads or tools

## Architecture
- Vector DB (Chroma): canonical document embeddings
- MongoDB: chat history and system logs
- Backend: REST API (FastAPI / Flask)
- Frontend: simple history-based chat UI

## Non-Goals (DO NOT IMPLEMENT)
- User authentication
- Multi-user memory
- Preference learning
- Knowledge correction or unlearning
- Model fine-tuning

Phase 1 exists to establish a measurable zero-knowledge baseline.
Subsequent phases will introduce memory isolation and controlled learning.
