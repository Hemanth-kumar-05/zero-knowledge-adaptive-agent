# Integrated Application Validation Report

- Integration type: weighted summary merge
- Source 1: `test/reports/till-avs17/application_validation_full/application_validation_summary.json`
- Source 2: `test/reports/after_17/application_validation_full/application_validation_summary.json`
- Validator provider: openai
- Validator model: `gpt-4.1-mini`
- Total turns: 153
- Completed turns: 151
- Failed turns: 2

## Metric Summary

| Metric | Value |
| --- | --- |
| personalization_accuracy | 0.7391 |
| zero_knowledge_compliance | 1.0 |
| user_memory_relevance_score | 1.2693 |
| grounded_response_fidelity | 0.6784 |
| contradiction_resolution_rate | 1.0 |
| knowledge_evolution_stability | 1.0 |
| end_to_end_task_success_rate | 0.6536 |
| hallucination_rate | 0.0463 |
| context_sufficiency_rate | 0.6755 |
| retry_recovery_rate | 0.3333 |
| refusal_correctness_rate | 1.0 |
| policy_claim_false_alarm_rate | 0.0 |

## Latency Summary

- Average latency (ms): 43271.82
- P95 latency (ms): 74405.15

## Failure Categories

| Category | Count |
| --- | --- |
| task_failure | 15 |
| no_error | 11 |
| retrieval_failure | 21 |
| generation_hallucination | 5 |
| memory_error | 1 |

## Method

- This file integrates the two summary snapshots only.
- It does not use `runs.jsonl` or `manual_review.md`.
- Metrics were merged with weighted aggregation, not simple averaging.
- Completed-answer quality metrics were weighted by completed turns.
- Attempt-level metrics were weighted by total turns.
- If one source had `null` and the other had a value, the available value was kept.
- The p95 latency is a conservative proxy using the higher source p95 because exact recomputation is not possible from summary files alone.
