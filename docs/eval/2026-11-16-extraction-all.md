# Extraction eval — 2026-11-16

Prompt version: v1
Model: gemini-3.5-flash-lite
Scope: all samples (10 bills)

## Result

10/10 schema-valid

## Per-sample

- hazeco_001: schema-valid, 2 field(s) off: provider (got 'HAZARA ELECTRIC SUPPLY COMPANY', expected 'HAZECO'); total_payable_after_due_date (got 2686.0, expected 2586.0)
- hazeco_002: schema-valid, 2 field(s) off: provider (got 'HAZARA ELECTRIC SUPPLY COMPANY', expected 'HAZECO'); total_payable_after_due_date (got 1749.0, expected 1685.0)
- hazeco_003: schema-valid, 3 field(s) off: provider (got 'HAZARA ELECTRIC SUPPLY COMPANY', expected 'HAZECO'); total_payable_by_due_date (got 1627.0, expected 1562.0); total_payable_after_due_date (got 1692.0, expected 1627.0)
- hazeco_004: schema-valid, 2 field(s) off: provider (got 'HAZARA ELECTRIC SUPPLY COMPANY', expected 'HAZECO'); sanctioned_load_kw (got None, expected 1.0)
- iesco_001: schema-valid, 4 field(s) off: provider (got 'ISLAMABAD ELECTRIC SUPPLY COMPANY (LTD).', expected 'IESCO'); tariff_category (got 'A1a(01)', expected 'A-1a(01)'); total_payable_by_due_date (got 7935.0, expected 7626.0); total_payable_after_due_date (got 8244.0, expected 7935.0)
- iesco_002: schema-valid, 1 field(s) off: provider (got 'ISLAMABAD ELECTRIC SUPPLY COMPANY (LTD).', expected 'IESCO')
- sngpl_001: schema-valid, 2 field(s) off: provider (got 'Sui Northern Gas Pipelines Limited', expected 'SNGPL'); tariff_category (got 'DOMU- B', expected 'DOMU-B')
- sngpl_002: schema-valid, 1 field(s) off: provider (got 'SUI NORTHERN GAS PIPELINES LIMITED', expected 'SNGPL')
- sngpl_003: schema-valid, 1 field(s) off: provider (got 'Sui Northern Gas', expected 'SNGPL')
- sngpl_004: schema-valid, 1 field(s) off: provider (got 'Sui Northern Gas', expected 'SNGPL')

## Per-field accuracy

- provider: 0/10
- utility: 10/10
- billing_month: 10/10
- issue_date: 10/10
- due_date: 10/10
- tariff_category: 8/10
- sanctioned_load_kw: 9/10
- meter_reading_previous: 10/10
- meter_reading_current: 10/10
- units_consumed: 10/10
- total_payable_by_due_date: 8/10
- total_payable_after_due_date: 6/10
