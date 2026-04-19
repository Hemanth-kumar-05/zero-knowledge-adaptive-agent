"""CLI harness for authenticated application validation runs."""

from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from application_validation_benchmark import BENCHMARK_SESSIONS, TOTAL_TURNS


DEFAULT_OUTPUT_DIR = Path("reports") / "application_validation"
DEFAULT_VALIDATOR_PROVIDER = "openai"
DEFAULT_VALIDATOR_MODEL = "gpt-4.1-mini"
DEFAULT_TIMEOUT_SECONDS = 90
MAX_RETRY_ATTEMPTS = 5
INITIAL_RETRY_DELAY_SECONDS = 2.0
MAX_BACKOFF_SECONDS = 600.0
DEFAULT_BACKEND_WAIT_THRESHOLD_SECONDS = 180.0
DEFAULT_BACKEND_HOST = "127.0.0.1"
DEFAULT_BACKEND_PORT = 8000


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, indent=2, default=str)


def normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def parse_host_port_from_base_url(base_url: str) -> tuple[str, int]:
    parsed = urllib.parse.urlparse(normalize_base_url(base_url))
    host = parsed.hostname or DEFAULT_BACKEND_HOST
    port = parsed.port or DEFAULT_BACKEND_PORT
    return host, port


def extract_json_object(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(text[start : end + 1])


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = int(round((pct / 100.0) * (len(ordered) - 1)))
    return ordered[index]


def prompt_if_missing(value: str | None, prompt: str, secret: bool = False) -> str:
    if value:
        return value
    if secret:
        print("Paste is enabled for this prompt. Input will be visible.")
    return input(prompt).strip()


class BackendApiClient:
    def __init__(self, base_url: str, jwt_token: str, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS):
        self.base_url = normalize_base_url(base_url)
        self.jwt_token = jwt_token.strip()
        self.timeout_seconds = timeout_seconds

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any], str, dict[str, str]]:
        url = f"{self.base_url}{path}"
        if query:
            url = f"{url}?{urllib.parse.urlencode(query)}"
        body = None
        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Accept": "application/json",
        }
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url=url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
                data = json.loads(raw) if raw else {}
                return response.status, data, raw, dict(response.headers.items())
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8")
            try:
                data = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                data = {"detail": raw}
            return exc.code, data, raw, dict(exc.headers.items())

    def verify_auth(self) -> dict[str, Any]:
        status, data, _, _ = self._request("GET", "/api/auth/me")
        if status != 200:
            raise RuntimeError(f"Authentication failed ({status}): {data}")
        return data

    def create_session(self) -> dict[str, Any]:
        status, data, _, _ = self._request("POST", "/api/v1/sessions/")
        if status not in {200, 201}:
            raise RuntimeError(f"Failed to create session ({status}): {data}")
        return data

    def query(self, session_id: str, question: str) -> tuple[int, dict[str, Any], str, dict[str, str]]:
        return self._request("POST", "/api/v1/query", payload={"question": question, "session_id": session_id})

    def get_session_messages(self, session_id: str) -> dict[str, Any]:
        status, data, _, _ = self._request("GET", f"/api/v1/sessions/{session_id}/messages")
        if status != 200:
            raise RuntimeError(f"Failed to fetch session messages ({status}): {data}")
        return data

    def get_memory(self) -> dict[str, Any]:
        status, data, _, _ = self._request("GET", "/api/v1/memory/view")
        if status != 200:
            raise RuntimeError(f"Failed to fetch memory ({status}): {data}")
        return data

    def get_preferences(self) -> dict[str, Any]:
        status, data, _, _ = self._request("GET", "/api/v1/users/preferences")
        if status != 200:
            raise RuntimeError(f"Failed to fetch preferences ({status}): {data}")
        return data


def parse_retry_after_seconds(headers: dict[str, str]) -> float | None:
    raw_value = None
    for key, value in headers.items():
        if key.lower() == "retry-after":
            raw_value = value
            break
    if raw_value is None:
        return None
    try:
        return max(0.0, float(raw_value))
    except ValueError:
        return None


def extract_response_generation_error(data: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(data, dict):
        return None
    generation_error = data.get("generation_error")
    return generation_error if isinstance(generation_error, dict) else None


class ValidationJudge:
    def judge(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class OpenAIValidationJudge(ValidationJudge):
    def __init__(self, api_key: str, model: str):
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def judge(self, payload: dict[str, Any]) -> dict[str, Any]:
        system_prompt = (
            "You are a strict application validator for a document-grounded academic assistant. "
            "Return JSON only. Be conservative. If evidence is missing, score lower rather than guessing."
        )
        user_prompt = json_dumps(
            {
                "task": "Evaluate one query-response turn.",
                "required_output_schema": {
                    "groundedness_score": "integer 1-5",
                    "hallucination_detected": "boolean",
                    "answer_relevance_score": "integer 1-5",
                    "completeness_score": "integer 1-5",
                    "context_sufficiency_score": "integer 1-5",
                    "personalization_applied_correctly": "boolean or null",
                    "zero_knowledge_compliant": "boolean or null",
                    "memory_relevance_score": "integer 0-2 or null",
                    "contradiction_handled_correctly": "boolean or null",
                    "refusal_correctness": "boolean or null",
                    "verdict": "accept or reject",
                    "error_type": "no_error, retrieval_failure, generation_hallucination, personalization_error, memory_error, contradiction_handling_error, task_failure",
                    "reasoning": "short string"
                },
                "payload": payload,
            }
        )
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        parsed = extract_json_object(response.output_text)
        parsed.setdefault("groundedness_score", 1)
        parsed.setdefault("hallucination_detected", False)
        parsed.setdefault("answer_relevance_score", 1)
        parsed.setdefault("completeness_score", 1)
        parsed.setdefault("context_sufficiency_score", 1)
        parsed.setdefault("personalization_applied_correctly", None)
        parsed.setdefault("zero_knowledge_compliant", None)
        parsed.setdefault("memory_relevance_score", None)
        parsed.setdefault("contradiction_handled_correctly", None)
        parsed.setdefault("refusal_correctness", None)
        parsed.setdefault("verdict", "reject")
        parsed.setdefault("error_type", "task_failure")
        parsed.setdefault("reasoning", "")
        return parsed


class GroqValidationJudge(ValidationJudge):
    def __init__(self, api_key: str, model: str):
        from groq import Groq

        self.client = Groq(api_key=api_key)
        self.model = model

    def judge(self, payload: dict[str, Any]) -> dict[str, Any]:
        system_prompt = (
            "You are a strict application validator for a document-grounded academic assistant. "
            "Return JSON only. Be conservative. If evidence is missing, score lower rather than guessing."
        )
        user_prompt = json_dumps(
            {
                "task": "Evaluate one query-response turn.",
                "required_output_schema": {
                    "groundedness_score": "integer 1-5",
                    "hallucination_detected": "boolean",
                    "answer_relevance_score": "integer 1-5",
                    "completeness_score": "integer 1-5",
                    "context_sufficiency_score": "integer 1-5",
                    "personalization_applied_correctly": "boolean or null",
                    "zero_knowledge_compliant": "boolean or null",
                    "memory_relevance_score": "integer 0-2 or null",
                    "contradiction_handled_correctly": "boolean or null",
                    "refusal_correctness": "boolean or null",
                    "verdict": "accept or reject",
                    "error_type": "no_error, retrieval_failure, generation_hallucination, personalization_error, memory_error, contradiction_handling_error, task_failure",
                    "reasoning": "short string"
                },
                "payload": payload,
            }
        )
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.1,
                max_tokens=900,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = response.choices[0].message.content or "{}"
        except Exception:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.1,
                max_tokens=900,
                messages=[
                    {"role": "system", "content": system_prompt + " Return valid JSON only."},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = response.choices[0].message.content or "{}"
        parsed = extract_json_object(content)
        parsed.setdefault("groundedness_score", 1)
        parsed.setdefault("hallucination_detected", False)
        parsed.setdefault("answer_relevance_score", 1)
        parsed.setdefault("completeness_score", 1)
        parsed.setdefault("context_sufficiency_score", 1)
        parsed.setdefault("personalization_applied_correctly", None)
        parsed.setdefault("zero_knowledge_compliant", None)
        parsed.setdefault("memory_relevance_score", None)
        parsed.setdefault("contradiction_handled_correctly", None)
        parsed.setdefault("refusal_correctness", None)
        parsed.setdefault("verdict", "reject")
        parsed.setdefault("error_type", "task_failure")
        parsed.setdefault("reasoning", "")
        return parsed


def build_validator(provider: str, api_key: str, model: str) -> ValidationJudge:
    if provider == "openai":
        return OpenAIValidationJudge(api_key=api_key, model=model)
    if provider == "groq":
        return GroqValidationJudge(api_key=api_key, model=model)
    raise ValueError(f"Unsupported validator provider: {provider}")


class ManagedBackend:
    def __init__(self, base_url: str, groq_api_key: str, output_dir: Path):
        self.base_url = normalize_base_url(base_url)
        self.host, self.port = parse_host_port_from_base_url(base_url)
        self.groq_api_key = groq_api_key
        self.output_dir = output_dir
        self.process: subprocess.Popen[str] | None = None
        self.log_path = output_dir / "managed_backend.log"
        self.log_handle = None

    def _python_executable(self) -> str:
        venv_python = repo_root() / "venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            return str(venv_python)
        return sys.executable

    def start(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_handle = self.log_path.open("a", encoding="utf-8")
        env = os.environ.copy()
        env["GROQ_API_KEY"] = self.groq_api_key
        env.setdefault("LLM_PROVIDER", "groq")
        env.setdefault("PYTHONIOENCODING", "utf-8")
        env.setdefault("PYTHONUTF8", "1")
        command = [
            self._python_executable(),
            "-m",
            "uvicorn",
            "app.main:app",
            "--app-dir",
            "backend",
            "--host",
            self.host,
            "--port",
            str(self.port),
        ]
        self.process = subprocess.Popen(
            command,
            cwd=str(repo_root()),
            env=env,
            stdout=self.log_handle,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self.wait_until_ready()

    def stop(self) -> None:
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        self.process = None
        if self.log_handle:
            self.log_handle.flush()
            self.log_handle.close()
            self.log_handle = None

    def restart_with_new_key(self, groq_api_key: str) -> None:
        self.stop()
        self.groq_api_key = groq_api_key
        self.start()

    def wait_until_ready(self) -> None:
        start_time = time.time()
        last_notice_at = 0.0
        while True:
            try:
                request = urllib.request.Request(f"{self.base_url}/api/v1/health/live", method="GET")
                with urllib.request.urlopen(request, timeout=5):
                    return
            except Exception:
                elapsed = time.time() - start_time
                if elapsed - last_notice_at >= 30:
                    print(f"Waiting for managed backend to become ready... ({int(elapsed)}s elapsed)")
                    last_notice_at = elapsed
                time.sleep(2)


def execute_with_retry(
    api_client: BackendApiClient,
    session_id: str,
    question: str,
    managed_backend: ManagedBackend | None = None,
    backend_wait_threshold_seconds: float = DEFAULT_BACKEND_WAIT_THRESHOLD_SECONDS,
) -> dict[str, Any]:
    retry_events = []
    last_status = None
    last_data: dict[str, Any] = {}
    last_raw = ""
    last_headers: dict[str, str] = {}
    start = time.time()
    cumulative_wait_seconds = 0.0
    for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
        status, data, raw, response_headers = api_client.query(session_id=session_id, question=question)
        last_status, last_data, last_raw, last_headers = status, data, raw, response_headers
        generation_error = extract_response_generation_error(data)
        app_retryable = (
            status < 400
            and isinstance(generation_error, dict)
            and generation_error.get("category") == "provider_rate_limit"
            and bool(generation_error.get("retryable"))
        )
        if status < 400:
            if app_retryable:
                retry_after = generation_error.get("retry_after_seconds")
                if retry_after is not None:
                    wait_seconds = min(MAX_BACKOFF_SECONDS, float(retry_after))
                else:
                    wait_seconds = min(
                        MAX_BACKOFF_SECONDS,
                        INITIAL_RETRY_DELAY_SECONDS * (2 ** (attempt - 1)) + random.uniform(0.0, 0.5),
                    )
                retry_events.append(
                    {
                        "attempt": attempt,
                        "status": status,
                        "reason": generation_error.get("message", "Provider rate limit wrapped by backend"),
                        "wait_seconds": round(wait_seconds, 2),
                        "retry_after_header": retry_after,
                        "application_error": generation_error,
                    }
                )
                cumulative_wait_seconds += wait_seconds
                if managed_backend is not None and cumulative_wait_seconds >= backend_wait_threshold_seconds:
                    print("\nBackend Groq key appears rate-limited for too long.")
                    new_key = prompt_if_missing(None, "Paste a new backend GROQ_API_KEY: ", secret=True)
                    managed_backend.restart_with_new_key(new_key)
                    cumulative_wait_seconds = 0.0
                    retry_events.append(
                        {
                            "attempt": attempt,
                            "status": status,
                            "reason": "Managed backend restarted with a newly supplied GROQ_API_KEY",
                            "wait_seconds": 0.0,
                            "retry_after_header": retry_after,
                            "application_error": generation_error,
                        }
                    )
                    continue
                time.sleep(wait_seconds)
                continue
            return {
                "final_status": "completed",
                "http_status": status,
                "response": data,
                "raw_response": raw,
                "response_headers": response_headers,
                "retry_events": retry_events,
                "retry_count": len(retry_events),
                "latency_ms": round((time.time() - start) * 1000, 2),
            }
        is_retryable = status == 429 or 500 <= status <= 599
        if not is_retryable:
            break
        retry_after = parse_retry_after_seconds(response_headers)
        if retry_after is not None:
            wait_seconds = min(MAX_BACKOFF_SECONDS, retry_after)
        else:
            wait_seconds = min(
                MAX_BACKOFF_SECONDS,
                INITIAL_RETRY_DELAY_SECONDS * (2 ** (attempt - 1)) + random.uniform(0.0, 0.5),
            )
        retry_events.append(
            {
                "attempt": attempt,
                "status": status,
                "reason": data.get("detail") if isinstance(data, dict) else str(data),
                "wait_seconds": round(wait_seconds, 2),
                "retry_after_header": retry_after,
            }
        )
        cumulative_wait_seconds += wait_seconds
        if (
            managed_backend is not None
            and status == 429
            and cumulative_wait_seconds >= backend_wait_threshold_seconds
        ):
            print("\nBackend Groq key appears rate-limited for too long.")
            new_key = prompt_if_missing(None, "Paste a new backend GROQ_API_KEY: ", secret=True)
            managed_backend.restart_with_new_key(new_key)
            cumulative_wait_seconds = 0.0
            retry_events.append(
                {
                    "attempt": attempt,
                    "status": status,
                    "reason": "Managed backend restarted with a newly supplied GROQ_API_KEY",
                    "wait_seconds": 0.0,
                    "retry_after_header": retry_after,
                }
            )
            continue
        time.sleep(wait_seconds)
    return {
        "final_status": "failed",
        "http_status": last_status,
        "response": last_data,
        "raw_response": last_raw,
        "response_headers": last_headers,
        "retry_events": retry_events,
        "retry_count": len(retry_events),
        "latency_ms": round((time.time() - start) * 1000, 2),
    }


def pick_message(messages: list[dict[str, Any]], message_id: str | None) -> dict[str, Any] | None:
    if not message_id:
        return None
    for message in messages:
        if str(message.get("id")) == str(message_id):
            return message
    return None


def build_rule_checks(
    turn: dict[str, Any],
    execution: dict[str, Any],
    session_messages: list[dict[str, Any]],
    memory_before: dict[str, Any],
    memory_after: dict[str, Any],
) -> dict[str, Any]:
    expected = turn.get("expected_behaviors", {})
    response = execution.get("response", {})
    user_message = pick_message(session_messages, response.get("user_message_id"))
    assistant_message = pick_message(session_messages, response.get("assistant_message_id"))
    before_keys = {fact.get("key") for fact in memory_before.get("facts", [])}
    after_keys = {fact.get("key") for fact in memory_after.get("facts", [])}
    fact_delta = len(after_keys - before_keys)
    preference_extracted = bool(user_message and user_message.get("extracted_preferences"))
    applied_preferences = bool(assistant_message and assistant_message.get("applied_preferences"))
    policy_claim_detected = bool(response.get("policy_claim_detected"))
    refusal_observed = bool(response.get("refused"))
    return {
        "source_count": len(response.get("sources") or []),
        "latency_ms": execution.get("latency_ms"),
        "response_received": execution.get("final_status") == "completed",
        "retry_count": execution.get("retry_count", 0),
        "retry_recovered": execution.get("final_status") == "completed" and execution.get("retry_count", 0) > 0,
        "session_message_count": len(session_messages),
        "preference_extracted": preference_extracted,
        "applied_preferences_detected": applied_preferences,
        "fact_count_before": len(before_keys),
        "fact_count_after": len(after_keys),
        "fact_count_delta": fact_delta,
        "policy_claim_detected": policy_claim_detected,
        "claim_detection_match": expected.get("expects_claim_detection") is None or expected.get("expects_claim_detection") == policy_claim_detected,
        "refusal_observed": refusal_observed,
        "refusal_match": expected.get("expects_refusal") is None or expected.get("expects_refusal") == refusal_observed,
        "risk_alert_count": len(response.get("risk_alerts") or []),
    }


def build_judge_payload(
    benchmark_session: dict[str, Any],
    turn: dict[str, Any],
    execution: dict[str, Any],
    rule_checks: dict[str, Any],
    history: list[dict[str, Any]],
) -> dict[str, Any]:
    response = execution.get("response", {})
    return {
        "session_id": benchmark_session["session_id"],
        "session_goal": benchmark_session["session_goal"],
        "turn_id": turn["turn_id"],
        "question": turn["question"],
        "objective": turn["objective"],
        "metric_tags": turn.get("metric_tags", []),
        "expected_behaviors": turn.get("expected_behaviors", {}),
        "history": history[-6:],
        "answer": response.get("answer"),
        "refused": response.get("refused"),
        "confidence": response.get("confidence"),
        "sources": response.get("sources") or [],
        "policy_claim_detected": response.get("policy_claim_detected"),
        "risk_alerts": response.get("risk_alerts") or [],
        "rule_checks": rule_checks,
    }


def compute_task_success(record: dict[str, Any]) -> bool:
    if record["execution"]["final_status"] != "completed":
        return False
    expected = record["expected_behaviors"]
    rules = record["rule_checks"]
    judge = record["judge"]
    if expected.get("expects_preference_extraction"):
        return rules["preference_extracted"]
    if expected.get("expects_fact_extraction"):
        return rules["fact_count_delta"] > 0
    if expected.get("expects_refusal"):
        return rules["refusal_match"] and bool(judge.get("refusal_correctness"))
    if expected.get("expects_claim_detection"):
        return rules["claim_detection_match"]
    if expected.get("expects_personalization"):
        return bool(judge.get("personalization_applied_correctly"))
    if expected.get("expects_memory_use"):
        return (judge.get("memory_relevance_score") or 0) >= 1
    if expected.get("expects_grounded_answer"):
        return judge.get("verdict") == "accept" and judge.get("groundedness_score", 0) >= 4 and not judge.get("hallucination_detected")
    return judge.get("verdict") == "accept"


def safe_rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 4)


def summarize_records(records: list[dict[str, Any]], run_metadata: dict[str, Any]) -> dict[str, Any]:
    successful = [r for r in records if r["execution"]["final_status"] == "completed"]
    latencies = [r["execution"]["latency_ms"] for r in successful]
    personalization_cases = [r for r in records if r["expected_behaviors"].get("expects_personalization")]
    zero_knowledge_cases = [r for r in records if r["expected_behaviors"].get("expects_zero_knowledge")]
    memory_cases = [r for r in records if r["expected_behaviors"].get("expects_memory_use")]
    grounded_cases = [r for r in records if r["expected_behaviors"].get("expects_grounded_answer")]
    refusal_cases = [r for r in records if r["expected_behaviors"].get("expects_refusal")]
    claim_cases = [r for r in records if r["expected_behaviors"].get("expects_claim_detection")]
    knowledge_cases = [r for r in records if "knowledge_evolution" in r["metric_tags"]]
    retries = [r for r in records if r["execution"].get("retry_count", 0) > 0]
    non_claim_cases = [r for r in records if not r["expected_behaviors"].get("expects_claim_detection")]
    false_claims = [r for r in non_claim_cases if r["rule_checks"].get("policy_claim_detected")]
    summary = {
        "run_metadata": run_metadata,
        "total_turns": len(records),
        "completed_turns": len(successful),
        "failed_turns": len(records) - len(successful),
        "average_latency_ms": round(mean(latencies), 2) if latencies else None,
        "p95_latency_ms": round(percentile(latencies, 95), 2) if latencies else None,
        "metrics": {
            "personalization_accuracy": safe_rate(
                sum(1 for r in personalization_cases if r["judge"].get("personalization_applied_correctly")),
                len(personalization_cases),
            ),
            "zero_knowledge_compliance": safe_rate(
                sum(1 for r in zero_knowledge_cases if r["judge"].get("zero_knowledge_compliant")),
                len(zero_knowledge_cases),
            ),
            "user_memory_relevance_score": round(
                mean([(r["judge"].get("memory_relevance_score") or 0) for r in memory_cases]), 3
            ) if memory_cases else None,
            "grounded_response_fidelity": safe_rate(
                sum(1 for r in grounded_cases if r["judge"].get("groundedness_score", 0) >= 4 and not r["judge"].get("hallucination_detected")),
                len(grounded_cases),
            ),
            "contradiction_resolution_rate": safe_rate(
                sum(1 for r in claim_cases if r["rule_checks"].get("claim_detection_match")),
                len(claim_cases),
            ),
            "knowledge_evolution_stability": safe_rate(
                sum(1 for r in knowledge_cases if r["rule_checks"].get("claim_detection_match", True) and r["execution"]["final_status"] == "completed"),
                len(knowledge_cases),
            ),
            "end_to_end_task_success_rate": safe_rate(
                sum(1 for r in records if compute_task_success(r)),
                len(records),
            ),
            "hallucination_rate": safe_rate(
                sum(1 for r in successful if r["judge"].get("hallucination_detected")),
                len(successful),
            ),
            "context_sufficiency_rate": safe_rate(
                sum(1 for r in successful if r["judge"].get("context_sufficiency_score", 0) >= 4),
                len(successful),
            ),
            "retry_recovery_rate": safe_rate(
                sum(1 for r in retries if r["execution"]["final_status"] == "completed"),
                len(retries),
            ),
            "refusal_correctness_rate": safe_rate(
                sum(1 for r in refusal_cases if r["judge"].get("refusal_correctness")),
                len(refusal_cases),
            ),
            "policy_claim_false_alarm_rate": safe_rate(len(false_claims), len(non_claim_cases)),
        },
        "failure_categories": {},
    }
    failures = [r["judge"].get("error_type", "task_failure") for r in records if not compute_task_success(r)]
    for item in failures:
        summary["failure_categories"][item] = summary["failure_categories"].get(item, 0) + 1
    return summary


def build_markdown_report(summary: dict[str, Any], records: list[dict[str, Any]], validator_model: str) -> str:
    metrics = summary["metrics"]
    good_examples = [r for r in records if compute_task_success(r)][:3]
    bad_examples = [r for r in records if not compute_task_success(r)][:3]
    provider = summary.get("run_metadata", {}).get("validator_provider", "unknown")
    lines = [
        "# Application Validation Report",
        "",
        f"- Generated at: {now_iso()}",
        f"- Validator provider: {provider}",
        f"- Validator model: `{validator_model}`",
        f"- Total turns: {summary['total_turns']}",
        f"- Completed turns: {summary['completed_turns']}",
        f"- Failed turns: {summary['failed_turns']}",
        "",
        "## Metric Summary",
        "",
        "| Metric | Value |",
        "| --- | --- |",
    ]
    for key, value in metrics.items():
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## Retry Summary",
            "",
            f"- Average latency (ms): {summary['average_latency_ms']}",
            f"- P95 latency (ms): {summary['p95_latency_ms']}",
            "",
            "## Strong Examples",
            "",
        ]
    )
    for record in good_examples:
        lines.append(f"- {record['benchmark_session_id']} {record['turn_id']}: {record['question']}")
    lines.extend(["", "## Weak Examples", ""])
    for record in bad_examples:
        lines.append(f"- {record['benchmark_session_id']} {record['turn_id']}: {record['question']}")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- The validator provider is configurable through the harness.",
            "- This report is updated incrementally from per-turn JSONL records.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_manual_review_report(records: list[dict[str, Any]]) -> str:
    lines = [
        "# Application Validation Manual Review",
        "",
        "This file is intended for later manual inspection of each evaluated turn.",
        "",
    ]
    for record in records:
        execution = record["execution"]
        response = execution.get("response", {})
        lines.extend(
            [
                f"## {record['benchmark_session_id']} {record['turn_id']}",
                "",
                f"- Question: {record['question']}",
                f"- Status: {execution.get('final_status')} ({execution.get('http_status')})",
                f"- Retry count: {execution.get('retry_count')}",
                f"- Latency ms: {execution.get('latency_ms')}",
                f"- Metric tags: {', '.join(record.get('metric_tags', []))}",
                f"- Judge verdict: {record['judge'].get('verdict')}",
                f"- Judge error type: {record['judge'].get('error_type')}",
                f"- Judge reasoning: {record['judge'].get('reasoning')}",
                "",
                "### Expected Behaviors",
                "",
                "```json",
                json.dumps(record.get("expected_behaviors", {}), ensure_ascii=True, indent=2),
                "```",
                "",
                "### Answer",
                "",
                response.get("answer", "(no answer captured)"),
                "",
                "### Sources",
                "",
                "```json",
                json.dumps(response.get("sources") or [], ensure_ascii=True, indent=2),
                "```",
                "",
                "### Rule Checks",
                "",
                "```json",
                json.dumps(record.get("rule_checks", {}), ensure_ascii=True, indent=2),
                "```",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def write_outputs(output_dir: Path, records: list[dict[str, Any]], summary: dict[str, Any], validator_model: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    records_path = output_dir / "application_validation_runs.jsonl"
    with records_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True, default=str) + "\n")
    (output_dir / "application_validation_summary.json").write_text(json_dumps(summary) + "\n", encoding="utf-8")
    (output_dir / "application_validation_summary.md").write_text(
        build_markdown_report(summary, records, validator_model=validator_model),
        encoding="utf-8",
    )
    (output_dir / "application_validation_manual_review.md").write_text(
        build_manual_review_report(records),
        encoding="utf-8",
    )


def load_existing_records(output_dir: Path) -> list[dict[str, Any]]:
    records_path = output_dir / "application_validation_runs.jsonl"
    if not records_path.exists():
        return []
    records = []
    for line in records_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def selected_sessions(filter_value: str | None) -> list[dict[str, Any]]:
    if not filter_value:
        return BENCHMARK_SESSIONS
    wanted = {item.strip() for item in filter_value.split(",") if item.strip()}
    return [item for item in BENCHMARK_SESSIONS if item["session_id"] in wanted]


def run_harness(args: argparse.Namespace) -> int:
    base_url = prompt_if_missing(args.base_url, "Backend base URL: ")
    jwt_token = prompt_if_missing(args.jwt_token, "Paste JWT token: ", secret=True)
    validator_key = prompt_if_missing(
        args.validator_api_key,
        f"Paste {args.validator_provider} validator API key: ",
        secret=True,
    )
    validator_model = args.validator_model or DEFAULT_VALIDATOR_MODEL
    output_dir = Path(args.output_dir or DEFAULT_OUTPUT_DIR)
    managed_backend = None
    if args.manage_backend:
        backend_key = prompt_if_missing(
            args.backend_groq_api_key,
            "Paste backend GROQ_API_KEY: ",
            secret=True,
        )
        managed_backend = ManagedBackend(base_url=base_url, groq_api_key=backend_key, output_dir=output_dir)
        managed_backend.start()

    try:
        api_client = BackendApiClient(base_url=base_url, jwt_token=jwt_token)
        auth_user = api_client.verify_auth()
        print(f"Authenticated as {auth_user.get('email')} ({auth_user.get('role')})")
        judge = build_validator(provider=args.validator_provider, api_key=validator_key, model=validator_model)
        benchmark = selected_sessions(args.sessions)
        if sum(len(item["turns"]) for item in benchmark) > TOTAL_TURNS:
            raise RuntimeError("Selected benchmark exceeded total turn count.")

        existing_records = load_existing_records(output_dir) if args.resume else []
        run_metadata = {
            "run_id": existing_records[0]["run_id"] if existing_records else datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
            "started_at": existing_records[0]["recorded_at"] if existing_records else now_iso(),
            "validator_provider": args.validator_provider,
            "validator_model": validator_model,
            "base_url": normalize_base_url(base_url),
            "authenticated_user": auth_user.get("email"),
            "resumed": bool(existing_records),
            "managed_backend": bool(managed_backend),
        }
        records: list[dict[str, Any]] = list(existing_records)
        completed_keys = {(r["benchmark_session_id"], r["turn_id"]) for r in existing_records}
        existing_backend_sessions = {
            r["benchmark_session_id"]: r["backend_session_id"]
            for r in existing_records
        }
        existing_histories: dict[str, list[dict[str, Any]]] = {}
        for record in existing_records:
            if record["execution"]["final_status"] == "completed":
                existing_histories.setdefault(record["benchmark_session_id"], []).append(
                    {
                        "question": record["question"],
                        "answer": record["execution"]["response"].get("answer"),
                        "refused": record["execution"]["response"].get("refused"),
                    }
                )
        for benchmark_session in benchmark:
            backend_session_id = existing_backend_sessions.get(benchmark_session["session_id"])
            if not backend_session_id:
                created_session = api_client.create_session()
                backend_session_id = created_session["session_id"]
            print(f"Running {benchmark_session['session_id']} -> backend session {backend_session_id}")
            history: list[dict[str, Any]] = list(existing_histories.get(benchmark_session["session_id"], []))
            try:
                memory_state = api_client.get_memory()
            except Exception:
                memory_state = {"facts": []}
            for turn in benchmark_session["turns"]:
                key = (benchmark_session["session_id"], turn["turn_id"])
                if key in completed_keys:
                    print(f"  {turn['turn_id']} -> skipped (already recorded)")
                    continue
                execution = execute_with_retry(
                    api_client,
                    backend_session_id,
                    turn["question"],
                    managed_backend=managed_backend,
                    backend_wait_threshold_seconds=args.backend_wait_threshold_seconds,
                )
                if execution["final_status"] == "completed":
                    messages_payload = api_client.get_session_messages(backend_session_id)
                    session_messages = messages_payload.get("messages", [])
                    try:
                        new_memory_state = api_client.get_memory()
                    except Exception:
                        new_memory_state = memory_state
                    rule_checks = build_rule_checks(turn, execution, session_messages, memory_before=memory_state, memory_after=new_memory_state)
                    judge_payload = build_judge_payload(benchmark_session, turn, execution, rule_checks, history=history)
                    judge_result = judge.judge(judge_payload)
                    memory_state = new_memory_state
                    history.append({"question": turn["question"], "answer": execution["response"].get("answer"), "refused": execution["response"].get("refused")})
                else:
                    rule_checks = {
                        "source_count": 0,
                        "latency_ms": execution["latency_ms"],
                        "response_received": False,
                        "retry_count": execution["retry_count"],
                        "retry_recovered": False,
                        "session_message_count": len(history) * 2,
                        "preference_extracted": False,
                        "applied_preferences_detected": False,
                        "fact_count_before": len(memory_state.get("facts", [])),
                        "fact_count_after": len(memory_state.get("facts", [])),
                        "fact_count_delta": 0,
                        "policy_claim_detected": False,
                        "claim_detection_match": not turn.get("expected_behaviors", {}).get("expects_claim_detection", False),
                        "refusal_observed": False,
                        "refusal_match": not turn.get("expected_behaviors", {}).get("expects_refusal", False),
                        "risk_alert_count": 0,
                    }
                    judge_result = {
                        "groundedness_score": 1,
                        "hallucination_detected": False,
                        "answer_relevance_score": 1,
                        "completeness_score": 1,
                        "context_sufficiency_score": 1,
                        "personalization_applied_correctly": None,
                        "zero_knowledge_compliant": None,
                        "memory_relevance_score": None,
                        "contradiction_handled_correctly": None,
                        "refusal_correctness": None,
                        "verdict": "reject",
                        "error_type": "task_failure",
                        "reasoning": "No API response after retry budget.",
                    }
                record = {
                    "run_id": run_metadata["run_id"],
                    "recorded_at": now_iso(),
                    "benchmark_session_id": benchmark_session["session_id"],
                    "backend_session_id": backend_session_id,
                    "turn_id": turn["turn_id"],
                    "question": turn["question"],
                    "objective": turn["objective"],
                    "metric_tags": turn["metric_tags"],
                    "expected_behaviors": turn["expected_behaviors"],
                    "execution": execution,
                    "rule_checks": rule_checks,
                    "judge": judge_result,
                }
                records.append(record)
                completed_keys.add(key)
                summary = summarize_records(records, run_metadata=run_metadata)
                write_outputs(output_dir, records, summary, validator_model=validator_model)
                print(f"  {turn['turn_id']} -> {execution['final_status']} ({execution['http_status']})")
        final_summary = summarize_records(records, run_metadata=run_metadata)
        write_outputs(output_dir, records, final_summary, validator_model=validator_model)
        print(f"Completed {len(records)} turns. Summary written to {output_dir}")
        return 0
    finally:
        if managed_backend is not None:
            managed_backend.stop()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run application validation benchmark.")
    parser.add_argument("--base-url")
    parser.add_argument("--jwt-token")
    parser.add_argument("--validator-provider", default=DEFAULT_VALIDATOR_PROVIDER)
    parser.add_argument("--validator-api-key")
    parser.add_argument("--validator-model", default=DEFAULT_VALIDATOR_MODEL)
    parser.add_argument("--manage-backend", action="store_true", help="Start and manage the backend as a quiet subprocess.")
    parser.add_argument("--backend-groq-api-key", help="Initial GROQ_API_KEY for the managed backend subprocess.")
    parser.add_argument(
        "--backend-wait-threshold-seconds",
        type=float,
        default=DEFAULT_BACKEND_WAIT_THRESHOLD_SECONDS,
        help="After this much cumulative 429 wait for one turn, prompt for a new backend GROQ_API_KEY and restart the managed backend.",
    )
    parser.add_argument("--output-dir")
    parser.add_argument("--sessions", help="Comma-separated benchmark session ids to run.")
    parser.add_argument("--resume", action="store_true", help="Resume from the existing JSONL log in the output directory.")
    return parser


if __name__ == "__main__":
    sys.exit(run_harness(build_parser().parse_args()))
