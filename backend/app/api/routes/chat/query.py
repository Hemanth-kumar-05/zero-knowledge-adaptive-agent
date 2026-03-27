# POST /api/v1/query endpoint
from fastapi import APIRouter, HTTPException, Depends, File, Form, UploadFile, Request
import re

from app.api.schemas.query import QueryRequest, QueryResponse, CodeRepairRequest, CodeRepairResponse
from app.services.query_service import query_service
from app.core.auth_middleware import get_optional_user
from typing import Optional, Dict
from rag.generate import Generator

query_router = APIRouter()


def _extract_python_code(text: str) -> str:
    if not text:
        return ""
    match = re.search(r"```(?:python|py)\s*([\s\S]*?)```", text, re.IGNORECASE)
    return (match.group(1) if match else text).strip()

@query_router.post("/query", response_model=QueryResponse)
async def query(
    http_request: Request,
    current_user: Optional[Dict] = Depends(get_optional_user),
    question: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """
    Handle user query and return answer with sources.
    Supports both JSON and multipart/form-data (with file upload).
    """
    # Add user_id to request if authenticated
    user_id = current_user.get("user_id") if current_user else None
    
    # Check content type to determine how to parse request
    content_type = http_request.headers.get("content-type", "")
    
    # Handle multipart/form-data (with or without file)
    if "multipart/form-data" in content_type:
        if not question or not session_id:
            raise HTTPException(status_code=400, detail="Missing question or session_id in form data")
        
        # Create request from form data
        req = QueryRequest(question=question, session_id=session_id)
        
        if file:
            # File upload case - read file content
            file_content = await file.read()
            file_data = {
                "filename": file.filename,
                "content": file_content,
                "content_type": file.content_type
            }
            response = await query_service.query(req, user_id=user_id, file_data=file_data)
        else:
            # Form data without file
            response = await query_service.query(req, user_id=user_id)
    
    # Handle JSON request
    elif "application/json" in content_type:
        body = await http_request.json()
        request_obj = QueryRequest(**body)
        response = await query_service.query(request_obj, user_id=user_id)
    
    else:
        raise HTTPException(status_code=400, detail="Invalid content type. Use application/json or multipart/form-data")
    
    if isinstance(response, str):
        raise HTTPException(status_code=400, detail=response)
    return response


@query_router.post("/query/code-repair", response_model=CodeRepairResponse)
async def repair_code(
    request: CodeRepairRequest,
    current_user: Optional[Dict] = Depends(get_optional_user),
):
    """
    Repair AI-generated Python code for browser-side dataset execution.
    Returns only corrected Python code.
    """
    _ = current_user  # Auth is optional, but keep middleware consistent.

    generator = Generator()
    dataset_preview = (request.dataset_preview or "")[:6000]
    full_traceback = request.traceback or request.error
    extension_name = (request.extension_name or "").strip()
    extra_plotly_hint = ""
    if "Invalid element(s) received for the 'data' property" in full_traceback and "Invalid elements include: [Figure(" in full_traceback:
        extra_plotly_hint = """
Specific Plotly guidance for this traceback:
- Do not pass full Figure objects inside another Figure's `data=[...]`
- A Figure's `data` must contain traces, not nested Figure instances
- If combining multiple chart sections, either:
  - use `make_subplots()` and `add_trace(...)`, or
  - build one `go.Figure()` and add traces directly
- If using Plotly Express, extract traces with `for trace in fig.data:`
"""

    extension_rules = ""
    if "general data analyzer" in extension_name.lower():
        extension_rules = """
Extension-specific rule:
- The active extension is General Data Analyzer
- Do not generate any plots, charts, dashboards, Plotly, matplotlib, or seaborn code
- Return dataframe/table/statistical analysis only
- Assign the final user-facing output to `result_markdown`
"""
    elif "visualization" in extension_name.lower():
        extension_rules = """
Extension-specific rule:
- The active extension is a visualization extension
- Prefer Plotly figures as the primary output
"""

    repair_prompt = f"""
You repair Python code that runs against uploaded tabular data in a browser sandbox.

Important runtime facts:
- The dataset is already loaded in:
  - `df`: a pandas DataFrame created from the uploaded CSV/JSON
  - `rows`: a list of dictionaries derived from `df`
  - `file_name` and `file_text`
- Additional inspection helpers are available:
  - `df_columns`
  - `df_shape`
  - `df_head`
  - `df_numeric_summary`
- Prefer using `df` and pandas for analysis
- Do not redefine `df`, `rows`, `file_name`, `file_text`, or the helper inspection variables
- Do not create sample data
- If the user's request is for a chart or visualization:
  - use Python `plotly.graph_objects` or `plotly.express`
  - if the user asks for multiple charts, create multiple figures and call `fig.show()` for each, or build one subplot/dashboard figure
  - do not stop after the first chart when the request clearly asks for several plots
  - if only one figure is created, assign the resulting figure to `fig` or `plotly_figure`
  - keep `result_markdown` empty or very short
  - apply clear styling with titles, labels, readable colors, and a consistent theme
- Do not import matplotlib or seaborn
- Return ONLY corrected Python code, with no explanations or markdown fences

User query:
{request.question}

Uploaded file:
{request.file_name or "dataset"}

Active extension:
{extension_name or "unknown"}

Dataset preview:
{dataset_preview}

Current broken code:
{request.code}

FULL PYTHON TRACEBACK:
{full_traceback}

{extra_plotly_hint}
{extension_rules}

Repair the code so it works on the actual uploaded data, preferably through `df`, and answers the query faithfully.
"""

    fixed = generator.generate(
        query="Repair the Python code for runtime dataset execution.",
        context=repair_prompt,
        conversation_history=None,
        preference_instructions=None,
        user_context=None,
        extension_system_prompt=(
            "You are a Python repair assistant for browser sandbox execution with pandas available. "
            "Return only valid Python code. Do not explain. Do not wrap code in markdown."
        ),
        max_tokens=2048,
    )

    cleaned = _extract_python_code(fixed)
    if not cleaned:
        raise HTTPException(status_code=500, detail="Code repair failed to return corrected Python.")

    return CodeRepairResponse(fixed_code=cleaned)
