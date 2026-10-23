# Extraction eval — 2026-10-23

Prompt version: v1
Model: gemini-3.5-flash-lite
Scope: electricity samples only (6 bills)

## Result

6/6 schema-valid

## Per-sample

- hazeco_001: schema-valid, 2 field(s) off: provider (got 'HAZARA ELECTRIC SUPPLY COMPANY', expected 'HAZECO'); total_payable_after_due_date (got 2686.0, expected 2586.0)
- hazeco_002: schema-valid, 2 field(s) off: provider (got 'HAZARA ELECTRIC SUPPLY COMPANY', expected 'HAZECO'); total_payable_after_due_date (got 1749.0, expected 1685.0)
- hazeco_003: schema-valid, 3 field(s) off: provider (got 'HAZACO (Hazara Electric Supply Company)', expected 'HAZECO'); total_payable_by_due_date (got 1627.0, expected 1562.0); total_payable_after_due_date (got 1692.0, expected 1627.0)
- hazeco_004: schema-valid, 2 field(s) off: provider (got 'HAZARA ELECTRIC SUPPLY COMPANY', expected 'HAZECO'); sanctioned_load_kw (got None, expected 1.0)
- iesco_001: schema-valid, 2 field(s) off: provider (got 'ISLAMABAD ELECTRIC SUPPLY COMPANY (LTD).', expected 'IESCO'); tariff_category (got 'A1a(01)', expected 'A-1a(01)')
- iesco_002: schema-valid, all fields matched

## Per-field accuracy

- provider: 1/6
- utility: 6/6
- billing_month: 6/6
- issue_date: 6/6
- due_date: 6/6
- tariff_category: 5/6
- sanctioned_load_kw: 5/6
- meter_reading_previous: 6/6
- meter_reading_current: 6/6
- units_consumed: 6/6
- total_payable_by_due_date: 5/6
- total_payable_after_due_date: 3/6
