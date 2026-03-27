"""
Data Visualization Studio Extension Script

Purpose:
- Accept flexible CSV or JSON tabular data
- Profile the uploaded dataset for visualization-oriented analysis
- Guide the LLM to generate Python code at runtime for charting/exploration
- Work with the existing frontend auto-execution and AI auto-fix loop

This extension is intentionally prompt-driven, like the general data analyzer,
so the LLM can generate chart logic dynamically based on the user's request.
"""

import csv
import json
from io import StringIO


def process(file_data: bytes, session_id: str, user_id: str) -> dict:
    """
    Handler for flexible visualization-oriented data exploration.
    """
    try:
        content = file_data.decode("utf-8-sig", errors="replace")
        rows, metadata = _parse_input(content)

        if not rows:
            return {
                "result_type": "error",
                "error": "No tabular records could be parsed from the uploaded file.",
                "help": "Upload a CSV or JSON file containing rows, records, items, or data.",
            }

        profile = _build_visual_profile(rows, metadata)
        prompt = _build_visualization_prompt(profile)

        return {
            "result_type": "data_visualization_studio",
            "session_id": session_id,
            "visual_profile": profile,
            "prompt": prompt,
            "metadata": {
                "row_count": profile.get("row_count", 0),
                "column_count": profile.get("column_count", 0),
                "numeric_column_count": len(profile.get("numeric_columns", [])),
                "categorical_column_count": len(profile.get("categorical_columns", [])),
                "date_like_column_count": len(profile.get("date_like_columns", [])),
                "source_format": metadata.get("source_format", "unknown"),
            },
        }

    except Exception as exc:
        return {
            "result_type": "error",
            "error": f"Processing error: {str(exc)}",
            "details": "Ensure the uploaded file is valid CSV or JSON.",
        }


def _parse_input(content: str):
    try:
        parsed = json.loads(content)
        rows = _extract_json_rows(parsed)
        if rows:
            return rows, {"source_format": "json"}
    except json.JSONDecodeError:
        pass

    rows = _parse_delimited_text(content)
    return rows, {"source_format": "csv"}


def _extract_json_rows(parsed):
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


def _parse_delimited_text(content: str):
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


def _normalize_row(row):
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


def _build_visual_profile(rows, metadata):
    columns = _collect_columns(rows)
    profiles = [_profile_column(rows, name) for name in columns]

    numeric_columns = [item["name"] for item in profiles if item["inferred_type"] == "numeric"]
    categorical_columns = [item["name"] for item in profiles if item["inferred_type"] == "categorical"]
    date_like_columns = [item["name"] for item in profiles if item["inferred_type"] == "date_like"]

    return {
        "source_format": metadata.get("source_format", "unknown"),
        "row_count": len(rows),
        "column_count": len(columns),
        "columns": profiles,
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "date_like_columns": date_like_columns,
        "recommended_visualizations": _recommend_visualizations(
            numeric_columns, categorical_columns, date_like_columns
        ),
        "sample_records": rows[:3],
    }


def _collect_columns(rows):
    ordered = []
    seen = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                ordered.append(key)
    return ordered


def _profile_column(rows, name):
    values = [row.get(name) for row in rows]
    non_null = [value for value in values if value is not None]
    numeric_values = [
        value for value in non_null
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    ]
    text_values = [value for value in non_null if isinstance(value, str)]

    inferred_type = "categorical"
    if non_null and len(numeric_values) >= max(2, int(len(non_null) * 0.6)):
        inferred_type = "numeric"
    elif _looks_date_like(text_values):
        inferred_type = "date_like"

    unique_count = len({str(value) for value in non_null})
    summary = {
        "name": name,
        "inferred_type": inferred_type,
        "non_null_count": len(non_null),
        "missing_count": len(rows) - len(non_null),
        "unique_count": unique_count,
    }

    if inferred_type == "numeric" and numeric_values:
        ordered = sorted(float(value) for value in numeric_values)
        summary.update({
            "min": round(min(ordered), 2),
            "max": round(max(ordered), 2),
            "mean": round(sum(ordered) / len(ordered), 2),
        })
    else:
        summary["top_values"] = _top_values(text_values)

    return summary


def _looks_date_like(values):
    if not values:
        return False

    hits = 0
    for value in values[:20]:
        text = str(value).strip()
        if not text:
            continue
        if (
            "-" in text or "/" in text or
            any(month in text.lower() for month in [
                "jan", "feb", "mar", "apr", "may", "jun",
                "jul", "aug", "sep", "oct", "nov", "dec"
            ])
        ):
            hits += 1

    return hits >= max(2, min(5, len(values[:20])))


def _top_values(values):
    counts = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    ordered = sorted(counts.items(), key=lambda item: (-item[1], str(item[0]).lower()))
    return [{"value": key, "count": count} for key, count in ordered[:5]]


def _recommend_visualizations(numeric_columns, categorical_columns, date_like_columns):
    recommendations = []

    if numeric_columns:
        recommendations.append({
            "chart": "histogram",
            "why": "Useful for showing the distribution of a numeric column.",
            "columns": numeric_columns[:2],
        })

    if numeric_columns and categorical_columns:
        recommendations.append({
            "chart": "bar_chart",
            "why": "Useful for comparing average numeric values across categories.",
            "columns": [categorical_columns[0], numeric_columns[0]],
        })
        recommendations.append({
            "chart": "box_plot",
            "why": "Useful for spotting spread and outliers by category.",
            "columns": [categorical_columns[0], numeric_columns[0]],
        })

    if len(numeric_columns) >= 2:
        recommendations.append({
            "chart": "scatter_plot",
            "why": "Useful for relationships between two numeric columns.",
            "columns": numeric_columns[:2],
        })
        recommendations.append({
            "chart": "correlation_heatmap",
            "why": "Useful for comparing how numeric columns move together.",
            "columns": numeric_columns[:6],
        })

    if date_like_columns and numeric_columns:
        recommendations.append({
            "chart": "line_chart",
            "why": "Useful for trends over time or ordered periods.",
            "columns": [date_like_columns[0], numeric_columns[0]],
        })

    if not recommendations:
        recommendations.append({
            "chart": "table",
            "why": "Fallback when the dataset is too sparse or irregular for a strong chart recommendation.",
            "columns": [],
        })

    return recommendations


def _build_visualization_prompt(profile):
    compact = json.dumps(profile, ensure_ascii=True, separators=(",", ":"))

    return f"""You are a data visualization assistant helping a faculty/user explore an uploaded dataset.

You have been given a structured visualization profile of the uploaded data.
Use that profile to understand the dataset shape, but for exact answers generate runtime Python code.

VISUAL DATA PROFILE:
{compact}

WHAT YOU SHOULD DO:
1. Answer the user's visualization or exploration request clearly.
2. For exact analysis, plotting, filtering, ranking, grouping, trend, or comparison requests, include a fenced ```python``` block.
3. The frontend will auto-run that Python code in a sandbox and auto-repair it if execution fails.

RUNTIME FACTS:
- `df` is already available as a pandas DataFrame from the uploaded file.
- `rows` is also available as a list of dictionaries derived from `df`.
- `file_name` and `file_text` are available.
- Additional inspection helpers are available:
  - `df_columns`
  - `df_shape`
  - `df_head`
  - `df_numeric_summary`
- Do not redefine `df`, `rows`, `file_name`, `file_text`, or the helper inspection variables.
- Never create sample data.
- Prefer `df` and pandas for filtering, grouping, sorting, aggregation, and exploratory analysis.

VISUALIZATION RULES:
- Use pandas to inspect and derive the chart data from the real uploaded dataset.
- Prefer Python `plotly.graph_objects` or `plotly.express` for interactive chart design.
- `plotly` is available inside the sandbox.
- When creating charts, build real Plotly figures.
- If the user asks for multiple plots, generate as many figures as needed.
- You may either:
  - create one combined subplot/dashboard figure, or
  - create multiple figures and call `fig.show()` for each one in sequence.
- The frontend can render multiple Plotly figures from repeated `fig.show()` calls.
- If you are creating only one figure, assign it to either:
  - `fig`, or
  - `plotly_figure`
- Do not use matplotlib or seaborn.
- If you use Plotly, the frontend will render only the figure itself.
- Do not include long markdown explanations for chart requests.
- Always derive values from the runtime data, not from the profile text alone.
- If the user asks for a chart, produce code that:
  - computes the correct grouped/filtered dataframe,
  - builds a clean Plotly figure,
  - and assigns it to `fig` or `plotly_figure`.
- If the user asks for multiple named plots, do not stop after the first chart.
- Match the exact number of requested plots unless the data makes one impossible.
- Apply clear styling:
  - readable titles
  - axis labels
  - legends where useful
  - modern color palette
  - consistent template such as `plotly_dark`, `plotly_white`, or another deliberate theme
  - appropriate sizing and spacing
- If the user asks for a dashboard-like response, build the figure(s) first and keep any supporting text minimal.

OUTPUT RULES:
- For visualization requests, the figure or figures are the primary output.
- Keep `result_markdown` empty unless a very short caption is truly necessary.
- Do not mention truncation unless your code explicitly truncates output.
"""
