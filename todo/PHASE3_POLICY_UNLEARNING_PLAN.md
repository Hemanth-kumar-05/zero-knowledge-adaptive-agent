# Phase 3 - Policy Unlearning Implementation Plan

## ⚠️ Non-Disruptive Implementation Guarantee

**CRITICAL PRINCIPLE**: All Phase 3 changes are ADDITIVE ONLY. The existing Phase 2 implementation remains untouched and operational.

### Safety Mechanisms
- Feature flag: `ENABLE_POLICY_UNLEARNING` (default: `false`)
- Versioned policy chunks (never overwrite active data)
- Separate API endpoints (no changes to existing `/api/v1/query`)
- Isolated services (no modifications to existing services)
- Backward-compatible data model extensions
- Optional integration points in query flow

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    User Query (Student)                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│            Existing Query Flow (UNCHANGED)                   │
│  /api/v1/query → QueryService → RAG Pipeline                │
└────────────┬───────────────────────────────┬────────────────┘
             │                               │
             │ (if flag enabled)             │
             ↓                               ↓
    ┌────────────────┐              ┌──────────────────┐
    │ Claim Detection│              │  Active Version  │
    │     Agent      │              │  Retrieval Filter│
    └────────┬───────┘              └──────────────────┘
             │                               │
             ↓                               │
    ┌────────────────┐                      │
    │  Contradiction │                      │
    │    Analyzer    │                      │
    └────────┬───────┘                      │
             │                               │
             ↓                               │
    ┌────────────────┐                      │
    │    Evidence    │                      │
    │   Extraction   │                      │
    └────────┬───────┘                      │
             │                               │
             ↓                               │
    ┌────────────────┐                      │
    │ Trust Scoring  │                      │
    └────────┬───────┘                      │
             │                               │
             ↓                               │
    ┌────────────────┐                      │
    │  Create Update │                      │
    │     Ticket     │                      │
    └────────────────┘                      │
                                            │
┌───────────────────────────────────────────┼────────────────┐
│              Admin/Faculty Portal         │                │
├───────────────────────────────────────────┘                │
│  Review Queue → Approve/Reject Decision                    │
│  ↓                                                          │
│  Approved Update Executor                                  │
│  ├─ Mark old chunks as deprecated                          │
│  ├─ Ingest new policy text                                 │
│  ├─ Re-embed (background job)                              │
│  ├─ Update active version pointer                          │
│  └─ Write audit trail                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Milestones

### **Milestone 1: Foundation & Data Models**

#### 1.1 Configuration Extensions
**Files to modify:**
- `config.py` - Add Phase 3 feature flags

**New configuration:**
```python
# ============================================
# Phase 3 - Policy Unlearning (Feature Flags)
# ============================================
ENABLE_POLICY_UNLEARNING = os.getenv("ENABLE_POLICY_UNLEARNING", "false").lower() == "true"
POLICY_UPDATE_APPROVAL_REQUIRED = os.getenv("POLICY_UPDATE_APPROVAL_REQUIRED", "true").lower() == "true"

# Confidence thresholds for auto-categorization
POLICY_CLAIM_CONFIDENCE_LOW = float(os.getenv("POLICY_CLAIM_CONFIDENCE_LOW", "0.3"))
POLICY_CLAIM_CONFIDENCE_MEDIUM = float(os.getenv("POLICY_CLAIM_CONFIDENCE_MEDIUM", "0.6"))
POLICY_CLAIM_CONFIDENCE_HIGH = float(os.getenv("POLICY_CLAIM_CONFIDENCE_HIGH", "0.85"))
```

#### 1.2 Database Collections
**New repositories to create:**
- `backend/app/db/repositories/policy_documents_repo.py`
- `backend/app/db/repositories/policy_update_tickets_repo.py`
- `backend/app/db/repositories/policy_change_audit_repo.py`

**Schema: policy_documents**
```python
{
    "_id": ObjectId,
    "doc_id": str,  # e.g., "ncie_exam_registration_process"
    "version": int,  # Incremental version number
    "status": str,  # "active", "deprecated", "draft"
    "effective_date": datetime,
    "supersedes": str | None,  # Previous version doc_id
    "source_reference": str,  # Circular number, policy doc reference
    "created_at": datetime,
    "created_by": str,  # user_id of faculty/admin
    "chunk_ids": List[str],  # ChromaDB document IDs
    "metadata": {
        "filename": str,
        "section": str,
        "original_text": str
    }
}
```

**Schema: policy_update_tickets**
```python
{
    "_id": ObjectId,
    "ticket_id": str,  # Unique ticket identifier
    "created_at": datetime,
    "updated_at": datetime,
    "status": str,  # "pending", "approved", "rejected", "implemented"
    
    # User claim information
    "user_id": str,
    "session_id": str,
    "claim_text": str,  # Original user message
    "query_context": str,  # Original query that triggered detection
    
    # Detection results
    "claim_type": str,  # "policy_outdated", "contradiction", "missing_info"
    "confidence_score": float,  # 0.0 to 1.0
    "confidence_level": str,  # "low", "medium", "high"
    
    # Evidence
    "extracted_fields": {
        "circular_number": str | None,
        "date_mentioned": str | None,
        "policy_reference": str | None,
        "specific_claim": str
    },
    "affected_chunks": List[{
        "chunk_id": str,
        "doc_id": str,
        "current_text": str,
        "contradiction_score": float
    }],
    
    # Review
    "reviewer_id": str | None,
    "reviewed_at": datetime | None,
    "decision": str | None,  # "approve", "reject"
    "reviewer_notes": str | None,
    
    # Implementation
    "implemented_at": datetime | None,
    "audit_trail_id": str | None
}
```

**Schema: policy_change_audit**
```python
{
    "_id": ObjectId,
    "audit_id": str,
    "ticket_id": str,
    "timestamp": datetime,
    
    # What changed
    "change_type": str,  # "deprecate", "add", "update", "rollback"
    "old_chunk_ids": List[str],
    "new_chunk_ids": List[str],
    "affected_doc_ids": List[str],
    
    # Who and why
    "executed_by": str,  # user_id of faculty/admin
    "reason": str,
    "source_reference": str | None,
    
    # Technical details
    "embedding_job_id": str | None,
    "rollback_pointer": str | None,  # Previous audit_id for rollback
    
    # Verification
    "verification_status": str,  # "pending", "verified", "failed"
    "verification_notes": str | None
}
```

---

### **Milestone 2: Detection Layer (AI Services)**

#### 2.1 Claim Detection Agent
**New file:** `backend/app/services/claim_detection_service.py`

**Purpose:** Detect if user message contains policy change claim

**Interface:**
```python
class ClaimDetectionAgent:
    async def detect_claim(
        self, 
        user_message: str, 
        conversation_context: List[dict]
    ) -> dict:
        """
        Returns:
        {
            "is_claim_detected": bool,
            "claim_type": str,  # "policy_outdated", "contradiction", "missing_info", "none"
            "confidence": float,
            "reasoning": str
        }
        """
```

**Detection Patterns:**
- "This rule is outdated"
- "But the new circular says..."
- "I heard this changed recently"
- "The deadline was modified"
- Contradiction signals in user message vs retrieved context

#### 2.2 Contradiction Analyzer
**New file:** `backend/app/services/contradiction_analyzer_service.py`

**Purpose:** Compare user claim against retrieved policy chunks

**Interface:**
```python
class ContradictionAnalyzer:
    async def analyze_contradiction(
        self,
        claim_text: str,
        retrieved_chunks: List[dict]
    ) -> dict:
        """
        Returns:
        {
            "contradictions_found": bool,
            "affected_chunks": List[{
                "chunk_id": str,
                "contradiction_score": float,
                "specific_conflict": str
            }],
            "overall_confidence": float
        }
        """
```

#### 2.3 Evidence Extraction
**New file:** `backend/app/services/evidence_extraction_service.py`

**Purpose:** Extract structured evidence from claim

**Interface:**
```python
class EvidenceExtractor:
    async def extract_evidence(
        self,
        claim_text: str,
        user_message: str
    ) -> dict:
        """
        Returns:
        {
            "circular_number": str | None,
            "date_mentioned": str | None,
            "policy_reference": str | None,
            "specific_claim": str,
            "evidence_strength": str  # "weak", "moderate", "strong"
        }
        """
```

#### 2.4 Trust Scoring
**New file:** `backend/app/services/trust_scoring_service.py`

**Purpose:** Compute overall confidence for update request

**Interface:**
```python
class TrustScorer:
    def compute_trust_score(
        self,
        claim_confidence: float,
        contradiction_confidence: float,
        evidence_strength: str,
        user_history: dict | None = None
    ) -> dict:
        """
        Returns:
        {
            "trust_score": float,
            "confidence_level": str,  # "low", "medium", "high"
            "requires_approval": bool,
            "reasoning": str
        }
        """
```

---

### **Milestone 3: Governance Layer (Admin APIs)**

#### 3.1 Policy Update Ticket Creation
**New file:** `backend/app/api/routes/policy_updates.py`

**Endpoints:**
```python
# Auto-created by detection layer (internal)
POST /api/v1/policy-updates/tickets

# List pending tickets (admin/faculty)
GET /api/v1/policy-updates/tickets?status=pending

# Get ticket details
GET /api/v1/policy-updates/tickets/{ticket_id}

# Approve ticket
POST /api/v1/policy-updates/tickets/{ticket_id}/approve
Body: {
    "reviewer_notes": str,
    "source_reference": str | None
}

# Reject ticket
POST /api/v1/policy-updates/tickets/{ticket_id}/reject
Body: {
    "reviewer_notes": str,
    "reason": str
}
```

#### 3.2 Admin Schema Definitions
**New file:** `backend/app/api/schemas/policy_update.py`

```python
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PolicyUpdateTicketCreate(BaseModel):
    user_id: str
    session_id: str
    claim_text: str
    query_context: str
    claim_type: str
    confidence_score: float
    extracted_fields: dict
    affected_chunks: List[dict]

class PolicyUpdateTicketResponse(BaseModel):
    ticket_id: str
    status: str
    created_at: datetime
    confidence_level: str
    claim_text: str
    # ... more fields

class ApprovalRequest(BaseModel):
    reviewer_notes: Optional[str] = None
    source_reference: Optional[str] = None

class RejectionRequest(BaseModel):
    reviewer_notes: str
    reason: str
```

---

### **Milestone 4: Unlearning Executor**

#### 4.1 Chunk Deprecation Service
**New file:** `backend/app/services/chunk_deprecation_service.py`

**Purpose:** Mark old chunks as deprecated in ChromaDB

**Interface:**
```python
class ChunkDeprecator:
    async def deprecate_chunks(
        self,
        chunk_ids: List[str],
        reason: str,
        audit_id: str
    ) -> dict:
        """
        Updates metadata in ChromaDB:
        - status: "active" → "deprecated"
        - deprecated_at: datetime
        - deprecated_by: audit_id
        
        Returns:
        {
            "deprecated_count": int,
            "failed_chunks": List[str]
        }
        """
```

**Implementation Note:** This extends `rag/retrieve.py` with update capabilities.

#### 4.2 Policy Re-embedding Service
**New file:** `backend/app/services/policy_reembedding_service.py`

**Purpose:** Create new embeddings for updated policy text

**Interface:**
```python
class PolicyReembedder:
    async def reingest_policy(
        self,
        new_policy_text: str,
        doc_id: str,
        version: int,
        metadata: dict
    ) -> dict:
        """
        Background job that:
        1. Chunks new policy text
        2. Generates embeddings
        3. Adds to ChromaDB with status="active"
        4. Updates policy_documents collection
        
        Returns:
        {
            "job_id": str,
            "new_chunk_ids": List[str],
            "status": str  # "queued", "processing", "completed", "failed"
        }
        """
```

#### 4.3 Active Version Retrieval Filter
**New file:** `backend/app/core/version_aware_retrieval.py`

**Purpose:** Filter retrieval to only active chunks

**Interface:**
```python
class VersionAwareRetriever:
    def __init__(self, base_retriever):
        self.base_retriever = base_retriever
    
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.3,
        include_deprecated: bool = False
    ) -> List[dict]:
        """
        Wraps existing retriever with version filtering.
        Default: only returns chunks with status="active"
        """
```

**Integration Point:** `rag/retrieve.py` - Add optional filtering

#### 4.4 Approved Update Executor
**New file:** `backend/app/services/policy_update_executor_service.py`

**Purpose:** Orchestrate full update workflow

**Interface:**
```python
class PolicyUpdateExecutor:
    async def execute_approved_update(
        self,
        ticket_id: str,
        reviewer_id: str,
        source_reference: str | None
    ) -> dict:
        """
        Full workflow:
        1. Fetch ticket details
        2. Deprecate old chunks
        3. Queue re-embedding job
        4. Update policy_documents collection
        5. Write audit trail
        6. Update ticket status
        
        Returns:
        {
            "success": bool,
            "audit_id": str,
            "new_version": int,
            "message": str
        }
        """
```

---

### **Milestone 5: Audit & Rollback**

#### 5.1 Audit Trail Writer
**New file:** `backend/app/services/audit_trail_service.py`

**Interface:**
```python
class AuditTrailWriter:
    async def write_change_audit(
        self,
        ticket_id: str,
        change_type: str,
        old_chunk_ids: List[str],
        new_chunk_ids: List[str],
        executed_by: str,
        reason: str
    ) -> str:
        """
        Returns: audit_id
        """
```

#### 5.2 Rollback Manager
**New file:** `backend/app/services/rollback_manager_service.py`

**Interface:**
```python
class RollbackManager:
    async def rollback_to_version(
        self,
        audit_id: str,
        executed_by: str,
        reason: str
    ) -> dict:
        """
        1. Fetch audit trail
        2. Re-activate old chunks
        3. Deprecate new chunks
        4. Update version pointers
        5. Write rollback audit
        
        Returns:
        {
            "success": bool,
            "restored_version": int,
            "rollback_audit_id": str
        }
        """
```

**Endpoints:**
```python
# In policy_updates.py
POST /api/v1/policy-updates/rollback/{audit_id}
Body: {
    "reason": str,
    "confirmation": str  # Safety check
}

# Get audit history
GET /api/v1/policy-updates/audit?doc_id={doc_id}&limit=50
```

---

### **Milestone 6: Integration (Non-Disruptive)**

#### 6.1 Optional Query Flow Integration
**File to modify:** `backend/app/services/query_service.py`

**Integration Strategy:**
```python
# In QueryService.query() method
# Add AFTER retrieval but BEFORE response generation

# ========== PHASE 3 INTEGRATION (OPTIONAL) ==========
if config.ENABLE_POLICY_UNLEARNING:
    try:
        claim_detection_result = await claim_detector.detect_claim(
            user_message=request.question,
            conversation_context=conversation_history
        )
        
        if claim_detection_result["is_claim_detected"]:
            # Async fire-and-forget ticket creation
            asyncio.create_task(
                self._create_policy_update_ticket(
                    user_id=user_id,
                    session_id=request.session_id,
                    claim_detection=claim_detection_result,
                    retrieved_chunks=rag_results.get("sources", [])
                )
            )
    except Exception as e:
        logger.error(f"Phase 3 claim detection failed: {e}")
        # Continue with normal flow (fail gracefully)
# ====================================================
```

**Key Properties:**
- Wrapped in feature flag check
- Try-except for fail-safe behavior
- Async task (non-blocking)
- No impact on normal response path

#### 6.2 Version-Aware Retrieval Integration
**File to modify:** `rag/retrieve.py`

**Add filtering capability:**
```python
def retrieve(
    self,
    query: str,
    top_k: int = 5,
    min_similarity: float = 0.3,
    active_only: bool = True  # NEW PARAMETER
) -> List[Dict]:
    """
    If active_only=True, filter results to status="active"
    Default: True (backward compatible)
    """
    results = self.index.search(
        query,
        top_k=top_k,
        min_similarity=min_similarity,
        embedder=self.embedder
    )
    
    # NEW: Filter by status if requested
    if active_only:
        results = [
            r for r in results 
            if r.get("metadata", {}).get("status", "active") == "active"
        ]
    
    return results
```

#### 6.3 Metadata Extension for Chunks
**File to modify:** `rag/ingest.py`

**Extend chunk metadata:**
```python
chunk_metadata = {
    'type': 'canonical_knowledge',
    'doc_id': doc_id,
    'section': section,
    'text': chunk_text.strip(),
    'confidence': 1.0,
    'active': True,
    
    # NEW: Phase 3 version tracking
    'status': 'active',  # "active", "deprecated", "draft"
    'version': 1,
    'created_at': datetime.now().isoformat(),
    'updated_at': datetime.now().isoformat(),
    'supersedes': None
}
```

**Note:** Existing chunks without these fields default to `status="active"` (backward compatible).

---

## File Structure Summary

```
backend/app/
├── api/
│   ├── routes/
│   │   ├── policy_updates.py          # NEW
│   │   └── ... (existing unchanged)
│   └── schemas/
│       ├── policy_update.py           # NEW
│       └── ... (existing unchanged)
│
├── core/
│   ├── version_aware_retrieval.py     # NEW
│   └── ... (existing unchanged)
│
├── db/
│   └── repositories/
│       ├── policy_documents_repo.py              # NEW
│       ├── policy_update_tickets_repo.py         # NEW
│       ├── policy_change_audit_repo.py           # NEW
│       └── ... (existing unchanged)
│
└── services/
    ├── claim_detection_service.py                # NEW
    ├── contradiction_analyzer_service.py         # NEW
    ├── evidence_extraction_service.py            # NEW
    ├── trust_scoring_service.py                  # NEW
    ├── chunk_deprecation_service.py              # NEW
    ├── policy_reembedding_service.py             # NEW
    ├── policy_update_executor_service.py         # NEW
    ├── audit_trail_service.py                    # NEW
    ├── rollback_manager_service.py               # NEW
    └── ... (existing unchanged)

rag/
├── ingest.py              # MINOR EXTENSION (metadata)
├── retrieve.py            # MINOR EXTENSION (filtering)
└── ... (existing unchanged)

config.py                  # EXTENSION (new flags)
```

---

## Testing Strategy

### 1. Regression Testing
**Goal:** Ensure Phase 3 does NOT break existing functionality

**Test Suite:** `tests/phase3/test_regression.py`
```python
class TestPhase3Regression:
    """Verify existing flow unchanged when flag disabled"""
    
    async def test_query_flow_unchanged_flag_disabled(self):
        # Set ENABLE_POLICY_UNLEARNING = False
        # Run existing query tests
        # Assert: identical behavior to Phase 2
    
    async def test_retrieval_backward_compatible(self):
        # Test retrieve() with default params
        # Assert: same results as before
```

### 2. Unit Tests
- Test each service in isolation
- Mock LLM calls for speed
- Test edge cases (empty claims, malformed evidence)

### 3. Integration Tests
- End-to-end ticket creation flow
- Approval → execution → audit workflow
- Rollback scenarios

### 4. Performance Tests
- Query latency unchanged (flag disabled)
- Query latency acceptable (flag enabled)
- Re-embedding background job throughput

---

## Deployment Checklist

### Pre-Deployment
- [ ] All Phase 3 code behind feature flag
- [ ] Regression tests pass (100%)
- [ ] Feature flag `ENABLE_POLICY_UNLEARNING=false` in production config
- [ ] Database migrations ready (new collections)

### Deployment Stages
1. **Stage 1:** Deploy code with flag disabled (no behavior change)
2. **Stage 2:** Enable flag in staging environment
3. **Stage 3:** Monitor for 7 days in staging
4. **Stage 4:** Enable flag in production (gradual rollout)

### Rollback Plan
- If issues detected:
  - Set `ENABLE_POLICY_UNLEARNING=false` (instant rollback)
  - Redeploy previous codebase (if critical bug)

---

## Monitoring & Observability

### Key Metrics
- **Claim Detection Rate:** % of queries triggering detection
- **False Positive Rate:** Claims detected but rejected by human
- **Approval Rate:** % of tickets approved
- **Update Latency:** Time from approval to active in index
- **Rollback Frequency:** Number of rollbacks (should be rare)
- **Query Latency Impact:** Difference with/without Phase 3

### Alerts
- Claim detection service failures
- Re-embedding job failures
- Audit trail write failures
- Abnormal spike in policy update tickets

---

## FAQs

### Q: What happens if claim detection fails?
A: The query continues normally. Claim detection is non-blocking and fails gracefully.

### Q: Can users trigger policy updates directly?
A: No. Users can trigger ticket creation via claims, but approval is required.

### Q: What if re-embedding takes too long?
A: It runs as background job. Old chunks remain active until new ones ready.

### Q: How do we handle concurrent updates?
A: Use optimistic locking on policy documents. Reject concurrent updates to same doc.

### Q: Can we disable Phase 3 after enabling?
A: Yes. Set feature flag to `false`. System reverts to Phase 2 behavior immediately.

---

## Next Steps

1. Review this plan with team
2. Set up feature flags in config
3. Implement Milestone 1 (data models)
4. Build unit tests for each service
5. Implement Milestones 2-5 sequentially
6. Integration testing with flag enabled
7. Regression testing with flag disabled
8. Deploy to staging
9. Production rollout

---

**Document Version:** 1.0  
**Last Updated:** March 3, 2026  
**Status:** Ready for Implementation
