"""
General Data Analyzer Extension Script

Purpose:
- Accept flexible CSV or JSON tabular data
- Infer structure without requiring a fixed schema
- Tolerate missing values and mixed columns
- Produce a compact statistical profile so the assistant can answer user queries

This is designed as a more general replacement for the current grade analyzer.
"""

import csv
import json
import math
from io import StringIO


def process(file_data: bytes, session_id: str, user_id: str) -> dict:
    """
    Handler for generic tabular data analysis.
    """
    try:
        content = file_data.decode("utf-8-sig", errors="replace")
        rows, metadata = _parse_input(content)

        if not rows:
            return {
                "result_type": "error",
                "error": "No tabular records could be parsed from the uploaded file.",
                "help": (
                    "Upload a CSV or JSON file containing rows/records/items/data."
                ),
            }

        analysis = _analyze_rows(rows, metadata)
        prompt = _build_analysis_prompt(analysis)

        return {
            "result_type": "general_data_analysis",
            "session_id": session_id,
            "analysis": analysis,
            "prompt": prompt,
            "metadata": {
                "row_count": analysis.get("row_count", 0),
                "column_count": analysis.get("column_count", 0),
                "numeric_column_count": len(analysis.get("numeric_columns", [])),
                "categorical_column_count": len(analysis.get("categorical_columns", [])),
                "primary_metric": analysis.get("primary_metric"),
                "entity_column": analysis.get("entity_column"),
                "source_format": metadata.get("source_format", "unknown"),
            },
        }

    except Exception as e:
        return {
            "result_type": "error",
            "error": f"Processing error: {str(e)}",
            "details": "Ensure the uploaded file is valid CSV or JSON.",
        }


def _parse_input(content: str) -> tuple:
    """
    Parse JSON or CSV-like tabular data.
    """
    try:
        parsed = json.loads(content)
        rows = _extract_json_rows(parsed)
        if rows:
            return rows, {"source_format": "json"}
    except json.JSONDecodeError:
        pass

    rows = _parse_delimited_text(content)
    return rows, {"source_format": "csv"}


def _extract_json_rows(parsed) -> list:
    """
    Extract rows from common JSON shapes.
    """
    if isinstance(parsed, list):
        if all(isinstance(item, dict) for item in parsed):
            return [_normalize_row(item) for item in parsed]
        return []

    if isinstance(parsed, dict):
        for key in ["rows", "records", "data", "items", "students", "results"]:
            value = parsed.get(key)
            if isinstance(value, list) and all(isinstance(item, dict) for item in value):
                return [_normalize_row(item) for item in value]

        if all(not isinstance(v, (list, dict)) for v in parsed.values()):
            return [_normalize_row(parsed)]

    return []


def _parse_delimited_text(content: str) -> list:
    """
    Parse CSV/TSV using csv.Sniffer with fallback.
    """
    sample = content[:4096]
    delimiter = ","
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        delimiter = dialect.delimiter
    except Exception:
        pass

    reader = csv.DictReader(StringIO(content), delimiter=delimiter)
    rows = []
    for row in reader:
        if not row:
            continue
        normalized = _normalize_row(row)
        if any(str(v).strip() for v in normalized.values()):
            rows.append(normalized)
    return rows


def _normalize_row(row: dict) -> dict:
    """
    Normalize column names and raw values.
    """
    normalized = {}
    for key, value in row.items():
        clean_key = str(key).strip() if key is not None else ""
        if not clean_key:
            continue
        normalized[clean_key] = _normalize_value(value)
    return normalized


def _normalize_value(value):
    if value is None:
        return None
    if isinstance(value, (int, float, bool)):
        return value

    text = str(value).strip()
    if text == "":
        return None

    lowered = text.lower()
    if lowered in {"na", "n/a", "null", "none", "-", "--"}:
        return None

    numeric = _to_number(text)
    if numeric is not None:
        return numeric

    return text


def _to_number(value: str):
    cleaned = value.replace(",", "").replace("%", "").strip()
    try:
        num = float(cleaned)
        if num.is_integer():
            return int(num)
        return num
    except Exception:
        return None


def _analyze_rows(rows: list, metadata: dict) -> dict:
    columns = _collect_columns(rows)
    column_profile = _profile_columns(rows, columns)

    numeric_columns = [
        col["name"] for col in column_profile if col["inferred_type"] == "numeric"
    ]
    categorical_columns = [
        col["name"] for col in column_profile if col["inferred_type"] == "categorical"
    ]

    entity_column = _choose_entity_column(column_profile, categorical_columns)
    primary_metric = _choose_primary_metric(column_profile, numeric_columns)

    record_summaries = _summarize_records(rows, entity_column, primary_metric)
    grouped_summaries = _group_summaries(rows, column_profile, primary_metric)
    missing_summary = _missing_summary(column_profile)

    return {
        "source_format": metadata.get("source_format", "unknown"),
        "row_count": len(rows),
        "column_count": len(columns),
        "columns": column_profile,
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "entity_column": entity_column,
        "primary_metric": primary_metric,
        "primary_metric_summary": _metric_summary(rows, primary_metric),
        "top_records": record_summaries.get("top", []),
        "bottom_records": record_summaries.get("bottom", []),
        "grouped_summaries": grouped_summaries,
        "missing_value_summary": missing_summary,
        "data_quality_notes": _data_quality_notes(column_profile),
    }


def _collect_columns(rows: list) -> list:
    ordered = []
    seen = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                ordered.append(key)
                seen.add(key)
    return ordered


def _profile_columns(rows: list, columns: list) -> list:
    profiles = []
    total_rows = len(rows)

    for name in columns:
        values = [row.get(name) for row in rows]
        non_null = [v for v in values if v is not None]
        numeric_values = [v for v in non_null if isinstance(v, (int, float)) and not isinstance(v, bool)]
        text_values = [v for v in non_null if isinstance(v, str)]

        inferred_type = "categorical"
        if non_null and len(numeric_values) >= max(2, math.ceil(len(non_null) * 0.6)):
            inferred_type = "numeric"

        unique_count = len({str(v) for v in non_null})
        missing_count = total_rows - len(non_null)

        profile = {
            "name": name,
            "inferred_type": inferred_type,
            "non_null_count": len(non_null),
            "missing_count": missing_count,
            "missing_percentage": round((missing_count / total_rows) * 100, 2) if total_rows else 0,
            "unique_count": unique_count,
        }

        if inferred_type == "numeric":
            summary = _numeric_stats(numeric_values)
            profile.update(summary)
        else:
            profile["top_values"] = _top_text_values(text_values)

        profiles.append(profile)

    return profiles


def _numeric_stats(values: list) -> dict:
    if not values:
        return {"mean": None, "median": None, "min": None, "max": None}

    ordered = sorted(float(v) for v in values)
    count = len(ordered)
    mid = count // 2
    if count % 2 == 0:
        median = (ordered[mid - 1] + ordered[mid]) / 2
    else:
        median = ordered[mid]

    mean = sum(ordered) / count
    variance = sum((x - mean) ** 2 for x in ordered) / count if count else 0

    return {
        "mean": round(mean, 2),
        "median": round(median, 2),
        "min": round(min(ordered), 2),
        "max": round(max(ordered), 2),
        "std_deviation": round(variance ** 0.5, 2),
    }


def _top_text_values(values: list) -> list:
    counts = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    ordered = sorted(counts.items(), key=lambda item: (-item[1], str(item[0]).lower()))
    return [{"value": key, "count": count} for key, count in ordered[:5]]


def _choose_entity_column(column_profile: list, categorical_columns: list):
    preferred_keywords = [
        "name", "student", "roll", "id", "employee", "customer", "product", "item",
    ]

    for keyword in preferred_keywords:
        for col in categorical_columns:
            if keyword in col.lower():
                return col

    candidates = []
    for profile in column_profile:
        if profile["inferred_type"] != "categorical":
            continue
        if profile["unique_count"] <= 1:
            continue
        candidates.append(profile)

    if not candidates:
        return None

    candidates.sort(key=lambda item: (-item["unique_count"], item["missing_count"]))
    return candidates[0]["name"]


def _choose_primary_metric(column_profile: list, numeric_columns: list):
    preferred_keywords = [
        "total", "score", "marks", "mark", "grade", "cgpa", "gpa",
        "revenue", "sales", "amount", "value", "profit", "performance",
    ]

    for keyword in preferred_keywords:
        for col in numeric_columns:
            if keyword in col.lower():
                return col

    numeric_profiles = [p for p in column_profile if p["name"] in numeric_columns]
    if not numeric_profiles:
        return None

    numeric_profiles.sort(
        key=lambda item: (
            -(item.get("std_deviation") or 0),
            -(item.get("mean") or 0),
        )
    )
    return numeric_profiles[0]["name"]


def _metric_summary(rows: list, metric_name: str):
    if not metric_name:
        return None

    values = []
    for row in rows:
        value = row.get(metric_name)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            values.append(float(value))

    if not values:
        return None

    return _numeric_stats(values)


def _summarize_records(rows: list, entity_column, primary_metric: str) -> dict:
    if not primary_metric:
        return {"top": [], "bottom": []}

    scored = []
    for row in rows:
        metric_value = row.get(primary_metric)
        if not isinstance(metric_value, (int, float)) or isinstance(metric_value, bool):
            continue

        label = row.get(entity_column) if entity_column else None
        scored.append(
            {
                "entity": label if label is not None else "(record)",
                "metric_value": round(float(metric_value), 2),
                "key_details": _record_key_details(row, primary_metric, entity_column),
            }
        )

    scored.sort(key=lambda item: item["metric_value"], reverse=True)
    return {
        "top": scored[:5],
        "bottom": list(reversed(scored[-5:])) if scored else [],
    }


def _record_key_details(row: dict, primary_metric: str, entity_column):
    details = {}
    for key, value in row.items():
        if key == primary_metric or key == entity_column:
            continue
        if value is None:
            continue
        details[key] = value
        if len(details) >= 4:
            break
    return details


def _group_summaries(rows: list, column_profile: list, primary_metric: str) -> list:
    if not primary_metric:
        return []

    candidates = []
    for profile in column_profile:
        if profile["inferred_type"] != "categorical":
            continue
        unique_count = profile["unique_count"]
        if 2 <= unique_count <= 12:
            candidates.append(profile["name"])

    summaries = []
    for col in candidates[:3]:
        grouped = {}
        for row in rows:
            key = row.get(col)
            metric_value = row.get(primary_metric)
            if key is None or not isinstance(metric_value, (int, float)) or isinstance(metric_value, bool):
                continue
            grouped.setdefault(str(key), []).append(float(metric_value))

        if not grouped:
            continue

        bucket_stats = []
        for key, values in grouped.items():
            bucket_stats.append(
                {
                    "group": key,
                    "count": len(values),
                    "mean": round(sum(values) / len(values), 2),
                }
            )

        bucket_stats.sort(key=lambda item: (-item["mean"], -item["count"]))
        summaries.append(
            {
                "column": col,
                "groups": bucket_stats[:8],
            }
        )

    return summaries


def _missing_summary(column_profile: list) -> list:
    ordered = sorted(
        column_profile,
        key=lambda item: (-item["missing_percentage"], item["name"].lower()),
    )
    return [
        {
            "column": item["name"],
            "missing_count": item["missing_count"],
            "missing_percentage": item["missing_percentage"],
        }
        for item in ordered[:8]
        if item["missing_count"] > 0
    ]


def _data_quality_notes(column_profile: list) -> list:
    notes = []
    for profile in column_profile:
        if profile["missing_percentage"] >= 40:
            notes.append(
                f"Column '{profile['name']}' has high missingness ({profile['missing_percentage']}%)."
            )
        if profile["inferred_type"] == "categorical" and profile["unique_count"] == 1:
            notes.append(
                f"Column '{profile['name']}' has the same value in all rows."
            )
    return notes[:8]


def _build_analysis_prompt(analysis: dict) -> str:
    compact = json.dumps(analysis, ensure_ascii=True, separators=(",", ":"))

    return f"""You are a practical data analyst helping a faculty/user understand an uploaded dataset.

You have already been given a structured profile of the uploaded data.
Use this profile as the main source for answering the user's question.

DATA PROFILE:
{compact}

WHAT YOU SHOULD DO:
1. Answer the user's current question using the data profile.
2. If the user asks for tables, rankings, averages, weak areas, concentration areas, trends, or summaries, use the provided top_records, bottom_records, grouped_summaries, and primary_metric_summary.
3. If the dataset looks like student performance data, naturally discuss strong performers, weak performers, and where improvement is needed.
4. If the dataset is not academic, still answer in a general analytical way based on the same profile.

IMPORTANT RULES:
- Do not claim to see columns or rows that are not listed in the profile.
- If the user's request needs row-level detail that is not in the profile, say that the uploaded summary does not preserve every individual detail.
- Be specific, practical, and concise.
- Prefer tables when the user asks for comparison/ranking.
- Mention missing-value limitations when they affect the conclusion.
- For exact row-level filtering, tabulation, ranking, threshold, grouping, or exploration queries, include a fenced ```python``` block.
- This extension is strictly for dataframe-based analysis and tabular/code outputs.
- Never generate plots, charts, dashboards, Plotly figures, matplotlib, or seaborn code.
- Never assign anything to `fig` or `plotly_figure`.
- If the user asks for visualization, stay analytical and provide a table/statistical summary instead.
- The runtime already provides:
  - `df`: a pandas DataFrame loaded from the uploaded file
  - `rows`: a list of dictionaries derived from `df`
  - `file_name` and `file_text`
- Prefer `df` and pandas for analysis. Use `rows` only if truly simpler.
- NEVER create a sample dataset, NEVER redefine `df` or `rows`, and NEVER hardcode example values.
- Always compute counts, names, rankings, and summaries from the runtime data itself, not from the profile text.
- Never say the output is truncated unless your code explicitly truncates it.
- In that code, assign the final printable markdown/text output to a variable named `result_markdown`.
- When returning tables, use pandas for filtering/sorting and then render a clean text/markdown table from the real filtered result.
"""
