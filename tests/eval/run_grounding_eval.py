"""Evaluation harness for the Tariff-Grounding Agent (SCRUM-31).

Run from the repo root:
    python tests/eval/run_grounding_eval.py

Unlike tests/unit/test_grounding.py (which mocks the Gemini call so the
test suite runs offline), this calls the real model, the same way
tests/eval/run_extraction_eval.py does for the Extraction Agent, per
CONTRIBUTING.md section 6. It runs the one required seeded-error sample —
a real K-Electric A-1(a) bill with its GST line deliberately inflated —
through the real pipeline (engine -> retrieval -> Gemini phrasing) and
checks that the one seeded discrepancy is caught, cited, and that nothing
else is flagged.

Saves a dated results file to docs/eval/.
"""

import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from dotenv import load_dotenv

load_dotenv(REPO_ROOT / ".env")

from agents.grounding import ground_bill  # noqa: E402
from config import settings  # noqa: E402
from models.bill import BillExtraction, ChargeLine  # noqa: E402
from models.tariff import TariffCalculationInput  # noqa: E402
from services.tariff_engine import (  # noqa: E402
    calculate_bill,
    load_tariff_schedules,
    select_tariff,
)

RESULTS_DIR = REPO_ROOT / "docs" / "eval"

# Real K-Electric A-1(a) protected tariff, 145 units, 2 kW sanctioned load.
# Energy (1639.45), fixed (600.0), Electricity Duty (24.59) and the
# Quarterly Tariff Adjustment (-287.93, sourced from the official Gazette
# SRO — SCRUM-31, 2026-11-25, see data/tariffs/raw/sources.md S07) are the
# exact engine-computed values — any finding on those would be a bug.
# GST's exact value is 351.27; billed here as 851.27, a seeded Rs. 500 error.
SEEDED_EXTRACTION = BillExtraction(
    utility="electricity",
    provider="K-Electric",
    billing_month="2026-07",  # inside the QTA's Jun-Aug 2026 window
    tariff_category="A-1a(01)",
    sanctioned_load_kw=2.0,
    units_consumed=145,
    charges=[
        ChargeLine(name="Cost of electricity", amount_pkr=1639.45),
        ChargeLine(name="Fixed charges", amount_pkr=600.0),
        ChargeLine(name="Electricity duty", amount_pkr=24.59),
        ChargeLine(name="GST", amount_pkr=851.27),  # seeded: real value is 351.27
        ChargeLine(name="Qtr tariff adjustment", amount_pkr=-287.93),  # exact engine value
        ChargeLine(name="Fuel price adjustment", amount_pkr=71.0),  # still no engine counterpart
    ],
)


def main():
    schedules = load_tariff_schedules(REPO_ROOT / "data" / "tariffs" / "structured" / "k-electric")
    calc_input = TariffCalculationInput(
        disco="K-Electric",
        tariff_code="A-1(a)",
        monthly_units=145,
        sanctioned_load_kw=2.0,
        consumer_status="protected",
        billing_month="2026-07",
    )
    tariff = select_tariff(schedules, calc_input)
    calculation = calculate_bill(tariff, calc_input)

    response = ground_bill("eval-seeded-ke-a1a", SEEDED_EXTRACTION, calculation)

    print(f"Model: {settings.gemini_model}")
    print(f"Findings: {len(response.findings)}")
    lines = []
    for finding in response.findings:
        line = (
            f"- {finding.charge_name}: billed Rs. {finding.billed_amount_pkr}, "
            f"expected Rs. {finding.expected_amount_pkr}, "
            f"diff Rs. {finding.difference_pkr}, clause {finding.clause_id} "
            f"({finding.confidence} confidence)\n"
            f"  Explanation: {finding.explanation}"
        )
        print(line)
        lines.append(line)

    expected_ok = (
        len(response.findings) == 1
        and response.findings[0].charge_name == "GST"
        and response.findings[0].clause_text
    )
    print("\nPASS" if expected_ok else "\nFAIL: expected exactly one cited GST finding")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results_path = RESULTS_DIR / f"{date.today().isoformat()}-grounding-seeded-error.md"
    results_path.write_text(
        f"# Grounding eval — {date.today().isoformat()}\n\n"
        f"Prompt version: {calculation.tariff_code} / grounding v1\n"
        f"Model: {settings.gemini_model}\n"
        f"Scope: 1 seeded-error K-Electric A-1(a) bill (GST inflated by Rs. 500)\n\n"
        f"## Result\n\n{'PASS' if expected_ok else 'FAIL'}: "
        f"{len(response.findings)} finding(s), expected exactly 1 (GST)\n\n"
        f"## Findings\n\n" + ("\n".join(lines) if lines else "(none)") + "\n"
    )
    print(f"\nSaved results to {results_path.relative_to(REPO_ROOT)}")
    return 0 if expected_ok else 1


if __name__ == "__main__":
    sys.exit(main())
