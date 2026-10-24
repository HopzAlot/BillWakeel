"""Smoke test for the Gemini connection. Run from the repo root:
    python check_connection.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from dotenv import load_dotenv

from services.gemini import GeminiError, extract_text, get_llm, invoke_with_retry


def main():
    env_found = load_dotenv()
    print(f"[setup] .env loaded: {env_found}")

    try:
        llm = get_llm(temperature=0.2)
    except GeminiError as e:
        print(f"[error] {e}")
        sys.exit(1)

    print("[setup] API key found, initializing model...")

    prompt = "In one sentence, explain what a 'slab' means in a Pakistani electricity bill."
    print(f"[test] Sending prompt: {prompt}")

    try:
        response = invoke_with_retry(llm, prompt)
    except GeminiError as e:
        print(f"[error] {e}")
        sys.exit(1)

    print("\n[success] Response from Gemini:")
    print(extract_text(response))


if __name__ == "__main__":
    main()
