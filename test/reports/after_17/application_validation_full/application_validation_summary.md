# Application Validation Report

- Generated at: 2026-03-31T18:49:45.986468+00:00
- Validator provider: openai
- Validator model: `gpt-4.1-mini`
- Total turns: 43
- Completed turns: 43
- Failed turns: 0

## Metric Summary

| Metric | Value |
| --- | --- |
| personalization_accuracy | None |
| zero_knowledge_compliance | None |
| user_memory_relevance_score | 0.75 |
| grounded_response_fidelity | 0.5833 |
| contradiction_resolution_rate | None |
| knowledge_evolution_stability | 1.0 |
| end_to_end_task_success_rate | 0.5581 |
| hallucination_rate | 0.0698 |
| context_sufficiency_rate | 0.6047 |
| retry_recovery_rate | None |
| refusal_correctness_rate | 1.0 |
| policy_claim_false_alarm_rate | 0.0 |

## Retry Summary

- Average latency (ms): 44356.51
- P95 latency (ms): 74405.15

## Strong Examples

- AVS-017 T04: If someone mixes up lab marks with ESE marks, how would you correct them carefully?
- AVS-017 T05: Can you compare what is fixed, what is revisable, and what depends on registration in one explanation?
- AVS-018 T02: Do you know me well enough yet to give personalized advice, or should you stay general?

## Weak Examples

- AVS-017 T01: I'm confused because one person told me CA can be revaluated and another said only ESE can. How should I reason about that based on current rules?
- AVS-017 T02: If my final grade changes only after ESE revaluation, which parts of the grading pipeline stay unchanged?
- AVS-017 T03: What would be the wrong assumption a student might make here?

## Notes

- The validator provider is configurable through the harness.
- This report is updated incrementally from per-turn JSONL records.
