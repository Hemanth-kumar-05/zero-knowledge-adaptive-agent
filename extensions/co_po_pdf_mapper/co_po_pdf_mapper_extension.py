"""
Unified CO-PO PDF Mapper Extension

This script combines the current helper and mapper flows into one extension:
1. Read the uploaded PDF
2. Extract and normalize relevant academic text
3. Parse structured course / CO / PO / PSO data into JSON
4. Build a direct mapping prompt so the assistant can return the final CO-PO map

The goal is to avoid sending noisy raw PDF text to the model when possible.
Instead, the extension pushes a compact structured JSON representation plus only
the most relevant raw snippets needed to finish the mapping.
"""

import json
import re


def process(file_data: bytes, session_id: str, user_id: str) -> dict:
    """
    Main extension handler.

    Args:
        file_data: Uploaded PDF content as bytes
        session_id: Current session ID
        user_id: Current user ID

    Returns:
        dict with a direct mapping prompt for the assistant
    """
    pdf_text, extract_method = _extract_pdf_text(file_data)

    if not pdf_text.strip():
        return {
            "result_type": "error",
            "error": (
                "Could not extract readable text from the uploaded PDF. "
                "Please upload a PDF with selectable text."
            ),
        }

    normalized_text = _normalize_text(pdf_text)
    structured_data = _build_structured_course_data(normalized_text)
    compact_data = _compact_structured_data(structured_data)
    mapping_prompt = _build_direct_mapping_prompt(compact_data)

    return {
        "result_type": "co_po_pdf_mapping_request",
        "session_id": session_id,
        "extraction_method": extract_method,
        "pdf_text_length": len(pdf_text),
        "structured_data": compact_data,
        "mapping_prompt": mapping_prompt,
        "instruction": (
            "Use the parsed JSON as the primary source and produce the final CO-PO/PSO mapping output."
        ),
        "metadata": {
            "course_code": compact_data["course_info"].get("course_code", ""),
            "course_name": compact_data["course_info"].get("course_name", ""),
            "co_count": len(compact_data.get("course_outcomes", [])),
            "po_count": len(compact_data.get("programme_outcomes", [])),
            "pso_count": len(compact_data.get("programme_specific_outcomes", [])),
        },
    }


def _extract_pdf_text(file_data: bytes) -> tuple:
    """
    Cascading PDF text extraction with graceful fallback.
    """
    from io import BytesIO

    try:
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(file_data))
        pages = []
        for i, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(f"\n--- Page {i} ---\n{text}")
        if pages:
            return "\n".join(pages), "pypdf"
    except Exception:
        pass

    try:
        import PyPDF2

        reader = PyPDF2.PdfReader(BytesIO(file_data))
        pages = []
        for i, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(f"\n--- Page {i} ---\n{text}")
        if pages:
            return "\n".join(pages), "PyPDF2"
    except Exception:
        pass

    try:
        from pdfminer.high_level import extract_text as pm_extract

        text = pm_extract(BytesIO(file_data))
        if text.strip():
            return text, "pdfminer"
    except Exception:
        pass

    try:
        import pdfplumber

        pages = []
        with pdfplumber.open(BytesIO(file_data)) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""
                if text.strip():
                    pages.append(f"\n--- Page {i} ---\n{text}")
        if pages:
            return "\n".join(pages), "pdfplumber"
    except Exception:
        pass

    try:
        raw = file_data.decode("latin-1", errors="replace")
        clean = re.sub(r"[^\x20-\x7E\n\r\t]", " ", raw)
        clean = re.sub(r"[ \t]{2,}", " ", clean)
        clean = re.sub(r"\n{3,}", "\n\n", clean)
        if len(clean.strip()) > 200:
            return clean, "raw-decode"
    except Exception:
        pass

    return "", "none"


def _normalize_text(text: str) -> str:
    """
    Normalize whitespace and common OCR/PDF artifacts without losing content.
    """
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ ]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _build_structured_course_data(text: str) -> dict:
    """
    Parse relevant PDF content into a structured JSON object.

    This parser is intentionally heuristic. It aims to extract the data needed
    for mapping while preserving raw snippets so the assistant can recover from
    partial parsing.
    """
    course_info = _extract_course_info(text)
    cos = _extract_course_outcomes(text)
    pos = _extract_programme_outcomes(text)
    psos = _extract_programme_specific_outcomes(text)

    relevant_sections = {
        "course_info_snippet": _extract_context_window(
            text, ["course code", "course title", "course name", "credits", "semester", "department"], 2200
        ),
        "co_snippet": _extract_context_window(
            text, ["course outcomes", "co1", "co 1"], 5000
        ),
        "po_snippet": _extract_context_window(
            text, ["programme outcomes", "program outcomes", "po1", "po 1"], 8000
        ),
        "pso_snippet": _extract_context_window(
            text, ["programme specific outcomes", "program specific outcomes", "pso1", "pso 1"], 5000
        ),
    }

    return {
        "course_info": course_info,
        "course_outcomes": cos,
        "programme_outcomes": pos,
        "programme_specific_outcomes": psos,
        "relevant_sections": relevant_sections,
        "extraction_notes": {
            "parser": "heuristic_pdf_parser",
            "co_count": len(cos),
            "po_count": len(pos),
            "pso_count": len(psos),
            "needs_llm_completion": any(
                not course_info.get(key)
                for key in ["course_code", "course_name", "department"]
            ) or not cos or not pos,
        },
    }


def _compact_structured_data(data: dict) -> dict:
    """
    Shrink the payload before it goes to Groq.

    Strategy:
    - keep only the core fields needed for mapping
    - trim long descriptions
    - drop raw snippets unless extraction looks incomplete
    """
    course_info = {
        "course_code": _trim_text(data.get("course_info", {}).get("course_code", ""), 40),
        "course_name": _trim_text(data.get("course_info", {}).get("course_name", ""), 160),
        "semester": data.get("course_info", {}).get("semester", 0),
        "credits": data.get("course_info", {}).get("credits", 0),
        "department": _trim_text(data.get("course_info", {}).get("department", ""), 120),
    }

    course_outcomes = []
    for co in data.get("course_outcomes", [])[:12]:
        course_outcomes.append(
            {
                "co_id": co.get("co_id", ""),
                "description": _trim_text(co.get("description", ""), 280),
            }
        )

    programme_outcomes = []
    for po in data.get("programme_outcomes", [])[:20]:
        programme_outcomes.append(
            {
                "po_id": po.get("po_id", ""),
                "title": _trim_text(po.get("title", ""), 80),
                "description": _trim_text(po.get("description", ""), 220),
            }
        )

    programme_specific_outcomes = []
    for pso in data.get("programme_specific_outcomes", [])[:10]:
        programme_specific_outcomes.append(
            {
                "pso_id": pso.get("pso_id", ""),
                "description": _trim_text(pso.get("description", ""), 220),
            }
        )

    extraction_notes = data.get("extraction_notes", {})
    needs_llm_completion = bool(extraction_notes.get("needs_llm_completion"))

    compact = {
        "course_info": course_info,
        "course_outcomes": course_outcomes,
        "programme_outcomes": programme_outcomes,
        "programme_specific_outcomes": programme_specific_outcomes,
        "extraction_notes": {
            "parser": extraction_notes.get("parser", "heuristic_pdf_parser"),
            "needs_llm_completion": needs_llm_completion,
        },
    }

    if needs_llm_completion:
        relevant_sections = data.get("relevant_sections", {})
        compact["relevant_sections"] = {
            "course_info_snippet": _trim_text(relevant_sections.get("course_info_snippet", ""), 800),
            "co_snippet": _trim_text(relevant_sections.get("co_snippet", ""), 1600),
            "po_snippet": _trim_text(relevant_sections.get("po_snippet", ""), 1800),
            "pso_snippet": _trim_text(relevant_sections.get("pso_snippet", ""), 1000),
        }

    return compact


def _extract_course_info(text: str) -> dict:
    course_code = _first_match(
        text,
        [
            r"course\s*code\s*[:\-]\s*([A-Z]{2,}[0-9]{3,}[A-Z0-9]*)",
            r"subject\s*code\s*[:\-]\s*([A-Z]{2,}[0-9]{3,}[A-Z0-9]*)",
            r"\b([A-Z]{2,}[0-9]{3,}[A-Z0-9]*)\b",
        ],
    )

    course_name = _first_match(
        text,
        [
            r"course\s*(?:title|name)\s*[:\-]\s*([^\n]+)",
            r"subject\s*(?:title|name)\s*[:\-]\s*([^\n]+)",
        ],
    )
    if course_name:
        course_name = _clean_line(course_name)

    semester = _first_int(
        text,
        [
            r"semester\s*[:\-]\s*(\d+)",
            r"sem\s*[:\-]\s*(\d+)",
        ],
    )

    credits = _first_int(
        text,
        [
            r"credits?\s*[:\-]\s*(\d+)",
            r"credit\s*value\s*[:\-]\s*(\d+)",
        ],
    )

    department = _first_match(
        text,
        [
            r"department\s*[:\-]\s*([^\n]+)",
            r"programme\s*[:\-]\s*([^\n]+engineering[^\n]*)",
        ],
    )
    if department:
        department = _clean_line(department)

    return {
        "course_code": course_code or "",
        "course_name": course_name or "",
        "semester": semester or 0,
        "credits": credits or 0,
        "department": department or "",
    }


def _extract_course_outcomes(text: str) -> list:
    outcomes = _extract_labeled_items(text, "CO")
    return [{"co_id": item["id"], "description": item["description"]} for item in outcomes]


def _extract_programme_outcomes(text: str) -> list:
    outcomes = _extract_labeled_items(text, "PO")
    results = []
    for item in outcomes:
        title, description = _split_title_and_description(item["description"])
        results.append(
            {
                "po_id": item["id"],
                "title": title,
                "description": description,
                "competencies": [],
            }
        )
    return results


def _extract_programme_specific_outcomes(text: str) -> list:
    outcomes = _extract_labeled_items(text, "PSO")
    return [
        {
            "pso_id": item["id"],
            "description": item["description"],
            "competencies": [],
        }
        for item in outcomes
    ]


def _extract_labeled_items(text: str, prefix: str) -> list:
    """
    Extract labeled blocks such as CO1, PO2, PSO3 across the document.
    """
    pattern = re.compile(
        rf"(?is)\b({prefix}\s*-?\s*\d+)\b\s*[:.\-]?\s*(.+?)(?=\n\s*(?:{prefix}\s*-?\s*\d+)\b|\Z)"
    )
    items = []
    seen_ids = set()

    for match in pattern.finditer(text):
        item_id = re.sub(r"\s+", "", match.group(1).upper())
        description = _clean_block(match.group(2))
        if not description:
            continue
        if item_id in seen_ids:
            continue
        seen_ids.add(item_id)
        items.append({"id": item_id, "description": description})

    return items


def _split_title_and_description(text: str) -> tuple:
    """
    Split PO text into a short title and description when possible.
    """
    clean = _clean_block(text)
    if not clean:
        return "", ""

    for separator in [":", "-", "–"]:
        if separator in clean:
            left, right = clean.split(separator, 1)
            left = _clean_line(left)
            right = _clean_line(right)
            if 2 <= len(left.split()) <= 6 and right:
                return left, right

    words = clean.split()
    if len(words) <= 8:
        return clean, clean

    title = " ".join(words[:4])
    description = clean
    return title, description


def _extract_context_window(text: str, needles: list, max_chars: int) -> str:
    """
    Extract a compact raw snippet around the first useful heading/keyword.
    """
    lower = text.lower()
    start = None
    for needle in needles:
        index = lower.find(needle.lower())
        if index != -1:
            start = index
            break

    if start is None:
        return ""

    end = min(len(text), start + max_chars)
    return text[start:end].strip()


def _first_match(text: str, patterns: list) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def _first_int(text: str, patterns: list) -> int:
    value = _first_match(text, patterns)
    try:
        return int(value)
    except Exception:
        return 0


def _clean_line(value: str) -> str:
    value = re.sub(r"\s+", " ", value or "").strip(" .:-\n\t")
    return value


def _clean_block(value: str) -> str:
    value = value or ""
    value = value.replace("\r", "\n")
    value = re.sub(r"\n{2,}", "\n", value)
    lines = [_clean_line(line) for line in value.split("\n")]
    lines = [line for line in lines if line]
    return " ".join(lines).strip()


def _trim_text(value: str, max_chars: int) -> str:
    value = _clean_block(value)
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 3].rstrip() + "..."


def _build_direct_mapping_prompt(structured_data: dict) -> str:
    """
    Build the final prompt that asks the assistant to perform mapping directly.
    """
    compact_json = json.dumps(structured_data, ensure_ascii=True, separators=(",", ":"))

    return f"""You are an engineering curriculum assessor.

You have been given structured data parsed from a course PDF. The extension has already extracted the relevant academic content into JSON so you should use that JSON as the PRIMARY source for mapping.

STRUCTURED COURSE DATA:
{compact_json}

TASK:
1. Review the parsed course_info, course_outcomes, programme_outcomes, and programme_specific_outcomes.
2. If some fields are incomplete and relevant_sections exists, use ONLY those snippets to complete your reasoning.
3. Map every CO against every PO and every PSO.
4. Use the attainment scale:
   0 = No correlation
   1 = Low correlation
   2 = Medium correlation
   3 = High correlation
5. For each mapping, provide a brief justification of 5-12 words.

OUTPUT FORMAT:
- Start with a short course summary.
- Then provide a complete CO-PO mapping matrix.
- Then provide a complete CO-PSO mapping matrix if PSOs exist.
- Then provide concise observations:
  * strongest alignments
  * weak or missing alignments
  * curriculum improvement suggestions

STRICT RULES:
- Do not skip any CO.
- Do not skip any PO.
- If PSOs exist, do not skip any PSO.
- Do not ask the user for intermediate JSON.
- Produce the final mapping directly in this response.
- If some extracted fields are blank, continue using the available structured data and clearly note assumptions briefly.
- Keep the response compact and focused on the final matrices.
"""
