"""Extraction Agent — reads a bill image/PDF and returns structured data
via Gemini, grounded by the prompt in prompts/extraction/v1.md.
"""

from __future__ import annotations

import base64
from pathlib import Path

from langchain_core.exceptions import OutputParserException
from pydantic import ValidationError

from config import settings
from models.bill import BillExtraction, ExtractionResult
from services.gemini import get_llm, invoke_with_retry

PROMPT_VERSION = "v1"
RETRY_ATTEMPTS = 1

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_PROMPT_PATH = _REPO_ROOT / "prompts" / "extraction" / f"{PROMPT_VERSION}.md"


class ExtractionError(Exception):
    """The model returned output that could not be parsed into
    a valid ``BillExtraction``. Callers map this to HTTP 422."""


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text()


def extract_bill(file_path: str, content_type: str) -> ExtractionResult:
    """Extract structured bill data from an uploaded file.

    Parameters
    ----------
    file_path:
        Absolute path to the saved upload (jpg, png, or pdf).
    content_type:
        MIME type of the uploaded file.

    Returns
    -------
    ExtractionResult
        Contains the ``BillExtraction``, the prompt version used, and the
        model name.

    Raises
    ------
    ExtractionError
        If the model output cannot be parsed into a valid ``BillExtraction``,
        even after one retry.
    services.gemini.GeminiError
        If the model call itself fails (bad key, quota, 5xx after retry).
    """
    encoded = base64.b64encode(Path(file_path).read_bytes()).decode("ascii")
    message = {
        "role": "user",
        "content": [
            {"type": "text", "text": _load_prompt()},
            {"type": "media", "data": encoded, "mime_type": content_type},
        ],
    }

    llm = get_llm(temperature=0.0)
    structured_llm = llm.with_structured_output(BillExtraction)

    last_error: Exception | None = None
    for attempt in range(RETRY_ATTEMPTS + 1):
        try:
            extraction = invoke_with_retry(structured_llm, [message])
        except (OutputParserException, ValidationError) as e:
            last_error = e
            continue

        if not isinstance(extraction, BillExtraction):
            last_error = ExtractionError(f"Model returned unexpected output: {extraction!r}")
            continue

        return ExtractionResult(
            extraction=extraction,
            prompt_version=PROMPT_VERSION,
            model=settings.gemini_model,
        )

    raise ExtractionError(
        f"Could not parse model output into BillExtraction after "
        f"{RETRY_ATTEMPTS + 1} attempt(s): {last_error}"
    )
