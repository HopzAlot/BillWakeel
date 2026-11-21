# Structured Tariff Data

This directory contains structured tariff JSON files for electricity distribution companies (DISCOs).

## Current Status

The `ke_tariff.json` file is a placeholder template for development and schema validation.

**It does not contain official K-Electric tariff rates and must not be used for bill calculations.**

## Tariff JSON Fields

| Field | Description |
|---|---|
| `disco` | Distribution company name |
| `tariff_category` | Applicable consumer tariff category |
| `effective_from` | Tariff start date |
| `effective_to` | Tariff end date, if applicable |
| `slabs` | Consumption ranges and per-unit rates |
| `fixed_charge_pkr` | Fixed charge in PKR |
| `adjustments` | FCA, FPA, or QTA adjustments |
| `taxes` | Applicable taxes and their calculation basis |
| `source` | Official document URL, retrieval date, and reference |

## Data Requirements

Before adding production tariff records:

1. Obtain official tariff documents.
2. Verify slab limits and rates against the source.
3. Confirm fixed charges, adjustments, and tax rules.
4. Record effective dates and source metadata.
5. Validate each JSON file against `backend/models/tariff.py`.

## Pending Confirmations

- Final schema field names and structure: pending team approval.
- Tax calculation basis: pending confirmation.
- Adjustment representation: pending confirmation.
- Official K-Electric tariff data: pending source documents.

Do not replace placeholder values with assumed tariff information.
