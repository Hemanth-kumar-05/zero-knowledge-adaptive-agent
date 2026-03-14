"""
CO-PO Mapping Helper Extension Script

Reads an uploaded PDF (course syllabus, lab manual, or programme document)
and builds a structured prompt that directs the assistant to output a valid
co_po_mapping JSON object matching the exact input format expected by the
CO-PO Mapper extension.

Handler  : process
Dependencies: pypdf, PyPDF2, pdfminer.six, pdfplumber (all optional, cascaded fallback)
"""

import json
import re

# ---------------------------------------------------------------------------
# Canonical JSON schema shown to the LLM as a strict reference template.
# Field names must not change — they match sample_data.json exactly.
# ---------------------------------------------------------------------------
_SCHEMA = """{
  "course_info": {
    "course_code": "<string>",
    "course_name": "<string>",
    "semester": <integer>,
    "credits": <integer>,
    "department": "<string>"
  },
  "course_outcomes": [
    { "co_id": "CO1", "description": "<string>" },
    { "co_id": "CO2", "description": "<string>" }
  ],
  "programme_outcomes": [
    {
      "po_id": "PO1",
      "title": "<string>",
      "description": "<string>",
      "competencies": [
        {
          "competency_id": "1.1",
          "description": "<string>",
          "indicators": [
            { "indicator_id": "1.1.1", "description": "<string>" },
            { "indicator_id": "1.1.2", "description": "<string>" }
          ]
        }
      ]
    }
  ],
  "programme_specific_outcomes": [
    {
      "pso_id": "PSO1",
      "description": "<string>",
      "competencies": [
        {
          "competency_id": "1.1",
          "description": "<string>",
          "indicators": [
            { "indicator_id": "1.1.1", "description": "<string>" }
          ]
        }
      ]
    }
  ]
}"""


def process(file_data: bytes, session_id: str, user_id: str) -> dict:
    """
    Handler function for CO-PO Mapping Helper extension.

    Extracts text from the uploaded PDF then builds a structured LLM prompt
    that causes the assistant to output a co_po_mapping JSON object.

    Args:
        file_data : Uploaded PDF content as bytes.
        session_id: Current session ID.
        user_id   : ID of the requesting user.

    Returns:
        dict with result_type='co_po_json_builder' and mapping_prompt key.
    """
    pdf_text, extract_method = _extract_pdf_text(file_data)

    if not pdf_text.strip():
        return {
            "result_type": "error",
            "error": (
                "Could not extract readable text from the uploaded PDF. "
                "Please ensure the PDF contains selectable text (not a scanned image only). "
                "If the document is scanned, try copying the text manually into a .txt file."
            ),
        }

    mapping_prompt = _build_prompt(pdf_text)

    return {
        "result_type": "co_po_json_builder",
        "session_id": session_id,
        "extraction_method": extract_method,
        "pdf_text_length": len(pdf_text),
        "mapping_prompt": mapping_prompt,
        "instruction": (
            "Parse the extracted PDF text and output a valid co_po_mapping JSON object "
            "ready for use with the CO-PO Mapper extension."
        ),
    }


# ---------------------------------------------------------------------------
# PDF text extraction — cascades through multiple libraries gracefully
# ---------------------------------------------------------------------------

def _extract_pdf_text(file_data: bytes) -> tuple:
    """
    Try multiple PDF extraction approaches in order of preference.

    Returns:
        (extracted_text: str, method_used: str)
    """
    from io import BytesIO

    # ── Attempt 1: pypdf (modern, maintained) ──────────────────────────────
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
    except ImportError:
        pass
    except Exception:
        pass

    # ── Attempt 2: PyPDF2 (older alias, may be installed) ─────────────────
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
    except ImportError:
        pass
    except Exception:
        pass

    # ── Attempt 3: pdfminer.six ───────────────────────────────────────────
    try:
        from pdfminer.high_level import extract_text as pm_extract
        text = pm_extract(BytesIO(file_data))
        if text.strip():
            return text, "pdfminer"
    except ImportError:
        pass
    except Exception:
        pass

    # ── Attempt 4: pdfplumber ─────────────────────────────────────────────
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
    except ImportError:
        pass
    except Exception:
        pass

    # ── Attempt 5: raw latin-1 decode (last resort for embedded ASCII PDFs)
    try:
        raw = file_data.decode("latin-1", errors="replace")
        # Remove non-printable characters, collapse excessive whitespace
        clean = re.sub(r"[^\x20-\x7E\n\r\t]", " ", raw)
        clean = re.sub(r"[ \t]{4,}", " ", clean)
        clean = re.sub(r"\n{4,}", "\n\n", clean)
        if len(clean.strip()) > 200:
            return clean[:20000], "raw-decode"
    except Exception:
        pass

    return "", "none"


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _build_prompt(pdf_text: str) -> str:
    """
    Build the full extraction prompt that is passed as context to the LLM.
    """
    # Guard against token overflow — keep the most relevant first portion
    # MAX_CHARS = 12000
    # truncated = False
    # if len(pdf_text) > MAX_CHARS:
    #     pdf_text = pdf_text[:MAX_CHARS]
    #     truncated = True

    # truncation_note = (
    #     "\n[Note: Document was truncated to fit context window. "
    #     "Extract as much as is visible above.]\n"
    #     if truncated else ""
    # )

    prompt = f"""You are given raw text extracted from an engineering faculty document (course/lab/programme outline).

Your task is to parse this text and output a SINGLE, complete, valid JSON object that will be used as input for the CO-PO Mapper tool.

REQUIRED JSON SCHEMA — reproduce every field name exactly as shown:
{_SCHEMA}

FIELD EXTRACTION RULES:
1. course_info
   - course_code  : e.g. "CS0001", "EC3401" — look for codes near the course name
   - course_name  : full subject / lab name as stated in the document
   - semester     : integer (1–8); extract from document or infer from year/semester label
   - credits      : integer; look for "Credits:", "L-T-P", or credit value near course info
   - department   : full department name (e.g. "Computer Science and Engineering")

2. course_outcomes (COs)
   - List every CO found; keep the original CO number label (CO1, CO2, …)
   - description  : full sentence as written in the document

3. programme_outcomes (POs)
   - List every PO found (typically PO1–PO12 for NBA-accredited programmes)
   - po_id        : "PO1", "PO2", … exactly
   - title        : short label (e.g. "Engineering Knowledge")
   - description  : full PO statement
   - competencies : list sub-competencies if present; if absent use []
     Each competency: {{ "competency_id": "1.1", "description": "...", "indicators": [...] }}
     Each indicator : {{ "indicator_id": "1.1.1", "description": "..." }}

4. programme_specific_outcomes (PSOs)
   - List every PSO; if none are present in the document use []
   - pso_id       : "PSO1", "PSO2", …
   - description  : full PSO statement
   - competencies : same nested structure as POs; use [] if absent

IMPORTANT OUTPUT RULES:
- Output ONLY raw JSON. No markdown code fences (no ```), no explanation, no preamble.
- Output compact JSON (minified, no indentation, no extra line breaks) to reduce token usage.
- "semester" and "credits" MUST be integers, not strings.
- If a required field is not found in the document: use "" for strings, 0 for integers, [] for arrays.
- Do NOT invent outcomes that are not in the document.
- Do NOT omit outcomes that ARE in the document.
- If output length risk is high, still prioritize FULL JSON completeness over readability.
- Never stop at PO11/PO12 mid-way. Ensure valid closing brackets/braces are present.

--- EXTRACTED DOCUMENT TEXT BEGIN ---
{pdf_text}
--- EXTRACTED DOCUMENT TEXT END ---

Now output the JSON object:"""

    return prompt
