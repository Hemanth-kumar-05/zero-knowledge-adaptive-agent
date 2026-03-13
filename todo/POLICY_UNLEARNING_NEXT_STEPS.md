# Policy Unlearning - Next Steps (Tomorrow)

**Date Created:** March 4, 2026  
**Status:** Design Decision Needed

---

## ✅ What We've Validated Today

### 1. **Semantic Search Works Perfectly**
- ✅ Test Results: **100% recall** (found all 9 chunks with "CA 40%")
- ✅ No missed chunks (0 false negatives)
- ✅ Pure semantic approach viable (no keyword hacks needed)
- 📊 Test file: `scripts/test_semantic_policy_search.py`
- 📊 Results: `scripts/semantic_search_test_results.json`

### 2. **User Flow Working**
- ✅ User makes vague claim: "Yesterday's circular says 50%"
- ✅ LLM detects contradiction against existing policy
- ✅ System identifies affected chunks
- ✅ Ticket created with proof upload requirement
- ✅ Displays current_text to reviewer

### 3. **Technical Foundation Ready**
- ✅ ContradictionAnalyzer with Groq LLM working
- ✅ ChromaDB with 29+ chunks related to CA policy
- ✅ Semantic search can find all related chunks
- ✅ LLM can filter for true matches

---

## ❓ CRITICAL DECISION NEEDED TOMORROW

**Question:** When admin approves a policy change, what's the workflow?

### **Option A: Chunk-by-Chunk Manual Editing**
```
Process:
1. Admin sees 9 chunks with "40%"
2. Admin manually edits each one
3. System updates ChromaDB metadata

Pros: Full control, preserves exact wording
Cons: VERY tedious (9+ manual edits)
```

### **Option B: Bulk Deprecation + New Policy Text**
```
Process:
1. Admin provides NEW policy text once
2. System deprecates all 9 old chunks
3. System chunks & embeds new text
4. RAG returns new policy going forward

Pros: Fast, simple, audit trail preserved
Cons: Doesn't update source markdown files
```

### **Option C: LLM-Assisted Smart Rewrite**
```
Process:
1. Admin provides: "CA is now 50%"
2. LLM rewrites each chunk contextually
3. Admin reviews 9 suggested edits
4. Approve all OR edit individually
5. System applies changes

Pros: Best UX, preserves structure, reduces work
Cons: Most complex to implement
```

---

## 🎯 Tomorrow's Tasks

### **FIRST: Decide on Workflow**
- [ ] Review the 3 options above
- [ ] Choose: A, B, or C?
- [ ] Consider: How often will this happen? (affects complexity tradeoff)

### **THEN: Implementation Plan**

#### **If Option A (Manual):**
- [ ] Build chunk editor UI component
- [ ] API: `PATCH /api/chunks/{chunk_id}` - Update chunk text
- [ ] Re-embed edited chunks
- [ ] Update ChromaDB metadata

#### **If Option B (Deprecation):**
- [ ] Service: `semantic_policy_search_service.py`
  - Extract policy concept from ticket
  - Semantic search for all related chunks
  - LLM filter for true matches
- [ ] API: `POST /api/tickets/{ticket_id}/deprecate-chunks`
  - Mark chunks: `deprecated: true`
  - Ingest new policy text
  - Chunk & embed new text
- [ ] UI: Chunk selection interface
  - Show TP (green) vs FP (yellow)
  - Bulk select/deselect
  - New policy text input

#### **If Option C (LLM Rewrite):**
- [ ] Service: `llm_chunk_rewriter_service.py`
  - For each chunk, generate contextual rewrite
  - Return suggested edits
- [ ] API: `POST /api/tickets/{ticket_id}/generate-rewrites`
- [ ] UI: Review & approve interface
  - Diff view (old vs new)
  - Individual approve/edit
  - Bulk approve all

---

## 📝 Key Files Modified Today

1. **Backend:**
   - `backend/app/services/query_service.py` - Added LLM pre-check for claims
   - `backend/app/services/contradiction_analyzer_service.py` - JSON parser fixes
   - `rag/pipeline.py` - Always return sources with full text

2. **Frontend:**
   - Approval modal already shows affected chunks with current_text

3. **Testing:**
   - `scripts/test_semantic_policy_search.py` - Validates semantic approach

---

## 💡 Recommendations for Tomorrow

**My suggestion: Start with Option B (Deprecation)**

**Why:**
1. ✅ Simplest to implement (1-2 hours)
2. ✅ Covers 80% of use cases (value changes)
3. ✅ True "unlearning" - RAG forgets old policy
4. ✅ Preserves audit trail (old chunks not deleted)
5. ✅ Can add Option C later if needed

**Then enhance with Option C for complex changes**

---

## 🔍 Questions to Answer Tomorrow

1. **How often will policies change?**
   - Daily? → Need fast workflow (Option B)
   - Monthly? → Can afford complexity (Option C)

2. **Do source markdown files need updating?**
   - Yes → Must add document rewrite step
   - No → Deprecation is sufficient

3. **What about policy rollback?**
   - Need to un-deprecate chunks?
   - Or maintain version history?

4. **False positives handling:**
   - Auto-filter with second LLM pass?
   - Always show admin for manual review?

---

## 📞 Action Items for Next Session

1. **Decide:** A, B, or C?
2. **Design:** UI mockup for chosen workflow
3. **Implement:** Backend service for semantic search
4. **Build:** API endpoint for chunk deprecation/update
5. **Create:** Frontend component for admin review
6. **Test:** End-to-end with real CA 40%→50% change

---

**Status:** Ready to implement once design decision is made!  
**Confidence:** High - semantic search validated at 100% recall  
**Estimated Time:** 2-4 hours depending on chosen approach
