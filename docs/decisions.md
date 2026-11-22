# Engineering decisions

One entry per decision: date, decision, rationale.

## 2026-10-13: Arithmetic lives in code, not the LLM
A deterministic Python engine recalculates bills from structured tariff data. The LLM extracts, explains and writes, never computes. This is the main hallucination defence.

## 2026-10-13: Stack is FastAPI + React (Vite)
FastAPI fits the Python AI ecosystem (LangChain, Pydantic). React gives a flexible UI.

## 2026-10-13: Letters are never auto-submitted
No public submission API exists, and a human should own a dispute. The user reviews and sends.

## 2026-10-24: Pin Gemini model to gemini-3.5-flash-lite, not gemini-3.8-flash
Free tier for gemini-3.8-flash is 5 RPM / 20 RPD (confirmed via AI Studio's rate-limit dashboard) — nearly unusable for eval runs across 10 sample bills plus team testing. gemini-3.5-flash-lite has 15 RPM / 500 RPD. Switched locally via .env; backend/config.py's hardcoded default and .env.example still need updating to make this the team-wide default.

## 2026-11-16: "Second bill layout" means SNGPL gas bills; extraction stays on prompt v1 (SCRUM-32)
SCRUM-32 extends extraction to the SNGPL gas layout, using the 4 anonymised sngpl_* samples
already in data/samples/. The eval gained a --utility option and a gas-only units tolerance of
0.001 HM3, because the electricity tolerance of 1 unit would accept almost any gas value.
Prompt v1 already reads every gas-specific field correctly (4/4 schema-valid, see
docs/eval/2026-11-16-extraction-gas.md), so no v2 was written. Rejected: adding a new
electricity DISCO layout (no samples yet), and a v2 prompt only to fix provider names
(not a gas-layout problem and it would also change electricity results).

## 2026-11-22: Recalculation engine follows the extended tariff schema; provisional Rs. 1 tolerance (SCRUM-29)
backend/services/tariff_engine.py recalculates a bill from a TariffSchedule and a
TariffCalculationInput (SCRUM-28) in plain Python: energy through the slabs using the
schedule's billing_method (TOU tariffs price peak and off-peak units separately), then the fixed
charge (a slab's own fixed charge overrides the schedule's), a minimum-charge top-up only when no
fixed charge applies, per-unit adjustments, then taxes. Tax bases are looked up in a fixed table
that includes the exact wording used in the tariff files; any other basis raises an error instead
of being guessed. Tariffs that only publish a rate range, or are derived from another tariff
(rate_multiplier, derived_from_base_tariff), also raise an error rather than giving an
approximate total. A sanctioned load outside the tariff's range is returned as a warning, not an
error, because some load limits in the data still need checking. A recalculated total within
Rs. 1 of the billed total counts as a match; provisional until real bills are checked. Rejected:
Decimal arithmetic (rounding every line to paisa is enough at bill scale).
