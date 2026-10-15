"""Single place that builds the Gemini client, knows the model name, and
turns SDK errors into GeminiError. Agents call get_llm() - don't import
langchain_google_genai or read env vars directly.
"""

import os
import time

from google.genai.errors import ServerError
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError
from pydantic import ValidationError

DEFAULT_MODEL = "gemini-3.8-flash"
RETRY_ATTEMPTS = 1
RETRY_WAIT_SECONDS = 2


class GeminiError(Exception):
    """Client setup or call failure. Callers map this to an HTTP 502."""


def _model_name() -> str:
    # TODO(SCRUM-6): switch to config.py once it merges to dev.
    return os.getenv("GEMINI_MODEL", DEFAULT_MODEL)


def get_llm(temperature: float = 0.0) -> ChatGoogleGenerativeAI:
    """Build a Gemini client. Use temperature 0 for extraction (repeatable reads)."""
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise GeminiError(
            "No Gemini API key found. Set GOOGLE_API_KEY in your .env file."
        )

    try:
        return ChatGoogleGenerativeAI(
            model=_model_name(),
            google_api_key=api_key,
            temperature=temperature,
        )
    except ValidationError as e:
        raise GeminiError(f"Could not configure the Gemini client: {e}") from e


def extract_text(message) -> str:
    """Normalize response.content to plain text - Gemini 3 returns a list of
    parts (text + a thought-signature blob) instead of a str."""
    content = message.content
    if isinstance(content, str):
        return content
    return "".join(
        part.get("text", "")
        for part in content
        if isinstance(part, dict) and part.get("type") == "text"
    )


def invoke_with_retry(llm: ChatGoogleGenerativeAI, prompt):
    """Retry once on a 5xx. 4xx failures (bad key, quota, model not found)
    aren't retried - a second attempt won't fix those."""
    for attempt in range(RETRY_ATTEMPTS + 1):
        try:
            return llm.invoke(prompt)
        except ServerError as e:
            if attempt < RETRY_ATTEMPTS:
                time.sleep(RETRY_WAIT_SECONDS)
                continue
            raise GeminiError(f"Gemini server error after retry: {e}") from e
        except ChatGoogleGenerativeAIError as e:
            raise GeminiError(f"Gemini call failed: {e}") from e
