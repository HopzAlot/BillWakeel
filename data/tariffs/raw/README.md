# data/tariffs/raw

Raw tariff sources for SCRUM-27 (Sprint 2). This is the input to Ayesha's structured tariff schema (SCRUM-28) and Rehan's clause retrieval (SCRUM-30).

| Path | What it is |
|---|---|
| `sources.md` / `sources.csv` | Sources table: URL, retrieval date, effective date as printed, status for every document |
| `field_notes_for_SCRUM-28.md` | Fields visible in the sources (slabs, rates, fixed charges, taxes) plus gaps and inconsistencies |
| `_shared/` | The full tariff guide (secondary compilation) |
| `k-electric/`, `iesco/`, `lesco/` | Per-DISCO folder with a verbatim extract of the electricity schedule (guide sections 2 and 3) and a metadata header |

Rules: never edit a raw file, never invent a rate or URL. If a number is not in a source, it is not in the system.
