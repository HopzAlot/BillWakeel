# Extraction eval — 2026-11-25

Prompt version: v2
Model: gemini-3.5-flash-lite
Scope: electricity samples (6 bills)

## Result

6/6 schema-valid

## Per-sample

- hazeco_001: schema-valid, 2 field(s) off: provider (got 'HAZARA ELECTRIC SUPPLY COMPANY', expected 'HAZECO'); tariff_category (got None, expected 'A-1a(01)')
- hazeco_002: schema-valid, all fields matched
- hazeco_003: schema-valid, all fields matched
- hazeco_004: schema-valid, 1 field(s) off: sanctioned_load_kw (got None, expected 1.0)
- iesco_001: schema-valid, 1 field(s) off: tariff_category (got 'A1a(01)', expected 'A-1a(01)')
- iesco_002: schema-valid, 1 field(s) off: provider (got 'ISLAMABAD ELECTRIC SUPPLY COMPANY (LTD).', expected 'IESCO')

## Per-field accuracy

- provider: 4/6
- utility: 6/6
- billing_month: 6/6
- issue_date: 6/6
- due_date: 6/6
- tariff_category: 4/6
- sanctioned_load_kw: 5/6
- meter_reading_previous: 6/6
- meter_reading_current: 6/6
- units_consumed: 6/6
- total_payable_by_due_date: 6/6
- total_payable_after_due_date: 6/6
