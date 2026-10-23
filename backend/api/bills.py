"""Bill endpoints — upload, extract, and save corrected extraction.

Implements the Sprint 1 API contract (Brief §8.2):
    POST   /bills                    – upload a bill
    POST   /bills/{bill_id}/extract  – run the Extraction Agent
    PUT    /bills/{bill_id}/extraction – save user-corrected values
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, status

from config import settings
from agents.extraction import extract_bill, ExtractionError, ExtractionResult
from models.bill import BillExtraction, BillUploadResponse, ExtractionResponse
from services.gemini import GeminiError

router = APIRouter(prefix="/bills", tags=["bills"])

# ---------------------------------------------------------------------------
# In-memory stores (replaced by a database in Sprint 2)
# ---------------------------------------------------------------------------
# bill_id -> metadata dict
_bill_store: dict[str, dict] = {}
# bill_id -> BillExtraction
_extraction_store: dict[str, BillExtraction] = {}

# Allowed MIME types for uploads
_ALLOWED_CONTENT_TYPES: set[str] = {
    "image/jpeg",
    "image/png",
    "application/pdf",
}

# Map MIME type to file extension
_EXTENSION_MAP: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "application/pdf": ".pdf",
}


def _max_upload_bytes() -> int:
    return settings.max_upload_mb * 1024 * 1024


def _upload_dir() -> Path:
    """Resolve the upload directory relative to the repo root."""
    repo_root = Path(__file__).resolve().parent.parent
    upload_path = repo_root / settings.upload_dir
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path


# ── POST /bills ──────────────────────────────────────────────────────────
@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=BillUploadResponse,
    summary="Upload a bill image or PDF",
)
async def upload_bill(file: UploadFile = File(...)):
    """Accept a multipart ``file`` upload.

    Validates:
    - content type is jpeg, png, or pdf  (415 if not)
    - file is not empty                  (400 if empty)
    - file size ≤ MAX_UPLOAD_MB          (413 if too large)

    The file is saved as ``data/uploads/<bill_id>.<ext>`` using a
    generated UUID — the original filename is *never* used as a
    filesystem path (security: path-traversal prevention).
    """
    # ── Content-type validation ──────────────────────────────────────
    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported file type '{file.content_type}'. "
                f"Accepted types: {', '.join(sorted(_ALLOWED_CONTENT_TYPES))}."
            ),
        )

    # ── Read the file (don't trust Content-Length header) ────────────
    contents = await file.read()

    # ── Empty-file check ─────────────────────────────────────────────
    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    # ── Size check ───────────────────────────────────────────────────
    max_bytes = _max_upload_bytes()
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=(
                f"File size ({len(contents)} bytes) exceeds the "
                f"{settings.max_upload_mb} MB limit."
            ),
        )

    # ── Persist to disk ──────────────────────────────────────────────
    bill_id = str(uuid.uuid4())
    ext = _EXTENSION_MAP[file.content_type]
    save_path = _upload_dir() / f"{bill_id}{ext}"
    save_path.write_bytes(contents)

    # ── Store metadata in memory ─────────────────────────────────────
    _bill_store[bill_id] = {
        "bill_id": bill_id,
        "filename": file.filename or "unknown",
        "content_type": file.content_type,
        "size_bytes": len(contents),
        "file_path": str(save_path),
    }

    return BillUploadResponse(
        bill_id=bill_id,
        filename=file.filename or "unknown",
        content_type=file.content_type,
        size_bytes=len(contents),
    )


# ── POST /bills/{bill_id}/extract ────────────────────────────────────────
@router.post(
    "/{bill_id}/extract",
    response_model=ExtractionResponse,
    summary="Run the Extraction Agent on an uploaded bill",
)
async def extract(bill_id: str):
    """Look up the bill, call ``extract_bill``, and store the result.

    Error mapping:
    - Unknown bill_id → 404
    - GeminiError     → 502 (model call failed)
    - ExtractionError → 422 (model output unreadable)
    """
    if bill_id not in _bill_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bill '{bill_id}' not found.",
        )

    meta = _bill_store[bill_id]

    try:
        result: ExtractionResult = extract_bill(
            file_path=meta["file_path"],
            content_type=meta["content_type"],
        )
    except GeminiError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Model call failed: {exc}",
        )
    except ExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not parse model output: {exc}",
        )

    # Store the extraction so it can be retrieved / edited later
    _extraction_store[bill_id] = result.extraction

    return ExtractionResponse(
        bill_id=bill_id,
        extraction=result.extraction,
        prompt_version=result.prompt_version,
        model=result.model,
    )


# ── PUT /bills/{bill_id}/extraction ──────────────────────────────────────
@router.put(
    "/{bill_id}/extraction",
    response_model=BillExtraction,
    summary="Save user-corrected extraction values",
)
async def update_extraction(bill_id: str, body: BillExtraction):
    """Validate the body against ``BillExtraction`` and store it.

    Returns the stored extraction.  Pydantic handles 422 automatically
    if the body doesn't match the schema.
    """
    if bill_id not in _bill_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bill '{bill_id}' not found.",
        )

    _extraction_store[bill_id] = body
    return body
