# Structured Tariff Data

One JSON file per tariff category, validated by `backend/models/tariff.py` and read by
`backend/services/tariff_engine.py`. All files sit in `k-electric/`, but each lists the DISCOs it
applies to: K-Electric, IESCO and LESCO share the government's uniform schedule. `ke_tariff.json`
is the A-1(a) protected household schedule and is used in calculations like the others.

## Fields

| Field | Description |
|---|---|
| `discos` | DISCOs the schedule applies to |
| `tariff_code`, `tariff_category` | Code printed on the bill, and its category |
| `consumer_status` | `lifeline`, `protected` or `unprotected`; only A-1(a) splits by it |
| `billing_method`, `metering_type` | `telescopic`, `landing_slab` or `flat`; `regular`, `tou` or `prepaid` |
| `effective_from`, `effective_to` | Dates the schedule applies |
| `slabs` | Unit ranges, per-unit rates and any per-slab fixed charge |
| `fixed_charge` | Amount and calculation method |
| `minimum_monthly_charge_pkr`, `minimum_charge_includes_fixed` | Minimum bill, and whether the fixed charge counts towards it |
| `adjustments` | Quarterly adjustments, each limited to its billing months |
| `taxes` | Rate and base; `discos` limits a line to some DISCOs (provincial duty) |
| `source` | Document, link and retrieval date |

## Sources and checks

Rates and fixed charges were checked against SRO 279(I)/2026. Where each other number comes from is
listed in `../raw/sources.md`; reasoning and known limits are in `docs/decisions.md`.

## Keeping it current

- A quarterly adjustment is recorded for December 2025 to November 2026. Add each new one to every
  file that has `adjustments`, and add its row to `../raw/_official/sro_rows_2026.md`.
- Never fill a value from memory, a news report or a calculator website. Use a notification or an
  official page, and record it in `../raw/sources.md`.
