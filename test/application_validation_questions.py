"""Question-only view of the application validation benchmark."""

from __future__ import annotations

from application_validation_benchmark import BENCHMARK_SESSIONS


QUESTION_ONLY_SESSIONS = [
    {
        "session_id": item["session_id"],
        "session_goal": item["session_goal"],
        "questions": [turn["question"] for turn in item["turns"]],
    }
    for item in BENCHMARK_SESSIONS
]
