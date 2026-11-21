# Tariff Data Organization

This directory stores electricity tariff documents and their structured data for BillWakeel.

## Directory Structure

- `raw/` — Original tariff documents collected from official sources. These documents should remain unchanged.
- `structured/` — Tariff data converted into JSON format and validated against the tariff schema.

## Supported DISCOs

Currently, the project is organized for:

- K-Electric
- IESCO
- LESCO

Each provider has its own folder inside both `raw/` and `structured/`.

## Data Workflow

1. Collect official tariff documents.
2. Store the original documents in the appropriate `raw/` provider folder.
3. Extract and verify tariff information from the official documents.
4. Convert the verified information into JSON using the tariff schema.
5. Validate the JSON data before using it in the tariff engine.

## Important

Tariff rates, taxes, adjustments, and other tariff details must be based on official sources. No tariff values should be assumed or invented.

The existing K-Electric JSON file is a placeholder template and does not contain official tariff data.
