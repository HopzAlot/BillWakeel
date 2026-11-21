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

## 2026-11-21: Recalculation engine takes the slab method as an argument; provisional Rs. 1 tolerance (SCRUM-29)
backend/services/tariff_engine.py recalculates a bill from a TariffSchedule in plain Python:
energy through the slabs, then the fixed charge, then per-unit FCA/FPA/QTA, then taxes. The
SCRUM-28 schema does not say whether slabs are telescopic (protected consumers, each slab bills
its own units) or landing (unprotected consumers, all units at the rate of the slab the total
lands in), so the engine takes slab_method as a parameter, defaulting to telescopic, instead of
changing the shared schema this sprint. Percentage taxes must name one of three bases
(energy_charge, fixed_charge, subtotal); any other basis raises an error instead of being
guessed. A recalculated total within Rs. 1 of the billed total counts as a match; this is
provisional until real tariff JSON replaces the K-Electric placeholder. Rejected: adding a
slab_method field to TariffSchedule now (needs whole-team agreement), and Decimal arithmetic
(rounding every line to paisa is enough at bill scale).
                                                  
