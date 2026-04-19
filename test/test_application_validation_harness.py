"""Unit tests for the application validation harness."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from application_validation_benchmark import TOTAL_TURNS
from application_validation_harness import (
    compute_task_success,
    execute_with_retry,
    extract_json_object,
    summarize_records,
)

class HarnessHelpersTest(unittest.TestCase):
    def test_benchmark_contains_150_turns(self):
        self.assertEqual(TOTAL_TURNS, 150)

    def test_extract_json_object_with_wrapped_text(self):
        wrapped = "validator output\n{\"verdict\":\"accept\",\"groundedness_score\":5}\nthanks"
        parsed = extract_json_object(wrapped)
        self.assertEqual(parsed["verdict"], "accept")
        self.assertEqual(parsed["groundedness_score"], 5)

    def test_compute_task_success_for_preference_learning(self):
        record = {
            "execution": {"final_status": "completed"},
            "expected_behaviors": {"expects_preference_extraction": True},
            "rule_checks": {"preference_extracted": True},
            "judge": {},
        }
        self.assertTrue(compute_task_success(record))

    def test_summary_metrics_include_retry_recovery(self):
        records = [
            {
                "metric_tags": ["personalization"],
                "expected_behaviors": {"expects_personalization": True},
                "execution": {"final_status": "completed", "retry_count": 1, "latency_ms": 1000},
                "rule_checks": {
                    "claim_detection_match": True,
                    "policy_claim_detected": False,
                    "preference_extracted": False,
                    "fact_count_delta": 0,
                    "refusal_match": True,
                },
                "judge": {
                    "personalization_applied_correctly": True,
                    "zero_knowledge_compliant": None,
                    "memory_relevance_score": None,
                    "groundedness_score": 5,
                    "hallucination_detected": False,
                    "context_sufficiency_score": 5,
                    "refusal_correctness": None,
                    "verdict": "accept",
                    "error_type": "no_error",
                },
            },
            {
                "metric_tags": ["groundedness"],
                "expected_behaviors": {"expects_grounded_answer": True},
                "execution": {"final_status": "failed", "retry_count": 2, "latency_ms": 2000},
                "rule_checks": {
                    "claim_detection_match": True,
                    "policy_claim_detected": False,
                    "preference_extracted": False,
                    "fact_count_delta": 0,
                    "refusal_match": True,
                },
                "judge": {
                    "personalization_applied_correctly": None,
                    "zero_knowledge_compliant": None,
                    "memory_relevance_score": None,
                    "groundedness_score": 1,
                    "hallucination_detected": False,
                    "context_sufficiency_score": 1,
                    "refusal_correctness": None,
                    "verdict": "reject",
                    "error_type": "task_failure",
                },
            },
        ]
        summary = summarize_records(records, run_metadata={"run_id": "demo"})
        self.assertEqual(summary["completed_turns"], 1)
        self.assertEqual(summary["failed_turns"], 1)
        self.assertEqual(summary["metrics"]["retry_recovery_rate"], 0.5)

    def test_execute_with_retry_retries_wrapped_provider_rate_limit(self):
        class FakeClient:
            def __init__(self):
                self.calls = 0

            def query(self, session_id: str, question: str):
                self.calls += 1
                if self.calls == 1:
                    return (
                        200,
                        {
                            "answer": "I apologize, but I encountered an error while generating a response.",
                            "generation_error": {
                                "category": "provider_rate_limit",
                                "retryable": True,
                                "retry_after_seconds": 0.0,
                                "message": "Rate limit reached",
                            },
                        },
                        "{}",
                        {},
                    )
                return (200, {"answer": "40% comes from CA."}, "{}", {})

        result = execute_with_retry(FakeClient(), session_id="s1", question="q1")
        self.assertEqual(result["final_status"], "completed")
        self.assertEqual(result["retry_count"], 1)
        self.assertEqual(result["response"]["answer"], "40% comes from CA.")


if __name__ == "__main__":
    unittest.main()
