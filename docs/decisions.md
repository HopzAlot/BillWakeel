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

## 2026-11-25: Grounding Agent matches at the charge-line level; Finding gets an `explanation` field (SCRUM-31)
`ground_bill()` matches each printed charge line to the one engine-computed component it's about
(energy, fixed charge, or a named tax/adjustment), by exact alias after normalizing punctuation —
not fuzzy/substring matching, because "GST" and "GST on FPA" must never match the same component.
A charge the engine doesn't model yet (FCA/FPA, FC/NJ surcharges — SCRUM-28's `adjustments` arrays
had no entries at all as of 2026-11-25, see the next entry) is left unmatched and produces no
finding, rather than guessing. The citation gate (drop a finding if the best retrieved chunk
scores below 0.3 cosine similarity) runs before any Gemini call, in code, not as a prompt
instruction.

Deviation from the proposed Brief §8.4 `Finding` schema: added `explanation: str` (Gemini's
non-accusatory phrasing) as its own field, separate from `clause_text` (the retrieved clause,
verbatim, never edited by the LLM). The brief's step 2 requires Gemini to phrase each finding in
non-accusatory wording, but the proposed schema had nowhere to put that sentence without
overwriting the exact quoted source text SCRUM-33/34 need to display as the citation.

Also: `BillExtraction` has no `consumer_status` field (lifeline/protected/unprotected), so
`services/bill_to_tariff.py` defaults it to `"protected"` for A-1(a) bills only (the one tariff
code the structured JSON splits by status) and surfaces the assumption as a warning. Flagged for a
future extraction-prompt version, same as the known total_payable_after_due_date tier bug — not
fixed here.

## 2026-11-25: Add K-Electric's Quarterly Tariff Adjustment to the tariff JSON; FCA/FC/NJ still not modeled (SCRUM-31)
Flagged during SCRUM-31 review: SCRUM-27/28's sources table said S02, S04, S05 and S07 were still
"TO DOWNLOAD", but S02 and S03 had actually been downloaded during SCRUM-28 and never logged.
Fixed by downloading the genuinely-missing ones (S04 IESCO rebasing, S05 LESCO rebasing, S07 the
K-Electric/XWDISCO Q1 CY2026 quarterly adjustment SRO) and correcting `sources.md`/`sources.csv`.

Of those, only S07 was usable as-is: it gives one clean, single number (Rs. -1.9857/kWh, valid
June-August 2026 only, confirmed against the primary Gazette notification) that fits
`TariffAdjustment`'s schema (a flat `rate_pkr_per_unit`). Added to every K-Electric tariff file
except lifeline and prepaid ones (both explicitly excluded by the SRO's own text).

Follow-up the same day: a flat rate with no effective window is actively dangerous once a
schedule outlives one quarter — it would silently misapply June-August's QTA to a December bill.
Rather than bury that caveat in the adjustment's name string, extended the schema properly:
`TariffAdjustment` gained `effective_from_month`/`effective_to_month` ("YYYY-MM", inclusive,
either end optional), and `TariffCalculationInput` gained `billing_month` (same format as
`BillExtraction.billing_month`, threaded through by `services/bill_to_tariff.py`). `calculate_bill`
now skips a time-bounded adjustment outside its window — or when `billing_month` isn't known at
all — and records why in `BillCalculation.warnings`, rather than guessing. `grounding.py`'s
component-matching resolves a tax/adjustment's own canonical key by keyword (e.g. anything
containing "qta") rather than exact slug, so the match stays stable if the JSON's wording changes.

Deliberately NOT added: FCA/FPA (the guide itself calls it "variable monthly," with no single
rate — S02's 51-page decision has the formula, not a number for any specific month, and
inventing one would break the "never invent a tariff rate" rule) and the FC/NJ surcharges
(published as ranges, and FC is slab-dependent — `TariffAdjustment` only supports one flat rate).
S04/S05 (IESCO/LESCO rebasing determinations) are about base tariff rates, not adjustments, and
can't be used until IESCO/LESCO get base structured tariff files at all (still just `.gitkeep`) —
a SCRUM-28 scope gap, not something fixed here.

Because this changes GST's basis (GST is 18% of energy + fixed + adjustments) for every
non-lifeline, non-prepaid K-Electric category, `tests/unit/test_tariff_engine.py`'s two domestic
bill tests (SCRUM-29, Swati's) needed their expected totals corrected too — the engine logic
itself didn't change, only the data it now has to work with.
