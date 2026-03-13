# Phase 3: Policy Unlearning - Implementation Checklist

## 🎯 Overview
Track implementation progress for Phase 3 Policy Unlearning feature.
**Critical:** All changes must be non-disruptive to existing Phase 2 functionality.

---

## ✅ Milestone 1: Foundation & Data Models

### Configuration
- [ ] Add `ENABLE_POLICY_UNLEARNING` flag to `config.py` (default: `false`)
- [ ] Add `POLICY_UPDATE_APPROVAL_REQUIRED` flag to `config.py` (default: `true`)
- [ ] Add confidence threshold configs (`LOW`, `MEDIUM`, `HIGH`)
- [ ] Test: Verify flags load correctly from environment

### Database Repositories
- [ ] Create `policy_documents_repo.py`
  - [ ] Implement `create_policy_document()`
  - [ ] Implement `get_policy_document_by_id()`
  - [ ] Implement `get_active_version()`
  - [ ] Implement `update_policy_status()`
  - [ ] Implement `create_indexes()` for performance
  - [ ] Unit tests for repository methods

- [ ] Create `policy_update_tickets_repo.py`
  - [ ] Implement `create_ticket()`
  - [ ] Implement `get_ticket_by_id()`
  - [ ] Implement `list_tickets(status, limit, offset)`
  - [ ] Implement `update_ticket_status()`
  - [ ] Implement `add_review_decision()`
  - [ ] Implement `create_indexes()`
  - [ ] Unit tests for repository methods

- [ ] Create `policy_change_audit_repo.py`
  - [ ] Implement `write_audit_record()`
  - [ ] Implement `get_audit_by_id()`
  - [ ] Implement `get_audit_history(doc_id, limit)`
  - [ ] Implement `get_latest_audit_for_rollback()`
  - [ ] Implement `create_indexes()`
  - [ ] Unit tests for repository methods

### Database Initialization
- [ ] Update `backend/app/db/mongo.py` to create Phase 3 collections on startup
- [ ] Add index creation for new collections in lifespan handler
- [ ] Test: Verify collections created successfully
- [ ] Test: Verify indexes created for query performance

---

## ✅ Milestone 2: Detection Layer (AI Services)

### Claim Detection Agent
- [ ] Create `claim_detection_service.py`
- [ ] Implement `detect_claim(user_message, context)` method
- [ ] Build prompt template for claim classification
- [ ] Implement confidence scoring logic
- [ ] Handle edge cases (empty message, non-English, etc.)
- [ ] Unit tests with mock LLM responses
- [ ] Integration test with real Gemini API

### Contradiction Analyzer
- [ ] Create `contradiction_analyzer_service.py`
- [ ] Implement `analyze_contradiction(claim, chunks)` method
- [ ] Build prompt for contradiction detection
- [ ] Calculate per-chunk contradiction scores
- [ ] Aggregate overall contradiction confidence
- [ ] Unit tests with sample claims and chunks
- [ ] Integration test with real scenarios

### Evidence Extraction
- [ ] Create `evidence_extraction_service.py`
- [ ] Implement `extract_evidence(claim_text, user_message)` method
- [ ] Build extraction prompts for:
  - [ ] Circular numbers (e.g., "Circular 2024-03")
  - [ ] Dates (e.g., "January 15, 2025")
  - [ ] Policy references (e.g., "Section 4.2")
  - [ ] Specific claims (normalize text)
- [ ] Implement evidence strength classification
- [ ] Unit tests for each evidence type
- [ ] Test: Handle missing evidence gracefully

### Trust Scoring
- [ ] Create `trust_scoring_service.py`
- [ ] Implement `compute_trust_score()` method
- [ ] Define scoring algorithm:
  - [ ] Claim confidence weight
  - [ ] Contradiction score weight
  - [ ] Evidence strength weight
  - [ ] Optional: User reputation weight (future)
- [ ] Map trust score to confidence level (low/medium/high)
- [ ] Determine approval requirements by level
- [ ] Unit tests for scoring edge cases
- [ ] Test: Consistent scoring for same inputs

---

## ✅ Milestone 3: Governance Layer (Admin APIs)

### API Schemas
- [ ] Create `policy_update.py` in `api/schemas/`
- [ ] Define `PolicyUpdateTicketCreate` schema
- [ ] Define `PolicyUpdateTicketResponse` schema
- [ ] Define `ApprovalRequest` schema
- [ ] Define `RejectionRequest` schema
- [ ] Define `RollbackRequest` schema
- [ ] Add validation rules for all schemas

### API Routes
- [ ] Create `policy_updates.py` in `api/routes/`
- [ ] Implement `POST /api/v1/policy-updates/tickets` (internal)
- [ ] Implement `GET /api/v1/policy-updates/tickets?status={status}`
- [ ] Implement `GET /api/v1/policy-updates/tickets/{ticket_id}`
- [ ] Implement `POST /api/v1/policy-updates/tickets/{ticket_id}/approve`
- [ ] Implement `POST /api/v1/policy-updates/tickets/{ticket_id}/reject`
- [ ] Add authentication middleware (admin/faculty only)
- [ ] Add authorization checks (role-based)
- [ ] API documentation with examples

### Integration with Main App
- [ ] Register policy_updates router in `main.py`
- [ ] Add route prefix `/api/v1/policy-updates`
- [ ] Test: Verify routes accessible when authenticated
- [ ] Test: Verify 401/403 for unauthorized access

---

## ✅ Milestone 4: Unlearning Executor

### Chunk Deprecation Service
- [ ] Create `chunk_deprecation_service.py`
- [ ] Implement `deprecate_chunks(chunk_ids, reason, audit_id)` method
- [ ] Update ChromaDB chunk metadata:
  - [ ] Set `status = "deprecated"`
  - [ ] Add `deprecated_at` timestamp
  - [ ] Add `deprecated_by` audit_id reference
- [ ] Handle batch operations efficiently
- [ ] Error handling for missing chunks
- [ ] Unit tests with mock ChromaDB
- [ ] Integration test with real ChromaDB

### Policy Re-embedding Service
- [ ] Create `policy_reembedding_service.py`
- [ ] Implement `reingest_policy(text, doc_id, version, metadata)` method
- [ ] Chunk new policy text (reuse chunking logic)
- [ ] Generate embeddings via existing embedder
- [ ] Add chunks to ChromaDB with `status="active"`
- [ ] Update policy_documents collection
- [ ] Implement as background job (async)
- [ ] Job status tracking (queued/processing/completed/failed)
- [ ] Unit tests for chunking and embedding
- [ ] Integration test: Full re-ingest workflow

### Active Version Retrieval Filter
- [ ] Create `version_aware_retrieval.py` in `core/`
- [ ] Implement `VersionAwareRetriever` wrapper class
- [ ] Add `active_only` parameter to filter logic
- [ ] Test: Filter correctly excludes deprecated chunks
- [ ] Test: Backward compatible (default active_only=True)

### Extend Existing Retriever
- [ ] Modify `rag/retrieve.py`:
  - [ ] Add `active_only` parameter to `retrieve()` (default: True)
  - [ ] Implement status filtering on results
  - [ ] Maintain backward compatibility
- [ ] Test: Existing code works without changes
- [ ] Test: New parameter works correctly

### Approved Update Executor
- [ ] Create `policy_update_executor_service.py`
- [ ] Implement `execute_approved_update(ticket_id, reviewer_id)` method
- [ ] Orchestrate full workflow:
  - [ ] Fetch ticket details
  - [ ] Call chunk deprecation service
  - [ ] Queue re-embedding job
  - [ ] Update policy documents collection
  - [ ] Write audit trail
  - [ ] Update ticket status to "implemented"
- [ ] Handle partial failures gracefully
- [ ] Implement transaction-like semantics (compensating actions)
- [ ] Unit tests for each workflow step
- [ ] Integration test: End-to-end update

---

## ✅ Milestone 5: Audit & Rollback

### Audit Trail Writer
- [ ] Create `audit_trail_service.py`
- [ ] Implement `write_change_audit()` method
- [ ] Generate unique audit IDs
- [ ] Record all change metadata
- [ ] Link to policy update ticket
- [ ] Store rollback pointer
- [ ] Unit tests for audit record creation
- [ ] Test: Verify audit records queryable

### Rollback Manager
- [ ] Create `rollback_manager_service.py`
- [ ] Implement `rollback_to_version(audit_id, executed_by, reason)` method
- [ ] Rollback workflow:
  - [ ] Fetch original audit record
  - [ ] Re-activate deprecated chunks
  - [ ] Deprecate new chunks
  - [ ] Update version pointers
  - [ ] Write rollback audit record
- [ ] Safety checks before rollback
- [ ] Unit tests for rollback logic
- [ ] Integration test: Full rollback scenario

### Rollback API Endpoints
- [ ] Add `POST /api/v1/policy-updates/rollback/{audit_id}` route
- [ ] Add `GET /api/v1/policy-updates/audit?doc_id={doc_id}` route
- [ ] Implement confirmation mechanism (safety)
- [ ] Add admin-only authorization
- [ ] API documentation with warnings

---

## ✅ Milestone 6: Integration (Non-Disruptive)

### Query Flow Integration
- [ ] Modify `backend/app/services/query_service.py`
- [ ] Add feature flag check at beginning
- [ ] Import Phase 3 services conditionally
- [ ] Add claim detection call AFTER retrieval:
  ```python
  if config.ENABLE_POLICY_UNLEARNING:
      try:
          # Detection logic (non-blocking)
      except Exception as e:
          logger.error(f"Phase 3 failed: {e}")
          # Continue normally
  ```
- [ ] Implement `_create_policy_update_ticket()` helper method
- [ ] Launch ticket creation as async task (fire-and-forget)
- [ ] Test: Query flow unchanged when flag disabled
- [ ] Test: Query flow functional when flag enabled
- [ ] Test: Failure in Phase 3 doesn't break query

### Metadata Extension for Chunks
- [ ] Modify `rag/ingest.py`:
  - [ ] Add `status`, `version`, timestamps to chunk metadata
  - [ ] Maintain backward compatibility (defaults)
- [ ] Re-run ingestion script to update existing chunks (optional)
- [ ] Test: New metadata included in embeddings
- [ ] Test: Old chunks without new fields still work

### Background Job Queue (Optional)
- [ ] Research background job libraries (Celery, RQ, etc.)
- [ ] Set up job queue infrastructure (if not exists)
- [ ] Move re-embedding to background job
- [ ] Add job status monitoring endpoint
- [ ] Test: Jobs execute asynchronously
- [ ] Test: Job failures logged and retried

---

## ✅ Milestone 7: Testing & Validation

### Regression Tests
- [ ] Create `tests/phase3/test_regression.py`
- [ ] Test suite: All Phase 2 functionality unchanged
  - [ ] Query endpoint returns same results
  - [ ] Retrieval returns same results
  - [ ] Message persistence unchanged
  - [ ] Session management unchanged
  - [ ] User preferences still applied
- [ ] Run with `ENABLE_POLICY_UNLEARNING=false`
- [ ] 100% pass rate required before deployment

### Unit Tests
- [ ] Claim detection service: 90%+ coverage
- [ ] Contradiction analyzer: 90%+ coverage
- [ ] Evidence extraction: 90%+ coverage
- [ ] Trust scoring: 100% coverage (deterministic)
- [ ] All repositories: 90%+ coverage
- [ ] Executor services: 85%+ coverage

### Integration Tests
- [ ] End-to-end ticket creation workflow
- [ ] Approval → execution → audit workflow
- [ ] Rejection workflow
- [ ] Rollback workflow
- [ ] Concurrent update protection
- [ ] Failed re-embedding recovery

### Performance Tests
- [ ] Query latency unchanged (flag disabled)
- [ ] Query latency acceptable (flag enabled, +50ms max)
- [ ] Claim detection latency < 200ms
- [ ] Ticket creation async (non-blocking)
- [ ] Re-embedding throughput > 100 chunks/min

### Manual QA Scenarios
- [ ] Genuine policy change claim → ticket created
- [ ] False claim → low confidence ticket
- [ ] Admin approves ticket → update executes
- [ ] Admin rejects ticket → no update
- [ ] Rollback after bad update → system restored
- [ ] Check retrieval excludes deprecated chunks
- [ ] Check audit trail complete and accurate

---

## ✅ Milestone 8: Documentation

### Code Documentation
- [ ] Docstrings for all new services
- [ ] Inline comments for complex logic
- [ ] Type hints for all functions
- [ ] README for Phase 3 architecture

### API Documentation
- [ ] OpenAPI/Swagger docs for new endpoints
- [ ] Request/response examples
- [ ] Error codes and messages
- [ ] Authentication requirements

### Operational Documentation
- [ ] How to enable/disable feature flag
- [ ] How to review and approve tickets
- [ ] How to perform rollback
- [ ] Monitoring and alerting guide
- [ ] Troubleshooting common issues

### Developer Documentation
- [ ] Phase 3 architecture diagram
- [ ] Data flow diagrams
- [ ] Database schema documentation
- [ ] Deployment checklist
- [ ] Testing guide

---

## ✅ Milestone 9: Deployment Preparation

### Configuration Management
- [ ] Add Phase 3 env vars to `.env.example`
- [ ] Document all configuration options
- [ ] Set production defaults (flag disabled)
- [ ] Prepare staging configuration

### Database Migration Plan
- [ ] Migration script for new collections
- [ ] Index creation scripts
- [ ] Rollback plan for migrations
- [ ] Test migrations on staging data

### Deployment Checklist
- [ ] Code review completed
- [ ] All tests passing (100%)
- [ ] Performance benchmarks met
- [ ] Security review completed
- [ ] Documentation up to date
- [ ] Feature flag verified (disabled)
- [ ] Monitoring configured
- [ ] Rollback plan documented

### Staged Rollout Plan
- [ ] **Stage 1:** Deploy with flag disabled (Day 0)
- [ ] **Stage 2:** Monitor for 48 hours (Day 0-2)
- [ ] **Stage 3:** Enable in staging environment (Day 3)
- [ ] **Stage 4:** QA testing in staging (Day 3-7)
- [ ] **Stage 5:** Enable for 10% users in prod (Day 8)
- [ ] **Stage 6:** Monitor metrics for 1 week (Day 8-15)
- [ ] **Stage 7:** Increase to 50% users (Day 16)
- [ ] **Stage 8:** Full rollout (Day 23)

---

## ✅ Milestone 10: Monitoring & Maintenance

### Metrics Dashboard
- [ ] Claim detection rate metric
- [ ] False positive rate tracking
- [ ] Ticket approval rate
- [ ] Average update latency
- [ ] Rollback frequency (should be rare)
- [ ] Query latency comparison (with/without Phase 3)

### Alerts Configuration
- [ ] Alert: Claim detection service down
- [ ] Alert: Re-embedding job failures > 5%
- [ ] Alert: Audit trail write failures
- [ ] Alert: Spike in policy update tickets (>10/hour)
- [ ] Alert: Query latency degradation (>100ms increase)

### Logging
- [ ] Structured logging for all Phase 3 services
- [ ] Log levels appropriate (INFO, WARN, ERROR)
- [ ] Sensitive data not logged
- [ ] Log aggregation configured

### Maintenance Runbook
- [ ] How to investigate failed updates
- [ ] How to manually deprecate chunks
- [ ] How to re-run embedding jobs
- [ ] How to fix corrupted audit trail
- [ ] Emergency disable procedure

---

## 📊 Progress Summary

| Milestone | Status | Completion |
|-----------|--------|------------|
| 1. Foundation & Data Models | ⬜ Not Started | 0% |
| 2. Detection Layer | ⬜ Not Started | 0% |
| 3. Governance Layer | ⬜ Not Started | 0% |
| 4. Unlearning Executor | ⬜ Not Started | 0% |
| 5. Audit & Rollback | ⬜ Not Started | 0% |
| 6. Integration | ⬜ Not Started | 0% |
| 7. Testing & Validation | ⬜ Not Started | 0% |
| 8. Documentation | ⬜ Not Started | 0% |
| 9. Deployment Prep | ⬜ Not Started | 0% |
| 10. Monitoring | ⬜ Not Started | 0% |
| **Overall** | **⬜ Not Started** | **0%** |

---

## 🚨 Critical Success Factors

1. **Non-Disruption:** Phase 2 functionality must remain 100% unchanged
2. **Feature Flag:** All Phase 3 code behind `ENABLE_POLICY_UNLEARNING` flag
3. **Fail-Safe:** Phase 3 failures must not break main query flow
4. **Human Governance:** No automatic policy updates without approval
5. **Audit Trail:** Every change fully logged and reversible
6. **Performance:** Query latency increase < 50ms with flag enabled
7. **Testing:** 100% regression test pass rate before deployment

---

## 📝 Notes & Issues

- [ ] Decision: Which background job queue library to use?
- [ ] Decision: How to handle concurrent updates to same policy?
- [ ] Question: Should we version policies at document or chunk level?
- [ ] Risk: Re-embedding large policies may take significant time
- [ ] Mitigation: Implement chunked/incremental re-embedding

---

**Last Updated:** March 3, 2026  
**Status:** Ready to Begin Implementation  
**Next Action:** Start Milestone 1 (Foundation & Data Models)
