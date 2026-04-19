# Report Creation Reference

This document consolidates the earlier phase-wise implementation notes in `docs/` into a single report-oriented reference for writing the final project report.

## 1. Project Identity

- Project title direction: `An Adaptive AI Agent for Academic Policy Assistance with Secure Multi-User Memory and Controlled Knowledge Evolution Using Zero-Knowledge RAG`
- Working product name used in internal docs: `AcademiQ`
- Domain: academic policy assistance for an engineering institution
- Core objective: provide grounded academic-policy answers using a zero-knowledge RAG pipeline while progressively adding authentication, personalization, extensions, identity verification, and controlled policy evolution

## 2. System Evolution Summary

### 2.1 Phase 1: Canonical Zero-Knowledge RAG

- Knowledge source: 10 canonical academic policy markdown documents
- Vector store: ChromaDB
- Backend: FastAPI
- Frontend: React/Vite chat interface
- Key behavior:
  - retrieve relevant chunks from policy documents
  - answer only from retrieved evidence
  - refuse when evidence is insufficient
  - show sources and confidence
  - maintain session history for UX
- Constraints:
  - no external knowledge
  - no personalization
  - no long-term user memory
  - no learning from chat history

### 2.2 Phase 2.1 and 2.2: Authentication and User Management

- Added Google OAuth login
- Added JWT-based authentication middleware
- Added protected routes and user-specific access
- Added user repository and user service
- Added user profile handling and role-aware flows
- Added session ownership and user-scoped data isolation
- Added better conversation handling through history-aware context construction
- Added query rewriting for context-dependent follow-up questions
- Added multi-provider LLM support in the implementation notes

### 2.3 Phase 2.3 and 2.4: Preference Extraction and Personalization

- Added AI-based extraction of user preferences from conversation
- Added preference categories, confidence scores, and merging logic
- Added lock/reset/manual preference controls
- Added preference-aware response generation
- Added preferences dashboard on frontend
- Added repository and API support for preference management

### 2.4 Advanced Adaptive Features Present in Current System

- secure multi-user memory
- memory dashboard for inspect/retain/forget behavior
- identity verification for non-admin users
- role-aware access control
- extensions system with prompt-based and script-based modes
- file-upload-assisted interactions
- policy update detection and human-reviewed policy evolution workflow

### 2.5 Phase 3: Policy Unlearning and Controlled Knowledge Evolution

- feature flag controlled
- designed to avoid disrupting baseline RAG flow
- supports:
  - policy change claim detection
  - contradiction analysis
  - evidence/proof submission
  - ticket creation and review
  - semantic matching of affected chunks
  - deprecation of outdated chunks
  - creation of updated chunks
  - audit trail and rollback-oriented governance

## 3. Final System Description for Report Use

The completed system is no longer just a question-answering bot. It is a controlled academic knowledge platform with:

- zero-knowledge RAG over institutional policy documents
- secure authentication and user-specific sessions
- adaptive preference and memory management
- AI-assisted identity verification
- extension support for faculty and admin workflows
- refusal behavior when evidence is missing
- source-grounded responses with confidence indication
- a human-in-the-loop policy update and knowledge governance pipeline

## 4. Core Architecture Notes

### 4.1 High-Level Architecture

- Frontend:
  - React/Vite
  - authenticated routing
  - role-aware pages
  - chat, preferences, memory, extensions, policy updates, admin pages
- Backend:
  - FastAPI
  - route-based modular API structure
  - service layer for query flow, preferences, memory, extensions, policy updates
- Databases:
  - ChromaDB for policy chunks and retrieval
  - MongoDB for users, sessions, messages, preferences, memories, extensions, policy tickets, and audit data

### 4.2 Chat Pipeline

- authenticate user if token is present
- load session and recent conversation context
- optionally apply user preferences and memory context
- retrieve relevant academic-policy chunks from ChromaDB
- generate grounded answer from retrieved context
- return answer with sources, confidence, and refusal behavior when needed
- if a follow-up question is too context-dependent, rewrite and retry

### 4.3 Conversation History Design

- the system uses a hybrid history-aware strategy instead of dumping the entire chat every time
- recent turns are preserved more directly
- older context can be compacted or summarized
- this improves token efficiency while preserving coherence in multi-turn academic conversations

### 4.4 Retrieval and Chunking Design

- source files are markdown documents in `data/raw`
- ingestion loads markdown files, creates chunks, and stores metadata such as:
  - `doc_id`
  - `section`
  - `status`
  - `version`
  - timestamps
- ChromaDB stores chunk embeddings and metadata
- retrieval is section-aware and policy-grounded

## 5. Authentication, User Management, and Verification

### 5.1 Authentication

- Google OAuth is the primary login mechanism
- JWT tokens manage authenticated API access
- authenticated users get isolated sessions and data scope

### 5.2 User Management

- user profiles are stored in MongoDB
- roles include at least student, faculty, and admin
- user-level access affects pages and API routes

### 5.3 Identity Verification

- non-admin users go through an AI-assisted identity-verification step
- uploaded proof is analyzed before unlocking full usage
- the system checks claimed role and identity details against uploaded proof
- this introduces a trust gate before normal usage

## 6. Personalization and Secure Multi-User Memory

### 6.1 Preference Modeling

- preferences are extracted using LLM analysis of conversation
- preferences have categories and confidence levels
- repeated signals reinforce stored preferences
- conflicts are resolved using confidence and recency logic
- users can lock, delete, or reset preferences

### 6.2 Response Personalization

- preferences are transformed into response instructions
- the response style can adapt without overriding the retrieved factual policy content
- personalization is bounded so the system remains policy-grounded

### 6.3 Memory Governance

- the broader system now includes memory inspection and control
- users can review remembered facts
- users can retain, confirm, or forget facts
- memory is isolated per user
- memory is treated as controlled personalization context, not unrestricted long-term learning

## 7. Extensions and Faculty/Admin Tools

### 7.1 Extension Model

The system supports two extension types:

- prompt-based extensions
- script-based extensions

### 7.2 Script-Based Extension Capabilities

- secure upload or inline definition of Python scripts
- AST-based validation
- execution timeout controls
- restricted execution model
- file-processing workflows for domain-specific tasks

### 7.3 Extension Examples Mentioned in Notes

- Grade Analyzer
- Question Paper Generator
- CO-PO Mapper

### 7.4 Report-Relevant Interpretation

The extension framework demonstrates that the platform can move beyond generic chat into institution-specific academic tooling controlled by faculty/admin users.

## 8. Controlled Knowledge Evolution and Policy Updates

### 8.1 Motivation

- academic policies can change
- a static RAG corpus becomes stale over time
- the system therefore supports controlled, auditable knowledge evolution

### 8.2 Workflow

- user questions or claims may indicate policy contradiction or change
- the system detects a possible claim
- the system can request supporting proof
- proof can be uploaded and linked to a ticket
- a ticket is created for review
- faculty/admin reviewers inspect evidence
- semantic search identifies impacted chunks
- old chunks can be deprecated
- updated chunks can be created
- an audit trail records what changed

### 8.3 Governance Principles

- feature-flag controlled
- human review before implementation
- auditable updates
- deprecation instead of silent overwrite
- support for rollback-oriented thinking

## 9. Dataset and Knowledge Base Notes

### 9.1 Policy Dataset

- 10 academic policy documents were used as the initial canonical corpus
- topic coverage includes:
  - academic advising
  - continuous assessment
  - course add/drop/withdrawal
  - exam registration
  - final year project guidelines
  - grading components and weightage
  - internship registration and evaluation
  - lab evaluation and internal marks
  - project submission and review flow
  - revaluation and answer script review

### 9.2 Dataset Validation Summary

- validator: Claude Sonnet 4.5
- validation date: January 22, 2026
- source: LLM-generated policy documents
- total documents: 10
- overall average score: about 93.1%
- overall verdict: approved for use in the validation note

### 9.3 Quality Dimensions Used

- structural consistency
- content completeness
- cross-reference accuracy
- terminology consistency
- logical coherence
- realism and authenticity
- RAG suitability
- data quality

### 9.4 Report Interpretation

This validation can be presented as an LLM-based pre-deployment quality assurance step for the academic-policy dataset.

## 10. Testing and Evaluation Notes

### 10.1 Baseline Question Categories

- questions the system should answer from canonical policy docs
- questions it should refuse because they are outside scope

### 10.2 Useful Evaluation Angles for Final Report

- grounded answer correctness
- refusal correctness
- retrieval relevance
- follow-up question handling
- personalized response quality
- role-aware behavior
- extension execution behavior
- policy update detection and governance workflow

### 10.3 Demo-Safe Examples

- ask about CA/ESE weightage
- ask about exam registration workflow
- ask whether CA is eligible for revaluation
- ask an out-of-scope question to show refusal
- show a contradiction claim to trigger policy update flow

## 11. Novelty and Research Contribution Notes

The older novelty notes contain both implemented and proposed ideas. For the final report, it is safer to distinguish clearly between:

- implemented contribution
- partially implemented contribution
- future-work contribution

### 11.1 Implemented/Defensible Contributions

- zero-knowledge academic RAG baseline
- secure authenticated multi-user system
- adaptive preference-aware response generation
- controlled user memory interfaces
- extension framework for domain-specific academic utilities
- human-in-the-loop policy evolution workflow
- LLM-based dataset validation

### 11.2 Proposed or Future-Oriented Ideas Mentioned in Notes

- predictive academic risk reasoning
- counterfactual what-if reasoning
- broader multi-source RAG
- web intelligence layer

These should be positioned as future work unless fully supported in the current codebase and demo.

## 12. Figures and Tables Suggested for Final Report

### 12.1 Architecture Figures

- overall system architecture
- chat request processing pipeline
- authentication and identity verification flow
- preference and memory integration flow
- extension execution architecture
- policy update and controlled knowledge evolution workflow

### 12.2 Tables

- module-wise technology stack
- functional and non-functional requirements
- user roles and permissions
- dataset document list
- validation dimensions and scores
- comparison with traditional chatbots and basic RAG systems

### 12.3 Charts

- dataset validation score chart
- response evaluation comparison chart
- feature evolution across phases
- role-based feature availability matrix

## 13. Recommended Final Report Mapping

### Chapter 1: Introduction

- project motivation
- problem with static policy access
- need for secure, adaptive academic assistance

### Chapter 2: Literature Survey

- RAG
- academic support systems
- personalization and memory
- identity verification
- human-in-the-loop governance
- LLM-based validation

### Chapter 3: System Requirements and Analysis

- functional requirements
- non-functional requirements
- user roles
- feasibility

### Chapter 4: Existing Systems and Their Disadvantages

- static policy portals
- generic chatbots
- conventional non-governed RAG systems

### Chapter 5: Proposed System Architecture

- frontend/backend/database decomposition
- high-level workflow

### Chapter 6: Core Methodologies

- ingestion and chunking
- retrieval
- grounded generation
- query rewriting
- citations/confidence/refusal

### Chapter 7: Secure Memory and Personalization

- preference extraction
- memory control
- privacy and user control

### Chapter 8: Authentication, Verification, and Governance

- OAuth
- role-based access
- identity verification

### Chapter 9: Controlled Knowledge Evolution

- policy claim detection
- proof upload
- ticket review
- chunk deprecation/update/audit

### Chapter 10: System Implementation

- frontend pages
- backend services
- API design
- integration notes

### Chapter 11: Validation and Experimentation

- dataset validation
- functional testing
- retrieval and response evaluation
- policy-update workflow testing

### Chapter 12: Results and Outcome

- achieved features
- practical significance
- reliability and governance outcomes

### Chapter 13: Conclusion and Future Work

- summarize actual implemented system
- place predictive reasoning, what-if planning, and broader hybrid intelligence into future work if not fully demoed

## 14. Notes on Old `docs/` Files

The deleted phase-wise files mainly contained:

- implementation planning notes
- setup guides for extensions
- quick references for faculty tooling
- phase-completion summaries
- UI design notes
- testing question banks

Those details have been reduced here to only the information useful for the final report.

## 15. Important Caution for Report Writing

- do not overclaim features that were only proposed in earlier novelty notes
- keep a clear distinction between:
  - implemented
  - partially implemented
  - proposed future work
- use the current codebase and demo behavior as the primary source of truth
