# Application Validation Report

- Generated at: 2026-03-31T18:09:23.618702+00:00
- Validator provider: openai
- Validator model: `gpt-4.1-mini`
- Total turns: 110
- Completed turns: 108
- Failed turns: 2

## Metric Summary

| Metric | Value |
| --- | --- |
| personalization_accuracy | 0.7391 |
| zero_knowledge_compliance | 1.0 |
| user_memory_relevance_score | 1.476 |
| grounded_response_fidelity | 0.7162 |
| contradiction_resolution_rate | 1.0 |
| knowledge_evolution_stability | 1.0 |
| end_to_end_task_success_rate | 0.6909 |
| hallucination_rate | 0.037 |
| context_sufficiency_rate | 0.7037 |
| retry_recovery_rate | 0.3333 |
| refusal_correctness_rate | None |
| policy_claim_false_alarm_rate | 0.0 |

## Retry Summary

- Average latency (ms): 42847.8
- P95 latency (ms): 71934.05

## Strong Examples

- AVS-001 T01: Hello
- AVS-001 T02: I'm Arjun, a 4th year CSE student. I'm doing my final year project and internship this semester.
- AVS-001 T03: Just give me short direct answers from now on. I don't need long explanations.

## Weak Examples

- AVS-003 T01: Please keep your answers concise from now on.
- AVS-004 T01: I'm new to all this. Please explain things in a detailed beginner-friendly way.
- AVS-004 T06: Why does the system ask users to upload proof?

## Notes

- The validator provider is configurable through the harness.
- This report is updated incrementally from per-turn JSONL records.
