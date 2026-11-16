# Extraction eval — 2026-11-16

Prompt version: v1
Model: gemini-3.5-flash-lite
Scope: gas samples (4 bills)

## Result

4/4 schema-valid

## Per-sample

- sngpl_001: schema-valid, 2 field(s) off: provider (got 'Sui Northern Gas Pipelines Limited', expected 'SNGPL'); tariff_category (got 'DOMU- B', expected 'DOMU-B')
- sngpl_002: schema-valid, 1 field(s) off: provider (got 'Sui Northern Gas Pipelines Limited', expected 'SNGPL')
- sngpl_003: schema-valid, 1 field(s) off: provider (got 'Sui Northern Gas', expected 'SNGPL')
- sngpl_004: schema-valid, 1 field(s) off: provider (got 'Sui Northern Gas', expected 'SNGPL')

## Per-field accuracy

- provider: 0/4
- utility: 4/4
- billing_month: 4/4
- issue_date: 4/4
- due_date: 4/4
- tariff_category: 3/4
- sanctioned_load_kw: 4/4
- meter_reading_previous: 4/4
- meter_reading_current: 4/4
- units_consumed: 4/4
- total_payable_by_due_date: 4/4
- total_payable_after_due_date: 4/4


## Findings (SCRUM-32)

- Model: gemini-3.5-flash-lite (same as the Sprint 1 electricity eval). gemini-3.8-flash
  returned 503 "high demand" on 2026-11-16, so it could not be used for this run.
- Result: 4/4 gas bills schema-valid on prompt v1. Overall (--utility all): 10/10 schema-valid,
  see 2026-11-16-extraction-all.md. Acceptance criterion (at least 5 samples) met.
- Gas-specific fields are all correct: units_consumed 4/4 (HM3, not MMBTU),
  meter readings 4/4, sanctioned_load_kw 4/4 (null on gas), both payable totals 4/4.
- Decision: no prompt v2. The misses below are not gas-layout problems.
- provider 0/4: model writes the full name ("Sui Northern Gas Pipelines Limited")
  instead of "SNGPL". Same naming mismatch as electricity (0/6 today, 1/6 in Sprint 1).
- tariff_category 3/4: sngpl_001 read as "DOMU- B" (stray space) instead of "DOMU-B".
- Known v1 second-payment-tier issue: not seen on any gas sample. Still seen on electricity
  (total_payable_after_due_date 2/6 vs 3/6 in Sprint 1, same prompt; deferred, not fixed here).
