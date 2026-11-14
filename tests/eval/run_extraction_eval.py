"""Evaluation harness for the Extraction Agent (SCRUM-10).

Run from the repo root:
    python tests/eval/run_extraction_eval.py

Calls extract_bill() on every electricity sample in data/samples/ and
compares the result against its ground-truth JSON. Gas bills are out of
scope for this pass (fractional HM3 units need separate handling).

Saves a dated results file to docs/eval/ with the prompt version and
model used, per CONTRIBUTING.md section 6.
"""

import json
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from dotenv import load_dotenv

load_dotenv(REPO_ROOT / ".env")

from agents.extraction import ExtractionError, extract_bill  # noqa: E402
from services.gemini import GeminiError  # noqa: E402

SAMPLES_DIR = REPO_ROOT / "data" / "samples"
RESULTS_DIR = REPO_ROOT / "docs" / "eval"

AMOUNT_TOLERANCE_PKR = 2
UNITS_TOLERANCE = 1
LOAD_TOLERANCE_KW = 0.1

_EXT_TO_CONTENT_TYPE = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".pdf": "application/pdf",
}

# Exact match except where noted; these use a tolerance or fuzzy check instead.
FIELDS_CHECKED = [
    "provider",  # fuzzy: substring either direction, case-insensitive
    "utility",
    "billing_month",
    "issue_date",
    "due_date",
    "tariff_category",
    "sanctioned_load_kw",  # tolerance
    "meter_reading_previous",  # tolerance
    "meter_reading_current",  # tolerance
    "units_consumed",  # tolerance
    "total_payable_by_due_date",  # tolerance
    "total_payable_after_due_date",  # tolerance
]


def _numbers_close(actual, expected, tolerance):
    if actual is None or expected is None:
        return actual == expected
    return abs(actual - expected) <= tolerance


def _provider_matches(actual, expected):
    if actual is None or expected is None:
        return actual == expected
    a, e = actual.strip().lower(), expected.strip().lower()
    return a in e or e in a


def _field_matches(field, actual, expected):
    if field == "provider":
        return _provider_matches(actual, expected)
    if field == "sanctioned_load_kw":
        return _numbers_close(actual, expected, LOAD_TOLERANCE_KW)
    if field in ("meter_reading_previous", "meter_reading_current", "units_consumed"):
        return _numbers_close(actual, expected, UNITS_TOLERANCE)
    if field in ("total_payable_by_due_date", "total_payable_after_due_date"):
        return _numbers_close(actual, expected, AMOUNT_TOLERANCE_PKR)
    return actual == expected


def _load_electricity_samples():
    samples = []
    for json_path in sorted(SAMPLES_DIR.glob("*.json")):
        ground_truth = json.loads(json_path.read_text())
        if ground_truth.get("utility") != "electricity":
            continue
        image_path = next(
            (
                json_path.with_suffix(ext)
                for ext in _EXT_TO_CONTENT_TYPE
                if json_path.with_suffix(ext).exists()
            ),
            None,
        )
        if image_path is None:
            raise FileNotFoundError(f"No bill image found for {json_path.name}")
        samples.append((json_path.stem, image_path, ground_truth))
    return samples


def main():
    samples = _load_electricity_samples()
    if not samples:
        print("No electricity samples found in data/samples/.")
        return

    field_hits = {f: 0 for f in FIELDS_CHECKED}
    field_total = {f: 0 for f in FIELDS_CHECKED}
    schema_valid = 0
    prompt_version = model_name = None
    per_sample_lines = []

    for name, image_path, ground_truth in samples:
        content_type = _EXT_TO_CONTENT_TYPE[image_path.suffix.lower()]
        print(f"[{name}] extracting...")

        try:
            result = extract_bill(str(image_path), content_type)
        except (ExtractionError, GeminiError) as e:
            print(f"[{name}] FAILED: {e}")
            per_sample_lines.append(f"- {name}: FAILED ({e})")
            continue

        prompt_version = result.prompt_version
        model_name = result.model
        schema_valid += 1
        extraction = result.extraction.model_dump(mode="json")

        misses = []
        for field in FIELDS_CHECKED:
            field_total[field] += 1
            if _field_matches(field, extraction.get(field), ground_truth.get(field)):
                field_hits[field] += 1
            else:
                misses.append(
                    f"{field} (got {extraction.get(field)!r}, expected {ground_truth.get(field)!r})"
                )

        status = "all fields matched" if not misses else f"{len(misses)} field(s) off: " + "; ".join(misses)
        print(f"[{name}] schema-valid, {status}")
        per_sample_lines.append(f"- {name}: schema-valid, {status}")

    total = len(samples)
    print(f"\n{schema_valid}/{total} schema-valid")
    print("\nPer-field accuracy (of schema-valid extractions):")
    field_lines = []
    for field in FIELDS_CHECKED:
        hits, attempted = field_hits[field], field_total[field]
        pct = f"{hits}/{attempted}" if attempted else "n/a"
        print(f"  {field}: {pct}")
        field_lines.append(f"- {field}: {pct}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results_path = RESULTS_DIR / f"{date.today().isoformat()}-extraction-electricity.md"
    results_path.write_text(
        f"# Extraction eval — {date.today().isoformat()}\n\n"
        f"Prompt version: {prompt_version}\n"
        f"Model: {model_name}\n"
        f"Scope: electricity samples only ({total} bills)\n\n"
        f"## Result\n\n{schema_valid}/{total} schema-valid\n\n"
        f"## Per-sample\n\n" + "\n".join(per_sample_lines) + "\n\n"
        f"## Per-field accuracy\n\n" + "\n".join(field_lines) + "\n"
    )
    print(f"\nSaved results to {results_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
