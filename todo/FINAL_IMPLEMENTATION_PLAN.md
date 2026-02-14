# Final Implementation Plan: Zero-Knowledge Adaptive RAG with Unlearning and Predictive Memory

**Project:** AcademiQ - Academic Advisory System  
**Timeline:** 8 Weeks (February 12 - April 8, 2026)  
**Status:** Implementation Plan  
**Scope:** Focused research contributions for graduation + publication

---

## Project Vision

**Title:** *"Zero-Knowledge Adaptive RAG with Unlearning and Predictive Memory Control for Educational Systems"*

**One-Line Summary:**  
An academic advisory chatbot that prevents hallucination, tracks knowledge changes, predicts student risks from conversation patterns, and gives users control over what it remembers.

---

## What We Have (Existing - Phase 1 & 2)

### Phase 1: Zero-Knowledge RAG Baseline ✅
- RAG pipeline over 10 academic policy documents
- Strict refusal for out-of-scope queries (89% refusal accuracy)
- Vector search with ChromaDB
- Query rewriting for failed retrievals
- Source citation and confidence scoring
- **Coverage:** 30% of academic queries

### Phase 2: User Management & Personalization ✅
- Google OAuth authentication
- User profiles with preferences (up to 50)
- AI-powered preference extraction (6 categories)
- Personalized responses (70/30 content-to-style ratio)
- Conversation history with smart context
- Preference locking and confidence scoring

**Current Capabilities:**
- Answers policy questions accurately (94% in-scope accuracy)
- Refuses out-of-scope questions appropriately
- Learns HOW users want responses (tone, style, format)
- Maintains conversation context

**Current Gaps:**
- ❌ No knowledge lifecycle management (static docs)
- ❌ No proactive assistance (only reactive)
- ❌ Doesn't remember WHO users are (only communication style)
- ❌ Can't handle policy updates cleanly

---

## What We Will Build (Phase 3 - 8 Weeks)

### Feature 1: Knowledge Unlearning & Lifecycle Management

**Problem:** Academic policies change over time. Current system has no way to update knowledge or deprecate outdated information.

**Solution:** Trackable knowledge evolution with clean unlearning.

#### Capabilities

**Document Lifecycle Operations:**
- Add new documents (admin upload)
- Update existing documents (versioning)
- Deprecate documents (soft delete)
- Delete documents (hard delete with 30-day recovery)
- Track version history

**Unlearning Process:**
- Remove embeddings from ChromaDB
- Archive old version in MongoDB
- Log what was unlearned and when
- Notify users who queried outdated info
- Zero hallucination of deprecated policies

**Conflict Prevention:**
- Only one version active at a time
- Immediate consistency after update
- No contradictory answers during transitions

#### Implementation Components

**New Service:**
```
backend/app/services/knowledge_lifecycle_service.py
- DocumentLifecycleManager class
- Methods: add_document(), update_document(), deprecate(), delete()
- Version tracking, audit logging
```

**New API Routes:**
```
POST   /api/v1/admin/documents/upload
PUT    /api/v1/admin/documents/{doc_id}/update
DELETE /api/v1/admin/documents/{doc_id}/deprecate
DELETE /api/v1/admin/documents/{doc_id}/delete
GET    /api/v1/admin/documents/history
GET    /api/v1/admin/documents/deprecated
```

**Database Schema:**
```javascript
// New collection: document_metadata
{
  doc_id: "exam_registration_v2",
  title: "Exam Registration Process",
  version: "2.0",
  status: "active | deprecated | deleted",
  created_at: ISODate,
  updated_at: ISODate,
  deprecated_at: ISODate,
  deprecated_reason: "Policy updated to 80% attendance requirement",
  chunk_ids: ["chunk_1", "chunk_2", ...],
  previous_version: "exam_registration_v1",
  next_version: null,
  updated_by: "admin_user_id"
}

// New collection: unlearning_audit
{
  event_id: ObjectId,
  event_type: "deprecate | delete | update",
  doc_id: "exam_registration_v1",
  timestamp: ISODate,
  reason: "Policy change: 75% → 80% attendance",
  affected_chunks: 45,
  admin_user: "admin_user_id"
}
```

**Frontend (Admin Panel):**
```
New admin dashboard component:
- Upload new documents
- View document list with versions
- Update/deprecate buttons
- Version history viewer
- Unlearning audit log
```

#### Evaluation Metrics

**Unlearning Effectiveness:**
- Transition time: Time from update trigger to complete deployment (<1 minute)
- Conflict rate: % of queries receiving contradictory answers (target: 0%)
- Hallucination of deprecated policies: % queries returning old info (target: 0%)
- Query accuracy maintained: Before vs. after update (target: 94% maintained)

**Test Scenarios:**
1. Update attendance policy 75% → 80%
2. Deprecate old exam registration process
3. Add new course withdrawal policy
4. Delete outdated grading scheme

---

### Feature 2: Predictive Risk Detection from Conversation Patterns

**Problem:** Current system is reactive - only answers when asked. Students may not realize they're at risk until it's too late.

**Solution:** Analyze conversation patterns to predict academic risks and provide early warnings.

#### Risk Categories (3 Types - Focused Scope)

**1. Attendance Risk**
- **Detection Signals:**
  - User asks about attendance requirements
  - Questions about medical leave, absence policies
  - Asks about attendance impact on eligibility
  - Multiple attendance-related queries in short time
  
- **Risk Scoring:**
  - Low (30-50%): 1-2 mentions within 7 days
  - Medium (51-75%): 3-4 mentions within 7 days
  - High (76-100%): 5+ mentions or urgency indicators
  
- **Proactive Response:**
  ```
  "I notice you've asked about attendance policies several times. 
  Based on the 75% requirement, you may be at risk. Consider:
  - Checking your current attendance
  - Meeting with your academic advisor
  - Exploring medical leave options if needed"
  ```

**2. Deadline Risk**
- **Detection Signals:**
  - Questions about deadline extensions
  - Asks about late submission policies
  - Questions timing-related (e.g., "Is it too late to...")
  - Calendar proximity to known deadlines
  
- **Risk Scoring:**
  - Low: General deadline questions
  - Medium: Specific deadline + anxiety indicators
  - High: <3 days to deadline + no action taken (if trackable)
  
- **Proactive Response:**
  ```
  "Exam registration closes in 3 days (March 1). I haven't 
  detected questions about hall tickets or registration yet. 
  Would you like information on the registration process?"
  ```

**3. Policy Confusion Risk**
- **Detection Signals:**
  - Same question asked 2+ times
  - Contradictory understanding shown
  - Follow-up questions suggesting confusion
  - Asks for clarification on previously explained topics
  
- **Risk Scoring:**
  - Low: Question repeated once
  - Medium: Question repeated 2 times
  - High: Question repeated 3+ times or conflicting understanding
  
- **Proactive Response:**
  ```
  "You've asked about course withdrawal 3 times. Would you like 
  to schedule a clarification session with your advisor? I can 
  help you understand the difference between drop vs. withdrawal."
  ```

#### Implementation Components

**New Service:**
```
backend/app/services/risk_prediction_service.py
- RiskPredictor class
- analyze_conversation_patterns()
- calculate_risk_scores()
- generate_risk_alerts()
```

**Risk Detection Logic:**
```python
# Pattern matching + temporal analysis
def detect_attendance_risk(messages, time_window_days=7):
    keywords = ["attendance", "75%", "absent", "medical leave"]
    recent_messages = filter_by_time_window(messages, time_window_days)
    mentions = count_keyword_mentions(recent_messages, keywords)
    
    if mentions >= 5:
        return {"type": "attendance", "severity": "high", "confidence": 0.85}
    elif mentions >= 3:
        return {"type": "attendance", "severity": "medium", "confidence": 0.70}
    elif mentions >= 1:
        return {"type": "attendance", "severity": "low", "confidence": 0.50}
    
    return None
```

**Integration Point:**
```python
# Modify: backend/app/services/query_service.py
async def query(self, request: QueryRequest, user_id: str = None):
    # ... existing RAG query logic ...
    
    # NEW: After generating response, check for risks
    if user_id and config.ENABLE_RISK_PREDICTION:
        risks = await self.risk_predictor.analyze_risks(
            user_id=user_id,
            session_id=request.session_id
        )
        
        if risks:
            response.risk_alerts = risks  # Add to response
    
    return response
```

**Frontend Display:**
```
Response with risk alert:

┌─────────────────────────────────────────┐
│ Answer: "Attendance requirement is 75%"│
├─────────────────────────────────────────┤
│ ⚠️ Risk Alert: Attendance Concern      │
│                                         │
│ You've asked about attendance multiple │
│ times. Consider meeting your advisor.   │
└─────────────────────────────────────────┘
```

#### Evaluation Metrics

**Prediction Accuracy:**
- Precision: % of predicted risks that actually occurred
- Recall: % of actual risks that were predicted
- Lead time: Average days of early warning (target: 7+ days)
- False positive rate: <20%

**User Perception:**
- Survey: "Did risk alerts help you?" (target: >70% yes)
- Survey: "Were alerts intrusive?" (target: <20% yes)
- Survey: "Would you recommend this feature?" (target: >75% yes)

**Test Methodology:**
- Synthetic conversations with risk patterns
- Manual validation by academic advisors
- User study with 10-15 students

---

### Feature 3: User-Controlled Selective Memory (Fact Extraction)

**Problem:** System only remembers HOW users want responses (preferences), not WHO they are or WHAT their situation is.

**Solution:** Extract factual information about users and let them control what gets remembered.

#### Two Memory Types

**A. Preference Memory (Already Exists - Extended)**
- Communication style, tone, detail level, format
- Auto-extracted with confidence scoring
- User can lock/unlock, delete

**B. Fact Memory (NEW)**
- User identity (name, student ID, year, major, department)
- Academic context (current courses, advisor, project supervisor)
- Situational facts (concerns, specific questions)

#### Fact Categories

**Identity Facts:**
- Name: "I'm Hemanth"
- Student ID: "My ID is 22Z225"
- Email: "My email is hemanth@psgtech.ac.in"
- Year/Semester: "I'm in 3rd year" / "I'm in semester 5"
- Major/Department: "I'm a CS student" / "I study Computer Science"

**Academic Context:**
- Current courses: "I'm taking CS301, MA401 this semester"
- Advisor: "My advisor is Dr. Smith"
- Project supervisor: "Dr. Kumar is my project guide"
- Completed courses: "I've completed Database, OS, Networks"

**Concern Signals:**
- "I'm worried about attendance"
- "I might fail CA in CS301"
- "Confused about withdrawal process"

#### User Control Mechanisms

**Explicit Memory Commands:**
```
User: "Remember my advisor is Dr. Smith"
→ System stores: {key: "advisor", value: "Dr. Smith", retention: "permanent"}

User: "Forget my previous major"
→ System deletes: {key: "major"}

User: "Don't remember this conversation"
→ System marks: {session_id: "abc", retention: "session_only"}

User: "What do you know about me?"
→ System displays: All stored facts with sources
```

**Implicit Detection with Confirmation:**
```
User: "I'm Hemanth, 3rd year CS student"

System: "I noticed you mentioned:
         - Name: Hemanth
         - Year: 3rd year
         - Major: CS
         
         Should I remember this information?"
         
Options:
✓ Yes, remember permanently
⏱ Remember for this session only
✗ No, don't remember
```

#### Memory Impact on Responses

**WITHOUT Memory:**
```
Q: "When is exam registration?"
A: "Exam registration opens 3 weeks before exams..."
```

**WITH Memory (knows name + year + major):**
```
Q: "When is exam registration?"
A: "Hi Hemanth! For 3rd year CS students, exam registration 
    opens March 1. Your typical courses (CS301, CS302, CS303) 
    will be available for registration. Need help with the process?"
```

#### Implementation Components

**New Service:**
```
backend/app/services/fact_extraction_service.py
- FactExtractor class
- extract_identity_facts()
- extract_academic_context()
- extract_concern_signals()
- request_user_confirmation()
```

**New Service:**
```
backend/app/services/memory_control_service.py
- MemoryController class
- store_fact_with_consent()
- delete_fact()
- set_retention_policy()
- get_user_memory_view()
```

**Database Schema:**
```javascript
// Add to users collection:
{
  user_id: "google_123",
  
  // Existing preferences array
  preferences: [...],
  
  // NEW: Facts array
  facts: [
    {
      category: "identity",
      key: "name",
      value: "Hemanth",
      retention: "permanent",
      locked: true,
      extracted_at: ISODate,
      confirmed_by_user: true,
      source: "conversation",
      session_id: "session_abc"
    },
    {
      category: "academic",
      key: "current_courses",
      value: ["CS301", "CS302", "MA401"],
      retention: "semester",  // Auto-expire after semester
      locked: false,
      extracted_at: ISODate,
      confirmed_by_user: true
    },
    {
      category: "concern",
      key: "attendance_worry",
      value: "Concerned about CS301 attendance",
      retention: "session",  // Temporary
      locked: false,
      extracted_at: ISODate,
      confirmed_by_user: false  // Implicit signal
    }
  ],
  
  memory_settings: {
    auto_extract_enabled: true,
    require_confirmation: true,
    default_retention: "permanent"
  }
}
```

**API Endpoints:**
```
GET    /api/v1/users/memory/view          # See all stored facts
POST   /api/v1/users/memory/remember      # Explicit store
DELETE /api/v1/users/memory/forget/{key}  # Delete fact
PUT    /api/v1/users/memory/retention     # Update retention policy
POST   /api/v1/users/memory/reset         # Delete all facts
```

**Frontend Components:**
```
1. Memory confirmation modal (when facts detected)
2. Memory dashboard page (view/edit all facts)
3. Memory directive input ("remember this", "forget that")
4. Privacy controls (retention policies)
```

**Integration with Response Generation:**
```python
# Modify: backend/app/services/query_service.py
async def query(self, request: QueryRequest, user_id: str = None):
    # Fetch user facts
    user_facts = await self.users_repo.get_user_facts(user_id)
    
    # Build personalized context
    context_prefix = self._build_user_context(user_facts)
    # e.g., "User is Hemanth, 3rd year CS student, taking CS301..."
    
    # Pass to RAG with context
    rag_result = await self.rag_adapter.query(
        question=request.question,
        user_context=context_prefix  # NEW
    )
    
    # Response is now personalized with user facts
    return rag_result
```

#### Evaluation Metrics

**Memory Accuracy:**
- Fact extraction precision: % correctly extracted
- Fact extraction recall: % of mentioned facts caught
- User confirmation rate: % of extractions confirmed by users

**Privacy & Control:**
- User survey: "I trust the system with my information" (target: >80%)
- User survey: "I feel in control of what's remembered" (target: >85%)
- Deletion compliance: 100% facts deleted when requested

**Response Quality:**
- Relevance improvement: With vs. without user facts
- User survey: "Responses feel personalized" (target: >75%)
- User survey: "System remembers important details" (target: >80%)

---

## Integration: How Features Work Together

### Unified System Flow

```
User Query: "When is exam registration?"
     ↓
1. FACT MEMORY (NEW)
   → System knows: User is Hemanth, 3rd year CS
   → Personalizes retrieval: Focus on 3rd year courses
     ↓
2. RAG RETRIEVAL (EXISTING)
   → Retrieves from current policy documents
   → Uses UNLEARNING system to ensure latest version
     ↓
3. RISK PREDICTION (NEW)
   → Analyzes: User asked about registration 2x
   → Detects: Potential deadline risk (low severity)
     ↓
4. RESPONSE GENERATION
   → Base answer: Policy information
   → Personalization: "Hi Hemanth, for 3rd year CS..."
   → Risk alert: "Registration closes March 1 (5 days)"
     ↓
5. OUTPUT
   "Hi Hemanth! For 3rd year CS students, exam registration 
    opens March 1. You'll register for courses like CS301, 
    CS302, etc. 
    
    ⚠️ Reminder: Registration closes in 5 days. Make sure 
    you have 75% attendance to be eligible."
```

### Example Scenarios

**Scenario 1: Policy Update Impact**
```
Day 0: Attendance policy updated 75% → 80%
       └─→ UNLEARNING: Old policy deprecated
       
Day 1: User asks "What's attendance requirement?"
       └─→ RAG: Retrieves new 80% policy (old unlearned)
       └─→ MEMORY: Knows user worried about attendance before
       └─→ Response: "Policy recently updated to 80% (was 75%). 
                      Since you were concerned about this, 
                      note the change."
```

**Scenario 2: Proactive Assistance**
```
Week 1: User asks "How to drop a course?"
Week 2: User asks "Drop deadline?"
Week 3: User asks "What happens if I drop CS301?"
        └─→ RISK PREDICTION: Course management risk detected
        └─→ MEMORY: Knows user is 3rd year, needs CS301 for prereq
        └─→ Response: "Before dropping CS301, note:
                      - Required for CS401 next semester
                      - Delay graduation by 1 semester
                      - Alternative: Consider withdrawal instead"
```

**Scenario 3: Transparent Memory**
```
User: "What do you know about me?"
System displays:
┌────────────────────────────────────┐
│ Your Stored Information            │
├────────────────────────────────────┤
│ ✓ Name: Hemanth (permanent, locked)│
│ ✓ Year: 3rd year (permanent)       │
│ ✓ Major: CS (permanent)            │
│ ✓ Concern: Attendance (session)    │
│                                    │
│ [Edit] [Delete] [Privacy Settings] │
└────────────────────────────────────┘
```

---

## 8-Week Implementation Timeline

### Week 1-2: Knowledge Unlearning & Lifecycle Management
**Goal:** Enable document updates and deprecation

**Tasks:**
- Day 1-2: Design document metadata schema
- Day 3-4: Implement DocumentLifecycleManager service
- Day 5-6: Create admin API routes
- Day 7-8: Build admin dashboard UI
- Day 9-10: Test unlearning with policy updates

**Deliverable:** Working document management system

---

### Week 3-4: Predictive Risk Detection
**Goal:** Detect 3 risk types from conversation patterns

**Tasks:**
- Day 1-2: Implement RiskPredictor service (pattern matching)
- Day 3-4: Add risk detection algorithms (3 types)
- Day 5-6: Integrate with query service
- Day 7-8: Build risk alert UI components
- Day 9-10: Create test scenarios and validate

**Deliverable:** Working risk prediction with alerts

---

### Week 5-6: User-Controlled Memory (Fact Extraction)
**Goal:** Extract and store user facts with consent

**Tasks:**
- Day 1-2: Implement FactExtractor service
- Day 3-4: Implement MemoryController service
- Day 5-6: Add confirmation flow
- Day 7-8: Build memory dashboard UI
- Day 9-10: Integrate with response generation

**Deliverable:** Working fact memory system

---

### Week 7: Integration & Evaluation
**Goal:** Connect all features and run experiments

**Tasks:**
- Day 1-2: End-to-end integration testing
- Day 3-4: Run evaluation experiments
- Day 5-6: Collect metrics for all 3 features
- Day 7: Fix bugs, polish UI

**Deliverable:** Complete integrated system + metrics

---

### Week 8: Paper Writing & User Study
**Goal:** Document research and validate with users

**Tasks:**
- Day 1-3: Write paper draft (6-8 pages)
- Day 4-5: Conduct user study (10-15 participants)
- Day 6-7: Analyze results, finalize paper

**Deliverable:** Research paper draft + user study results

---

## Evaluation Plan

### Experiment 1: Zero-Knowledge Baseline Validation
**Goal:** Prove hallucination prevention

**Methodology:**
- Compare 3 approaches: Pure LLM, Standard RAG, Zero-Knowledge RAG
- Test on 82 questions (in-scope + out-of-scope)
- Measure: Hallucination rate, refusal accuracy, F1 score

**Expected Results:**
| Approach | In-Scope Accuracy | Refusal Accuracy | Hallucination |
|----------|------------------|------------------|---------------|
| Pure LLM | 45% | 0% | 78% |
| Standard RAG | 78% | 12% | 34% |
| **Zero-Knowledge** | **94%** | **89%** | **<10%** |

---

### Experiment 2: Unlearning Effectiveness
**Goal:** Prove clean knowledge updates

**Methodology:**
- Update 3 policies (attendance, exam registration, grading)
- Test queries before and after update
- Measure: Transition time, conflict rate, hallucination of old policy

**Expected Results:**
- Transition time: <1 minute
- Conflict rate: 0%
- Old policy hallucination: 0%
- New policy accuracy: 94% (maintained)

---

### Experiment 3: Risk Prediction Accuracy
**Goal:** Validate conversation-based risk detection

**Methodology:**
- Create 20 synthetic risk scenarios (attendance, deadline, confusion)
- Manual validation by academic advisors
- Measure: Precision, recall, lead time, false positives

**Expected Results:**
- Precision: >70%
- Recall: >60%
- Average lead time: 7+ days
- False positive rate: <20%

---

### Experiment 4: User Memory Control
**Goal:** Validate privacy and personalization

**Methodology:**
- User study with 10-15 students
- Tasks: Provide personal info, test memory commands, rate experience
- Measure: Memory accuracy, user satisfaction, privacy trust

**Expected Results:**
- Fact extraction accuracy: >85%
- User satisfaction: >75%
- Privacy trust: >80%
- Deletion compliance: 100%

---

## Research Paper Structure

### Title
"Zero-Knowledge Adaptive RAG with Unlearning and Predictive Memory Control for Educational Systems"

### Abstract (250 words)
Academic advisory systems powered by Retrieval-Augmented Generation (RAG) face three critical challenges: hallucination of incorrect information, inability to handle knowledge updates, and reactive-only assistance. We present a novel RAG architecture that addresses these challenges through: (1) zero-knowledge constraints with measurable hallucination prevention, (2) trackable knowledge lifecycle management with clean unlearning, (3) predictive risk detection from conversation patterns, and (4) user-governed memory control with fact extraction. Our evaluation shows X% hallucination reduction, 100% conflict-free policy updates, Y% risk prediction accuracy with Z-day lead time, and W% user satisfaction with memory controls. The system represents the first integration of unlearning, predictive reasoning, and user-controlled memory in educational RAG systems.

### Sections
1. **Introduction** (2 pages)
   - Problem: Hallucination, static knowledge, reactive assistance
   - Research questions
   - Contributions: 4 novel features

2. **Related Work** (1.5 pages)
   - RAG systems and hallucination mitigation
   - Knowledge unlearning and memory management
   - Conversational AI and predictive assistance
   - Educational AI systems

3. **System Architecture** (2 pages)
   - Zero-knowledge RAG baseline
   - Unlearning mechanism
   - Risk prediction from memory
   - User-controlled fact extraction

4. **Experiments & Results** (2 pages)
   - Exp 1: Hallucination comparison
   - Exp 2: Unlearning effectiveness
   - Exp 3: Risk prediction accuracy
   - Exp 4: Memory control validation

5. **Discussion** (1 page)
   - Why these features work together
   - Limitations and threats to validity
   - Practical implications

6. **Conclusion** (0.5 pages)
   - Summary of contributions
   - Future work

**Target Length:** 8 pages (conference format)

---

## Success Criteria

### For Graduation
- ✅ Working system with 3 novel features
- ✅ Evaluation showing measurable improvements
- ✅ Documentation and code repository
- ✅ Demo video

### For Publication
- ✅ Clear novelty (unlearning + risk prediction + memory control)
- ✅ Comparative evaluation (better than baselines)
- ✅ User study validation
- ✅ Reproducible (dataset + code release)

### For Impact
- ✅ Practical applicability in real institutions
- ✅ Measurable student success improvements
- ✅ Privacy-first design
- ✅ Open source for community benefit

---

## Risk Mitigation

### Technical Risks
**Risk:** Features don't integrate cleanly  
**Mitigation:** Weekly integration testing, feature flags for rollback

**Risk:** Performance degradation  
**Mitigation:** Benchmark each feature, optimize critical paths

### Evaluation Risks
**Risk:** Can't recruit enough users for study  
**Mitigation:** Use synthetic scenarios + advisor validation as backup

**Risk:** Results don't meet expectations  
**Mitigation:** Set realistic targets, focus on relative improvement

### Timeline Risks
**Risk:** Implementation takes longer than expected  
**Mitigation:** Prioritize core functionality, cut nice-to-haves

**Risk:** Paper writing delayed  
**Mitigation:** Start writing early (Week 4), parallel with implementation

---

## Beyond Graduation (Future Work)

### Not Implementing Now (Documented for Future)
- Multi-source RAG with database integration
- Web intelligence and real-time scraping
- What-if scenario planning
- CO-PO outcome mapping integration
- Multi-modal support (images, documents)
- Multi-language support

### Explained in Paper As
- Proposed architecture (designed but not implemented)
- Natural extensions of current system
- Future research directions

---

## Repository Structure

```
project/
├── backend/
│   ├── app/
│   │   ├── services/
│   │   │   ├── knowledge_lifecycle_service.py    # NEW
│   │   │   ├── risk_prediction_service.py        # NEW
│   │   │   ├── fact_extraction_service.py        # NEW
│   │   │   ├── memory_control_service.py         # NEW
│   │   │   └── ... (existing services)
│   │   └── api/routes/
│   │       ├── admin_documents.py                # NEW
│   │       └── ... (existing routes)
│   └── ...
├── frontend/
│   └── src/
│       └── components/
│           ├── AdminDocumentPanel.jsx            # NEW
│           ├── RiskAlertDisplay.jsx              # NEW
│           ├── MemoryDashboard.jsx               # NEW
│           ├── MemoryConfirmationModal.jsx       # NEW
│           └── ... (existing components)
├── data/
│   └── chroma_db/                                # Existing
├── docs/
│   ├── FINAL_IMPLEMENTATION_PLAN.md              # This file
│   ├── paper_draft.md                            # Week 8
│   └── evaluation_results.md                     # Week 7
└── experiments/
    ├── hallucination_comparison.py               # Week 7
    ├── unlearning_tests.py                       # Week 2
    ├── risk_prediction_validation.py             # Week 4
    └── memory_accuracy_tests.py                  # Week 6
```

---

## Key Metrics to Track

### During Implementation
- [ ] Lines of code added
- [ ] Test coverage (target: >80% for new features)
- [ ] API response time (<1.5s with all features)
- [ ] Memory usage (should stay under 2GB)

### For Evaluation
- [ ] Hallucination rate: <10%
- [ ] Unlearning success rate: 100%
- [ ] Risk prediction accuracy: >70%
- [ ] User satisfaction: >75%
- [ ] Privacy trust: >80%

### For Paper
- [ ] Figure count: 4-6 figures
- [ ] Table count: 3-5 tables
- [ ] Citation count: 25-30 references
- [ ] Word count: 4000-5000 words

---

## Team Roles (If Applicable)

**Solo Implementation:**
- All development, testing, evaluation, and writing

**If Team (2 people):**
- Person 1: Backend (unlearning + risk prediction)
- Person 2: Frontend + memory control + user study

**Advisor Support:**
- Weekly check-ins
- Paper draft review (Week 6, Week 8)
- User study design guidance

---

## Conclusion

This implementation plan focuses on **3 core research contributions** that are:
- ✅ Novel (no existing system combines all three)
- ✅ Implementable (8 weeks with focused scope)
- ✅ Measurable (clear evaluation metrics)
- ✅ Practical (real impact on education)
- ✅ Publishable (conference-quality research)

**Next Steps:**
1. Review this plan with advisor
2. Set up development environment
3. Start Week 1: Knowledge Unlearning
4. Weekly progress tracking

**Target Completion:** April 8, 2026  
**Expected Outcome:** Research paper + working system + graduation

---

**Document Version:** 1.0  
**Last Updated:** February 12, 2026  
**Status:** Ready for Implementation
