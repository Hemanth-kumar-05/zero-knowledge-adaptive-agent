"""
Authentication Routes
Google OAuth and JWT token management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import File, Form, UploadFile
from fastapi.responses import RedirectResponse
from google.oauth2 import id_token
from google.auth.transport import requests
from typing import Dict, List, Optional
import json
import os
import re
import base64
import mimetypes
import io
import importlib
from datetime import datetime
from config import Config
from app.api.schemas.auth import (
    GoogleAuthRequest,
    GoogleCallbackRequest,
    TokenResponse,
    UserInfo,
    MessageResponse
)
from app.db.mongo import get_db
from app.db.repositories.users_repo import UsersRepository
from app.services.user_service import UserService
from app.utils.auth import AuthUtils
from app.core.auth_middleware import get_current_user
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

try:
    from groq import Groq
except Exception:
    Groq = None


ALLOWED_ID_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}
GROQ_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_VISION_MODEL = os.getenv("GROQ_VISION_MODEL", GROQ_MODEL)
GROQ_ENABLED = GROQ_PROVIDER == "groq" and bool(GROQ_API_KEY) and Groq is not None
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_ENABLED else None
OCR_ENGINE_CACHE = None


def _get_ocr_engine():
    """Lazily initialize OCR stack so dependencies remain optional."""
    global OCR_ENGINE_CACHE
    if OCR_ENGINE_CACHE is not None:
        return OCR_ENGINE_CACHE

    try:
        np_module = importlib.import_module("numpy")
        pil_image = importlib.import_module("PIL.Image")
        rapidocr_module = importlib.import_module("rapidocr_onnxruntime")
        engine = rapidocr_module.RapidOCR()
        OCR_ENGINE_CACHE = (engine, np_module, pil_image)
        return OCR_ENGINE_CACHE
    except Exception as e:
        logger.warning(f"OCR dependencies unavailable: {e}")
        OCR_ENGINE_CACHE = False
        return OCR_ENGINE_CACHE


def _is_allowed_id_file(filename: str) -> bool:
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_ID_EXTENSIONS


def _extract_json_object(raw_text: str) -> Dict:
    text = (raw_text or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        block = match.group(0).replace("'", '"')
        return json.loads(block)


def _heuristic_extract(scan_text: str, expected_role: str = "") -> Dict[str, str]:
    combined = (scan_text or "").lower()
    role = "unknown"
    if "faculty" in combined or "staff" in combined or "prof" in combined:
        role = "faculty"
    elif "student" in combined or "roll" in combined or "semester" in combined:
        role = "student"

    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", scan_text or "")
    id_match = re.search(r"\b[0-9]{2}[a-zA-Z][0-9]{3}\b|\b(emp|staff)[-_ ]?[0-9]{3,6}\b", scan_text or "", re.IGNORECASE)
    name_match = re.search(r"name\s*[:\-]\s*([A-Za-z .]{3,80})", scan_text or "", re.IGNORECASE)

    return {
        "id_type": role,
        "id_name": name_match.group(1).strip() if name_match else "",
        "roll_or_emp_id": id_match.group(0).strip().lower().replace(" ", "") if id_match else "",
        "ai_summary": "Heuristic extraction used",
        "ai_mode": "heuristic",
    }


def _extract_with_groq(
    scan_text: str,
    google_email: str,
    claimed_name: str,
    expected_role: str,
    image_data_urls: Optional[List[str]] = None,
) -> Dict[str, str]:
    image_data_urls = image_data_urls or []

    if not (scan_text or "").strip() and not image_data_urls:
        return {
            "id_type": "unknown",
            "id_name": "",
            "roll_or_emp_id": "",
            "institutional_email": "",
            "ai_summary": "No OCR text extracted from uploaded image",
            "ai_mode": "no_ocr",
        }

    if not GROQ_ENABLED or groq_client is None:
        return _heuristic_extract(scan_text, expected_role)

    payload = {
        "google_email": google_email,
        "claimed_name": claimed_name,
        "ocr_text": scan_text,
        "expected_role": expected_role,
    }
    prompt = (
        "Extract identity fields from OCR text and return strict JSON with keys "
        "id_type,id_name,roll_or_emp_id,institutional_email,ai_summary. "
        "id_type must be one of student/faculty/unknown. Use empty strings for missing values. "
        "Do not invent values. If OCR text is unrelated/non-ID, return unknown and empty fields. "
        "Use claimed_name and expected_role as user-claimed identity context for consistency checking. Input: "
        + json.dumps(payload, ensure_ascii=True)
    )

    completion = None
    vision_unavailable = False

    if image_data_urls:
        user_content = [{"type": "text", "text": prompt}]
        for data_url in image_data_urls[:2]:
            user_content.append({"type": "image_url", "image_url": {"url": data_url}})

        try:
            completion = groq_client.chat.completions.create(
                model=GROQ_VISION_MODEL,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are a strict JSON extractor."},
                    {"role": "user", "content": user_content},
                ],
            )
        except Exception as vision_error:
            vision_unavailable = True
            logger.warning(f"Groq vision extraction failed, falling back safely: {vision_error}")

            # If no OCR text is available, we cannot validate image content safely.
            if not (scan_text or "").strip():
                return {
                    "id_type": "unknown",
                    "id_name": "",
                    "roll_or_emp_id": "",
                    "institutional_email": "",
                    "ai_summary": "Vision model unavailable and no OCR text provided",
                    "ai_mode": "no_ocr",
                }

    if completion is None:
        try:
            completion = groq_client.chat.completions.create(
                model=GROQ_MODEL,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are a strict JSON extractor."},
                    {"role": "user", "content": prompt},
                ],
            )
        except Exception:
            completion = groq_client.chat.completions.create(
                model=GROQ_MODEL,
                temperature=0,
                messages=[
                    {"role": "system", "content": "Return valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
            )

    parsed = _extract_json_object(completion.choices[0].message.content)
    id_type = str(parsed.get("id_type", "")).strip().lower()
    if id_type not in {"student", "faculty", "unknown"}:
        id_type = "unknown"

    return {
        "id_type": id_type,
        "id_name": str(parsed.get("id_name", "")).strip(),
        "roll_or_emp_id": str(parsed.get("roll_or_emp_id", "")).strip().lower(),
        "institutional_email": str(parsed.get("institutional_email", "")).strip().lower(),
        "ai_summary": str(parsed.get("ai_summary", "")).strip() or "Groq extraction completed",
        "ai_mode": "groq_vision" if image_data_urls and not vision_unavailable else "groq",
    }


def _generate_failure_feedback(
    *,
    claimed_name: str,
    expected_role: str,
    extracted: Dict[str, str],
    trust_score: int,
    has_back: bool,
    has_valid_id_code: bool,
    name_matches_claim: bool,
    role_matches_claim: bool,
    internal_reasons: List[str],
) -> List[str]:
    """Generate user-facing verification feedback, preferring AI output with safe fallback."""
    fallback_feedback = [
        "Failure reason: The uploaded proof is not sufficient for confident verification.",
        "What AI expects: Upload a clear ID image with readable full name and roll/employee ID.",
    ]

    if not GROQ_ENABLED or groq_client is None:
        return fallback_feedback

    context_payload = {
        "claimed_name": claimed_name,
        "expected_role": expected_role,
        "trust_score": trust_score,
        "has_back_image": has_back,
        "has_valid_id_code": has_valid_id_code,
        "name_matches_claim": name_matches_claim,
        "role_matches_claim": role_matches_claim,
        "extracted": {
            "id_type": extracted.get("id_type", ""),
            "id_name": extracted.get("id_name", ""),
            "roll_or_emp_id": extracted.get("roll_or_emp_id", ""),
            "ai_mode": extracted.get("ai_mode", ""),
            "ai_summary": extracted.get("ai_summary", ""),
        },
        "internal_reasons": internal_reasons,
    }

    prompt = (
        "You are generating feedback for failed ID verification. "
        "Return JSON only with key failure_feedback containing 2 to 6 short lines. "
        "Each line must start with either 'Failure reason:' or 'What AI expects:'. "
        "Be specific to mismatches (person/role/readability) from the provided context and avoid technical jargon. "
        "Input: " + json.dumps(context_payload, ensure_ascii=True)
    )

    try:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You produce strict JSON only."},
                {"role": "user", "content": prompt},
            ],
        )
        parsed = _extract_json_object(completion.choices[0].message.content)
        feedback = parsed.get("failure_feedback", [])
        if isinstance(feedback, list):
            cleaned = [str(item).strip() for item in feedback if str(item).strip()]
            if cleaned:
                return cleaned[:6]
    except Exception as e:
        logger.warning(f"Failed to generate AI failure feedback, using fallback: {e}")

    return fallback_feedback


def _score_verification(
    google_email: str,
    google_name: str,
    id_type: str,
    id_name: str,
    roll_or_emp_id: str,
    institutional_email: str,
    has_front: bool,
    has_back: bool,
) -> tuple[int, list[str]]:
    score = 0
    reasons = []

    if has_front and has_back:
        score += 15
        reasons.append("Front and back ID evidence provided")
    elif has_front or has_back:
        score += 8
        reasons.append("Partial ID evidence provided")

    g_name = (google_name or "").strip().lower()
    i_name = (id_name or "").strip().lower()
    name_match = bool(g_name and i_name and (g_name in i_name or i_name in g_name))
    if name_match:
        score += 20
        reasons.append("Google name and extracted ID name are consistent")

    if "@" in google_email and not google_email.endswith("@psgtech.ac.in"):
        score -= 5
        reasons.append("Google account is personal domain (allowed with penalty)")

    if id_type == "student":
        score += 15
        reasons.append("ID classified as student")
    elif id_type == "faculty":
        score += 18
        reasons.append("ID classified as faculty")

    if roll_or_emp_id:
        score += 5
        reasons.append("Roll or employee ID provided")

    return max(0, min(100, score)), reasons


def _extract_ocr_text_from_images(read_buffers: List[bytes], uploads: List[UploadFile]) -> str:
    """Run local OCR on uploaded image buffers and return merged text."""
    ocr_stack = _get_ocr_engine()
    if not ocr_stack:
        return ""

    ocr_engine, np_module, pil_image = ocr_stack

    extracted_lines: List[str] = []
    for idx, file_bytes in enumerate(read_buffers):
        if not file_bytes:
            continue

        filename = (uploads[idx].filename or "").lower() if idx < len(uploads) else ""
        content_type = (uploads[idx].content_type or "").lower() if idx < len(uploads) else ""
        is_image = content_type.startswith("image/") or filename.endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp"))
        if not is_image:
            continue

        try:
            image = pil_image.open(io.BytesIO(file_bytes)).convert("RGB")
            img_np = np_module.array(image)
            ocr_result, _ = ocr_engine(img_np)
            if ocr_result:
                for item in ocr_result:
                    if len(item) >= 2 and item[1]:
                        extracted_lines.append(str(item[1]).strip())
        except Exception as e:
            logger.warning(f"Local OCR failed for image index {idx}: {e}")

    merged_text = "\n".join(line for line in extracted_lines if line)
    return merged_text.strip()


def _is_strong_identity_proof(
    google_email: str,
    google_name: str,
    id_type: str,
    id_name: str,
    roll_or_emp_id: str,
    institutional_email: str,
    has_front: bool,
) -> tuple[bool, list[str]]:
    """Require independent evidence from uploaded proof before verification passes."""
    checks = []
    failures = []

    if has_front:
        checks.append("ID image uploaded")
    else:
        failures.append("No readable ID image evidence")

    if id_type in {"student", "faculty"}:
        checks.append("Role identified from ID evidence")
    else:
        failures.append("ID role not identifiable")

    g_name = (google_name or "").strip().lower()
    i_name = (id_name or "").strip().lower()
    if g_name and i_name and (g_name in i_name or i_name in g_name):
        checks.append("ID name matches Google name")
    else:
        failures.append("ID name missing or mismatch")

    has_valid_id_code = bool(re.match(r"^[a-z0-9._\-]{3,}$", (roll_or_emp_id or "").strip().lower()))

    if has_valid_id_code:
        checks.append("Roll/employee ID extracted from proof")

    if not has_valid_id_code:
        failures.append("No roll/employee ID found in uploaded proof")

    return len(failures) == 0, checks + failures


@router.post("/google", response_model=Dict)
async def initiate_google_auth(request: GoogleAuthRequest):
    """
    Initiate Google OAuth flow
    Returns the Google OAuth URL for frontend redirect
    """
    # Build Google OAuth URL
    scopes = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ]
    scope_param = "%20".join(scopes)
    oauth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={Config.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={Config.GOOGLE_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope={scope_param}&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    
    return {"auth_url": oauth_url}


@router.get("/google/callback")
async def google_callback(code: str = None, error: str = None, db=Depends(get_db)):
    """
    Handle Google OAuth callback
    Exchange authorization code for user info and generate JWT
    """
    try:
        # Check for OAuth errors
        if error:
            logger.error(f"OAuth error from Google: {error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Authentication failed: {error}"
            )
        
        if not code:
            logger.error("No authorization code received")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No authorization code received"
            )
        
        logger.info("Processing Google OAuth callback with code")
        
        # Validate config
        if not Config.GOOGLE_CLIENT_ID or not Config.GOOGLE_CLIENT_SECRET:
            logger.error("Google OAuth credentials not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OAuth not configured properly"
            )
        
        # Exchange authorization code for tokens
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import Flow
        import os
        
        # Create OAuth flow
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": Config.GOOGLE_CLIENT_ID,
                    "client_secret": Config.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [Config.GOOGLE_REDIRECT_URI]
                }
            },
            scopes=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile"
            ]
        )
        flow.redirect_uri = Config.GOOGLE_REDIRECT_URI
        
        logger.info(f"Using redirect URI: {Config.GOOGLE_REDIRECT_URI}")
        
        # Exchange code for tokens
        try:
            flow.fetch_token(code=code)
            credentials = flow.credentials
            logger.info("Successfully exchanged code for tokens")
        except Exception as token_error:
            logger.error(f"Token exchange failed: {str(token_error)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to exchange authorization code: {str(token_error)}"
            )
        
        # Verify the ID token with clock skew tolerance
        try:
            # Add 60 seconds of clock skew tolerance to handle time sync issues
            idinfo = id_token.verify_oauth2_token(
                credentials.id_token,
                requests.Request(),
                Config.GOOGLE_CLIENT_ID,
                clock_skew_in_seconds=60
            )
            logger.info("ID token verified successfully")
        except Exception as verify_error:
            logger.error(f"Token verification failed: {str(verify_error)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token verification failed: {str(verify_error)}"
            )
        
        # Check issuer
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        
        google_user_info = {
            "sub": idinfo.get("sub"),
            "email": idinfo.get("email"),
            "name": idinfo.get("name"),
            "picture": idinfo.get("picture")
        }
        
        logger.info(f"Successfully authenticated user: {google_user_info['email']}")
        
        # Get or create user
        users_repo = UsersRepository(db)
        user_service = UserService(users_repo)
        
        user = await user_service.get_or_create_user(google_user_info)
        
        # Generate JWT token
        token_data = {
            "user_id": str(user["_id"]),
            "email": user["email"],
            "name": user["name"],
            "role": user.get("role", "student")
        }
        
        access_token = AuthUtils.create_access_token(token_data)
        
        # Redirect to frontend with token in URL
        frontend_url = Config.FRONTEND_URL
        redirect_url = f"{frontend_url}/auth/callback?token={access_token}&user={user['email']}"
        
        return RedirectResponse(url=redirect_url)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Google callback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: Dict = Depends(get_current_user)):
    """
    Logout endpoint (token is managed on client side)
    """
    logger.info(f"User logged out: {current_user['email']}")
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(
    current_user: Dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Get current authenticated user information
    """
    users_repo = UsersRepository(db)
    user = await users_repo.get_user_by_id(current_user["user_id"])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserInfo(
        id=str(user["_id"]),
        email=user["email"],
        name=user["name"],
        profile_picture=user.get("profile_picture"),
        role=user.get("role", "student"),
        verification_required=user.get("identity_verification", {}).get("required", True),
        verification_status=user.get("identity_verification", {}).get("status", "pending"),
        verified_role=user.get("identity_verification", {}).get("verified_role")
    )


@router.post("/verify-identity", response_model=Dict)
async def verify_identity(
    current_user: Dict = Depends(get_current_user),
    db=Depends(get_db),
    profile_name: str = Form(""),
    allow_name_edit: bool = Form(False),
    expected_role: str = Form(""),
    scan_mode: str = Form("upload"),
    scan_text: str = Form(""),
    id_images: Optional[List[UploadFile]] = File(None),
    front_id: UploadFile = File(None),
    back_id: UploadFile = File(None),
):
    """
    Verify student/faculty identity using AI-assisted extraction.
    Files are processed in-memory and never persisted.
    """
    users_repo = UsersRepository(db)
    user = await users_repo.get_user_by_id(current_user["user_id"])
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    uploads: List[UploadFile] = []
    if id_images:
        uploads.extend([u for u in id_images if u is not None])
    if front_id is not None:
        uploads.append(front_id)
    if back_id is not None:
        uploads.append(back_id)

    # Deduplicate same object references and keep max 2 files.
    deduped = []
    seen_refs = set()
    for u in uploads:
        if id(u) in seen_refs:
            continue
        seen_refs.add(id(u))
        deduped.append(u)

    uploads = deduped[:2]

    if not uploads:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload at least one ID image"
        )

    for uploaded in uploads:
        if not uploaded.filename or not _is_allowed_id_file(uploaded.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported ID file type: {uploaded.filename}"
            )

    # Read files only in memory to satisfy temporary processing requirement.
    read_buffers = []
    image_data_urls: List[str] = []
    for uploaded in uploads:
        file_bytes = await uploaded.read()
        read_buffers.append(file_bytes)

        content_type = (uploaded.content_type or "").lower().strip()
        if not content_type or content_type == "application/octet-stream":
            guessed, _ = mimetypes.guess_type(uploaded.filename or "")
            content_type = (guessed or "").lower()

        if file_bytes and content_type.startswith("image/"):
            encoded = base64.b64encode(file_bytes).decode("ascii")
            image_data_urls.append(f"data:{content_type};base64,{encoded}")

    non_empty_count = sum(1 for b in read_buffers if len(b) > 0)
    has_front = non_empty_count >= 1
    has_back = non_empty_count >= 2

    effective_name = profile_name.strip() if allow_name_edit and profile_name.strip() else user.get("name", "")
    normalized_expected_role = expected_role.strip().lower()

    effective_scan_text = (scan_text or "").strip()
    if not effective_scan_text:
        effective_scan_text = _extract_ocr_text_from_images(read_buffers, uploads)

    extracted = _extract_with_groq(
        scan_text=effective_scan_text,
        google_email=user.get("email", ""),
        claimed_name=effective_name,
        expected_role=normalized_expected_role,
        image_data_urls=image_data_urls,
    )

    # Explicitly discard byte buffers to avoid persistence.
    del read_buffers

    id_name = (extracted.get("id_name") or "").strip()
    id_type = (extracted.get("id_type") or "unknown").strip().lower()
    if id_type not in {"student", "faculty", "unknown"}:
        id_type = "unknown"
    roll_or_emp_id = extracted.get("roll_or_emp_id", "")
    institutional_email = extracted.get("institutional_email", "")

    score, reasons = _score_verification(
        google_email=user.get("email", ""),
        google_name=effective_name,
        id_type=id_type,
        id_name=id_name,
        roll_or_emp_id=roll_or_emp_id,
        institutional_email=institutional_email,
        has_front=has_front,
        has_back=has_back,
    )

    if extracted.get("ai_mode") == "no_ocr":
        reasons.append("Unable to read ID content from uploaded file (no OCR text)")
    elif effective_scan_text:
        reasons.append("OCR text extracted from uploaded ID image")

    is_strong, strict_reasons = _is_strong_identity_proof(
        google_email=user.get("email", ""),
        google_name=effective_name,
        id_type=id_type,
        id_name=id_name,
        roll_or_emp_id=roll_or_emp_id,
        institutional_email=institutional_email,
        has_front=has_front,
    )

    reasons = [*reasons, *strict_reasons]

    has_valid_id_code = bool(re.match(r"^[a-z0-9._\-]{3,}$", (roll_or_emp_id or "").strip().lower()))
    normalized_claimed_name = (effective_name or "").strip().lower()
    normalized_id_name = (id_name or "").strip().lower()
    name_matches_claim = bool(
        normalized_claimed_name and normalized_id_name and
        (normalized_claimed_name in normalized_id_name or normalized_id_name in normalized_claimed_name)
    )
    role_matches_claim = bool(
        normalized_expected_role in {"student", "faculty"} and
        id_type in {"student", "faculty"} and
        normalized_expected_role == id_type
    )

    # Allow strong proofs with slightly lower score when ID code + role + name are clear.
    should_auto_approve = is_strong and (
        score >= 70
        or (score >= 60 and has_valid_id_code and id_type in {"student", "faculty"} and bool(id_name))
        or (score >= 55 and has_valid_id_code and id_type in {"student", "faculty"} and bool(id_name) and has_back)
    )

    if should_auto_approve:
        resolved_role = id_type if id_type in {"student", "faculty"} else normalized_expected_role
        if resolved_role not in {"student", "faculty"}:
            resolved_role = "student"

        decision = "auto_approve"
        verification_status = "verified"

        await users_repo.set_role_and_verification(
            user_id=str(user["_id"]),
            role=resolved_role,
            name_override=effective_name if allow_name_edit and effective_name else None,
            verification_update={
                "required": True,
                "status": verification_status,
                "verified_role": resolved_role,
                "verified_at": datetime.utcnow(),
                "provider": "groq" if GROQ_ENABLED else "heuristic",
                "confidence": "high" if score >= 85 else "medium",
                "decision": decision,
                "reasons": reasons,
            },
        )
    else:
        resolved_role = user.get("role", "student")
        decision = "manual_review"
        verification_status = "pending"
        failure_feedback: List[str] = []

        # Add explicit, user-facing guidance about what is missing.
        reasons.append(
            f"Verification pending: trust score {score} did not meet auto-approval rules"
        )
        failure_feedback = _generate_failure_feedback(
            claimed_name=effective_name,
            expected_role=normalized_expected_role,
            extracted=extracted,
            trust_score=score,
            has_back=has_back,
            has_valid_id_code=has_valid_id_code,
            name_matches_claim=name_matches_claim,
            role_matches_claim=role_matches_claim,
            internal_reasons=reasons,
        )

        await users_repo.update_identity_verification(
            user_id=str(user["_id"]),
            verification_update={
                "required": True,
                "status": verification_status,
                "verified_role": None,
                "verified_at": None,
                "provider": "groq" if GROQ_ENABLED else "heuristic",
                "confidence": "low" if score < 70 else "medium",
                "decision": decision,
                "reasons": reasons,
            },
        )

    response_payload = {
        "verified": verification_status == "verified",
        "decision": decision,
        "verification_status": verification_status,
        "assigned_role": resolved_role if verification_status == "verified" else None,
        "trust_score": score,
        "reasons": reasons,
        "scan_mode": "upload",
        "uploaded_images": non_empty_count,
        "scan_extracted": extracted,
        "temporary_storage": "Files processed in-memory and discarded after verification",
    }

    if verification_status != "verified":
        response_payload["failure_feedback"] = failure_feedback

    return response_payload
