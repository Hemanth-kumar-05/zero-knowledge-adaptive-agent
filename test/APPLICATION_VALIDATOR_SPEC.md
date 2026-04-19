# Application Validator Specification

## Purpose

This validator evaluates the **running application behavior**, not just the policy dataset.

It should verify the full query lifecycle:

1. user question is submitted
2. the application retrieves context and generates a response
3. optional retry or query rewrite happens if needed
4. the validator inspects the query, retrieved sources, generated response, and workflow metadata
5. the validator appends a structured record to the evaluation report

The validator should therefore act as a **trace-based evaluation layer** over the real backend flow.

---

## Core Principle

The application validator should not be a pure LLM judge.

It should use a **hybrid design**:

- **deterministic checks** for things that can be measured directly
- **LLM-assisted checks** for semantic judgment
- **scenario-aware scoring** so each run is evaluated against the intended metric

This gives better credibility for a final review and for report writing.

---

## What The Validator Should Ingest Per Run

Each validation record should capture:

- `scenario_id`
- `user_id`
- `session_id`
- `question`
- `rewritten_question` if query rewriting occurred
- `retrieved_sources`
- `retrieval_count`
- `response`
- `refused`
- `confidence`
- `latency_ms`
- `applied_preferences`
- `user_memory_context_used`
- `extracted_preferences`
- `extracted_facts`
- `policy_claim_detected`
- `risk_alerts`
- `timestamp`

Optional but useful:

- top-k similarity scores
- full source chunk text
- source metadata such as `doc_id`, `section`, `status`, `version`
- whether this was first-attempt success or retry success

---

## Validation Layers

## 1. Retrieval Validation

This layer answers:

- were the retrieved chunks relevant?
- was enough evidence retrieved?
- were the best chunks ranked high enough?
- was the retry or query rewrite helpful?

Recommended outputs:

- `context_relevance_score`
- `context_sufficiency_score`
- `context_ranking_score`
- `retry_helpfulness`

Deterministic checks:

- source count
- similarity distribution
- whether active chunks were used instead of deprecated chunks
- whether at least one expected document appears in gold benchmark scenarios

LLM checks:

- whether retrieved chunks actually answer the question
- which chunks were useful vs irrelevant
- what key missing evidence was absent

---

## 2. Response Validation

This layer evaluates the answer against retrieved evidence.

Mandatory checks:

- groundedness / faithfulness
- hallucination detection
- relevance to query
- completeness
- contradiction with retrieved sources
- refusal correctness for out-of-scope cases

Recommended outputs:

- `groundedness_score`
- `hallucination_detected`
- `hallucinated_spans`
- `answer_relevance_score`
- `completeness_score`
- `contradiction_detected`
- `refusal_correctness`
- `verdict`
- `validator_confidence`

The validator should also classify answer failure cause:

- `retrieval_failure`
- `generation_hallucination`
- `personalization_error`
- `memory_error`
- `policy_workflow_error`
- `prompting_or_instruction_failure`
- `no_error`

---

## 3. Personalization Validation

This layer directly supports your project-specific contribution.

The validator should check whether the system:

- applied known preferences when it should
- stayed neutral when it should not personalize
- used user memory only when relevant
- avoided irrelevant memory injection

Metrics supported:

- `Personalization Accuracy`
- `Personalization Consistency`
- `Zero-Knowledge Compliance`
- `False Personalization Rate`
- `User Memory Relevance Score`

Recommended checks:

- did response style match stored preference?
- did format match stored preference?
- did technical level match stored preference?
- did memory appear only when relevant?
- did the system invent user traits for a fresh user?

Recommended outputs:

- `personalization_applied_correctly`
- `personalization_consistency_score`
- `memory_relevance_score`
- `zero_knowledge_compliant`
- `false_personalization_detected`

---

## 4. Memory Safety Validation

This layer focuses on privacy and governance.

Metrics supported:

- `Memory Isolation Integrity`
- `Fact Extraction Precision`
- `Memory Update Correctness`
- `User Control Compliance`

Recommended checks:

- cross-user leakage detection
- session ownership isolation
- whether extracted facts match annotated truth
- whether memory updates replace or preserve facts correctly
- whether forget / reset / confirm / retain controls actually work

Recommended outputs:

- `memory_isolation_pass`
- `cross_user_leak_detected`
- `fact_extraction_precision`
- `memory_update_correct`
- `user_control_compliance`

Any cross-user leakage should be treated as an **automatic critical fail**.

---

## 5. Knowledge Evolution Validation

This layer evaluates the Phase 3 workflow.

Metrics supported:

- `Knowledge Evolution Stability`
- `Contradiction Resolution Rate`
- `Policy Claim Detection Precision`
- `Audit Completeness`

Recommended checks:

- did the system detect a genuine policy-change claim?
- did it avoid triggering on non-claims?
- did it request proof properly?
- was a pending claim stored in session metadata?
- was ticket creation successful?
- were affected chunks found?
- were old chunks deprecated safely?
- were new chunks created correctly?
- was retrieval updated after approval?
- was the audit trail complete?

Recommended outputs:

- `policy_claim_detection_correct`
- `proof_request_triggered`
- `ticket_creation_success`
- `affected_chunk_recall`
- `chunk_update_success`
- `post_update_retrieval_correct`
- `audit_complete`

---

## 6. Operational Validation

This layer tracks practical product behavior.

Metrics supported:

- `End-to-End Task Success Rate`
- `Response Latency`
- `Extension Execution Success Rate`
- `Risk Alert Precision`
- `Session Context Continuity`

Recommended outputs:

- `task_success`
- `latency_ms`
- `p95_bucket`
- `extension_execution_success`
- `risk_alert_precision`
- `session_context_continuity_score`

---

## Judge Design

The validator should use **two judge modes**:

### A. Rule-Based Judge

Use for:

- latency
- source count
- expected document presence
- memory isolation
- session ownership
- ticket existence
- audit record existence
- preference and fact extraction comparison against labels

### B. LLM Judge

Use for:

- groundedness
- hallucination
- completeness
- response relevance
- context sufficiency
- memory relevance
- personalization quality
- contradiction explanation
- error classification

The LLM judge should always receive:

- original question
- expected scenario objective
- retrieved chunks
- final answer
- personalization context
- memory context
- workflow metadata

The prompt should force strict structured JSON output.

---

## Recommended Output Schema

Each validated request should produce a machine-readable record like:

```json
{
  "scenario_id": "SCN-GRD-01",
  "question": "Is CA eligible for revaluation?",
  "retrieval": {
    "context_relevance_score": 4,
    "context_sufficiency_score": 5,
    "context_ranking_score": 4,
    "retry_helpfulness": 0
  },
  "response": {
    "groundedness_score": 5,
    "hallucination_detected": false,
    "hallucinated_spans": [],
    "answer_relevance_score": 5,
    "completeness_score": 4,
    "contradiction_detected": false,
    "refusal_correctness": null,
    "verdict": "accept",
    "validator_confidence": 0.92
  },
  "personalization": {
    "personalization_applied_correctly": null,
    "memory_relevance_score": null,
    "zero_knowledge_compliant": null
  },
  "workflow": {
    "task_success": true,
    "latency_ms": 1820
  },
  "error_type": "no_error"
}
```

For personalization scenarios, the same schema should populate those fields instead.

---

## Metric Mapping To Your Existing Framework

The validator should compute your predefined metrics directly:

### Personalization Accuracy

Pass when known preferences or relevant memory are correctly applied.

Formula:

`correct_personalized_cases / total_personalization_cases`

### User Memory Relevance Score

Use a 0 to 2 scale per case:

- `0` irrelevant
- `1` partially useful
- `2` clearly relevant and helpful

### Memory Isolation Integrity

Pass/fail safety metric.

Formula:

`leak_free_cases / total_cross_user_cases`

### Knowledge Evolution Stability

Aggregate:

- claim detection correctness
- proof flow correctness
- affected chunk recall
- update execution success
- post-update retrieval correctness
- audit completeness

### Contradiction Resolution Rate

Formula:

`correctly_handled_contradiction_cases / total_contradiction_cases`

### Zero-Knowledge Compliance

Formula:

`neutral_responses_without_prior_learning / total_zero_knowledge_cases`

---

## Additional Metrics Worth Adding

To make the validator stronger, add these:

- `Context Sufficiency Rate`
- `Hallucination Rate`
- `Refusal Correctness Rate`
- `Retry Recovery Rate`
- `Expected Source Hit Rate`
- `Deprecated Chunk Avoidance Rate`
- `Prompt Instruction Compliance`
- `Cross-User Security Failure Count`
- `Policy Claim False Alarm Rate`
- `Post-Update Regression Rate`

These are especially useful in report tables and ablation discussion.

---

## Execution Flow

The recommended implementation flow is:

1. load benchmark scenario
2. prepare user and session state
3. send request to backend API
4. capture raw response and metadata
5. capture retrieved sources and workflow outputs
6. run rule-based checks
7. run LLM judge on semantic checks
8. merge both into one validated record
9. append the record to:
   - `jsonl` for machine processing
   - `csv` for aggregate metrics
   - `md` summary for report writing
10. recompute aggregate metric tables

---

## Report Append Strategy

The validator should append results in two forms:

### A. Per-run report log

Store each run in:

- `reports/application_validation_runs.jsonl`

Each line should be a full validation record.

### B. Aggregate summary

Store computed summaries in:

- `reports/application_validation_summary.json`
- `reports/application_validation_summary.md`

The markdown summary should include:

- metric table
- pass/fail counts
- key failures
- representative good and bad examples

---

## Recommendation For Simulated 100 Requests

For 100 simulated validation requests, the validator model should prioritize:

- strict JSON adherence
- strong instruction following
- low cost
- consistent grading behavior

Recommended choice:

- **Primary recommendation:** `GPT-4.1 mini`

Why:

- better structured judging reliability than very small open models
- low enough cost that 100 validation calls are inexpensive
- good fit for rubric-style JSON evaluation

Budget recommendation:

- use one validator pass per request for the main run
- optionally re-judge only borderline or failed cases with a stronger model

Suggested two-tier strategy:

- first pass: `GPT-4.1 mini`
- escalation pass for disputed cases only: stronger model such as `GPT-4.1` or `Claude Sonnet 4`

If absolute lowest cost matters more than judge quality:

- consider `Gemini 2.5 Flash-Lite`

If you want to stay in the open-model / Groq ecosystem:

- `openai/gpt-oss-20b` is a reasonable budget judge
- avoid using the cheapest model as the only judge for final reported results

---

## Final Position

Your application validator should evaluate **far more than answer quality**.

It should validate:

- retrieval quality
- grounded generation quality
- personalization correctness
- memory relevance and safety
- contradiction handling
- knowledge evolution workflow behavior
- end-to-end task completion

That is what makes it a true **application validator** rather than just a response scorer.
