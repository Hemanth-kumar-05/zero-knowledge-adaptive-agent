# Phase 3 - TBI (To Be Implemented)

## Title
AI-Driven Policy Unlearning and Academic Extensions for Zero-Knowledge Adaptive RAG

## Context
Phase 1 established a canonical zero-knowledge RAG baseline over NCIE policy documents.
Phase 2 introduced adaptive capabilities (authentication, memory, preferences, fact extraction, query rewriting, risk signals).
Phase 3 targets controlled policy-level unlearning and faculty-focused academic extensions.

## Problem Statement
Institutional policies evolve over time. If outdated policy chunks remain active in retrieval, the assistant can provide stale answers despite correct RAG mechanics.
At the same time, user-provided claims about policy changes cannot be directly trusted due to potential mistakes or malicious inputs.

## Phase 3 Objective
Implement a safe, AI-assisted policy unlearning workflow where:
- User prompts can trigger update proposals.
- AI can detect possible policy staleness and extract structured evidence.
- Final policy updates are human-governed (faculty/admin approval).
- Only approved updates modify active knowledge in the vector store.

## Original Overall Application Workflow (Current + Planned)
1. User sends query from frontend.
2. Backend authenticates user (if token provided/required by route).
3. Session and conversation context are loaded.
4. Adaptive layer enriches request using preferences, memory context, and query rewriting.
5. RAG retrieves relevant policy chunks from vector store.
6. Generator produces grounded answer with refusal/validation safeguards.
7. Response is returned with sources, confidence, and optional warnings/risk metadata.
8. Messages and query logs are persisted.
9. Post-response extraction updates user-level adaptive metadata (Phase 2).
10. Phase 3 addition: if query indicates policy contradiction, create policy-update proposal ticket (no immediate KB update).

## Original Phase 3 Workflow (Policy Unlearning)
1. User prompt includes policy-change claim (example: "this rule is outdated").
2. Claim Detection Agent classifies prompt as potential policy update trigger.
3. Contradiction Analyzer compares claim vs currently retrieved active policy chunks.
4. Evidence Request/Extraction module captures supporting details (circular/date/reference).
5. Trust scoring computes update confidence (low/medium/high).
6. Ticket is created for faculty/admin review (human governance gate).
7. Reviewer approves/rejects request.
8. If approved:
   - old affected chunks marked deprecated,
   - new policy text ingested,
   - selective re-embedding and index patch applied,
   - active-version retrieval pointer updated.
9. Audit trail is written (who, what, when, why).
10. Rollback remains available to previous stable version.

## Scope

### In Scope
- Policy-change claim detection from user prompts.
- Contradiction analysis between claim and currently retrieved policy chunks.
- Evidence extraction and confidence scoring.
- Review ticket generation for admin/faculty approval.
- Selective chunk deprecation and re-indexing after approval.
- Versioning, audit trail, and rollback support.
- Academic extension modules (separate from main student chat UI), including:
  - CO-PO mapping support for faculty.
  - Faculty-facing academic analytics.

### Out of Scope
- Fully automatic policy overwrite without approval.
- Direct user-driven edits to active policy vectors.
- UI redesign of the main student chatbot workflow.

## Proposed Architecture (High Level)
1. User Query Intake
2. Claim Detection Agent
3. Contradiction Analyzer (query claim vs active policy chunks)
4. Evidence Request + Extraction Agent
5. Trust/Confidence Scoring
6. Review Queue (human decision)
7. Approved Update Executor (deprecate old chunks, ingest new chunks, re-embed)
8. Versioned Retrieval Filter (active version only)
9. Audit + Rollback Manager

## Non-Disruptive Integration Plan (No Impact on Current Implementation)

### Design Principle
Phase 3 features are added as parallel extension modules, not as mandatory changes to the Phase 2 request path.

### How Current Flow Stays Unchanged
- Existing `/api/v1/query` flow remains primary and fully backward-compatible.
- Current RAG retrieval/generation pipeline is not replaced.
- Existing user auth/session/message/memory behavior continues as-is.
- If Phase 3 services are unavailable, system falls back to current Phase 2 behavior.

### Isolation Strategy
- Introduce new services/endpoints for policy-update proposals and review workflow.
- Keep unlearning executor behind admin/faculty approval APIs.
- Run academic extensions (CO-PO mapping, analytics) as separate modules.
- Do not couple extension logic to main student chat response path.

### Controlled Activation
- Use feature flags:
  - `ENABLE_POLICY_UNLEARNING`
  - `ENABLE_ACADEMIC_EXTENSIONS`
- Default both flags to `false` until validated.
- Enable gradually in staging, then production.

### Data Safety
- Version policies instead of overwriting active records.
- Use `active/deprecated` status tags for chunks.
- Retrieval defaults to `active` only.
- Maintain rollback snapshots for immediate recovery.

### Performance Protection
- Execute heavy tasks (re-embedding, batch updates) asynchronously in background jobs.
- Keep query-time latency path unchanged.
- Cache active policy index pointers.

### Reliability & Rollback
- Every approved change writes audit metadata.
- On anomaly, switch retrieval pointer to previous policy version.
- One-step rollback guarantees continuity of current system behavior.

### Validation Before Enablement
- Regression suite must pass on existing Phase 2 scenarios.
- Compare baseline vs Phase 3-disabled outputs (must match).
- Only then enable Phase 3 flags.

### One-Line Assurance
Phase 3 is an additive, feature-flagged, versioned extension layer; the current Phase 2 implementation remains the default operational path.

## Safety Model
- Principle: AI proposes, humans approve, system updates.
- No update is applied without review for medium/high-impact policy changes.
- Deprecated chunks are excluded from default retrieval.
- Every update event stores who approved, what changed, and why.

## Data/Metadata Additions (Conceptual)
- policy_documents: version, status, effective_date, supersedes, source_reference.
- policy_update_tickets: claim_text, extracted_fields, confidence, evidence, decision, reviewer, decision_time.
- policy_change_audit: old_chunk_ids, new_chunk_ids, embedding_job_id, rollback_pointer.

## Academic Extensions (Phase 3)

### 1) CO-PO Mapping Support
- Faculty query -> outcome extraction -> CO-PO mapping recommendation.
- Matrix generation and export (department/faculty use).

### 2) Faculty Analytics
- Aggregated trends from queries:
  - policy confusion hotspots,
  - repeated deadline risk themes,
  - high-frequency advisory topics.

### 3) Department Workflow Add-ons
- Extension modules run as separate services/endpoints.
- No coupling required with core student-facing chat flow.

## Implementation Milestones

### Milestone 1 - Detection Layer
- Build claim detection and contradiction scoring.
- Add structured ticket creation.

### Milestone 2 - Governance Layer
- Build admin/faculty review APIs and decisions.
- Introduce confidence thresholds and escalation rules.

### Milestone 3 - Unlearning Executor
- Implement selective chunk deprecation/replacement.
- Add re-embedding and active-version retrieval filtering.

### Milestone 4 - Audit and Rollback
- Full traceability of policy changes.
- One-click rollback to previous policy version.

### Milestone 5 - Academic Extensions
- CO-PO mapping module integration.
- Faculty analytics endpoints and dashboard-ready outputs.

## Validation Plan (Final Review)
- Scenario-based tests for genuine and fake policy-update claims.
- Precision/recall for claim detection.
- False-positive rate for contradiction alerts.
- Policy update latency (review-to-activation).
- Regression checks on zero-knowledge refusal behavior.
- Extension module functional demos (CO-PO mapping + analytics).

## Expected Outcomes
- Reduced stale-policy risk in responses.
- Controlled, auditable knowledge evolution.
- Stronger institutional trust in retrieval-grounded assistants.
- Faculty value-add through outcome mapping and academic insights.

## One-Line Positioning
Phase 3 operationalizes policy-aware unlearning with human governance and adds faculty-focused academic intelligence extensions, while preserving the zero-knowledge integrity of the core assistant.
