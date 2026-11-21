# SCRUM-27: Collect raw tariff sources with source metadata

**Owner:** Baig (Product Owner, Sprint 2) | **Points:** 3 | **Branch:** `feature/SCRUM-27-raw-tariff-sources` | **Reviewer:** Swati

## Definition of Ready (checked at planning)
| # | Check | Status |
|---|---|---|
| 1 | "As a / I want / so that" | Add to Jira: *As the team, we want official tariff sources saved with metadata, so that every number in the system is traceable.* |
| 2 | Demonstrable acceptance criteria | Yes: "Raw PDFs/pages saved under data/tariffs/raw; a sources table lists URL, retrieval date and effective date for each." |
| 3 | Estimate agreed | 3 points |
| 4 | Fits in a sprint (<= 8) | Yes |
| 5 | Dependencies | Blocks SCRUM-28 (Ayesha) and SCRUM-30 (Rehan) |
| 6 | Data available | Tariff guide supplied; official URLs located (see `data/tariffs/raw/sources.md`) |
| 7 | Prioritised, one owner | Baig |

## Definition of Done
| # | Criterion | Status |
|---|---|---|
| 1 | Merged to `dev` via PR reviewed by someone who did not write it | PENDING: open PR into `dev`, Swati reviews |
| 2 | Unit tests written and passing | N/A in substance (data-only story, no code). Say so in the PR description. |
| 3 | Acceptance criteria demonstrated at review | Ready to demo (see below) |
| 4 | Smart commits + PR title with Jira key | PENDING: use the commit messages below, PR title `SCRUM-27 Raw tariff sources with metadata` |
| 5 | Prompt/agent changed? | No |
| 6 | No secrets committed | Yes: data and docs only |
| 7 | Docs updated; decision logged if needed | Draft decision entry below, to paste into `docs/decisions.md` |
| 8 | Jira ticket Done with points | PENDING after merge |

## Honest status against the acceptance criteria
- Raw pages saved under `data/tariffs/raw`: **partly met.** The tariff guide and per-DISCO verbatim extracts are saved. The official NEPRA/KE PDFs (S02, S04, S05, S07) have URLs but were **not downloaded** because the build environment could not reach nepra.org.pk. Download them by hand and save them as listed in `sources.md`.
- Sources table lists URL, retrieval date and effective date: **met**, with "to be read" for effective dates of PDFs not yet opened. Row S03 (SRO 279(I)/2026) has no URL yet.
- The brief says sources must be official documents, not third-party summaries. The guide is a secondary compilation, so treat the data as provisional until S02/S03 are saved.

## Suggested commits (one logical change each)
```
SCRUM-27 #comment add tariff guide and per-DISCO extracts for K-Electric, IESCO and LESCO
SCRUM-27 #comment add sources table with URL, retrieval date and effective date
SCRUM-27 #comment add field notes and guide error list for tariff schema
SCRUM-27 #comment add SCRUM-27 DoR and DoD check
```
Commit with the same email as your Jira and GitHub accounts, otherwise the commits will not count.

## Draft entry for `docs/decisions.md`
```
## 2026-11-21: One uniform tariff table for K-Electric, IESCO and LESCO (SCRUM-27)
The sources (guide section 2, KE page) show a single Federal Government uniform consumer-end schedule for CY2026 shared by all ex-WAPDA DISCOs and K-Electric, so the raw corpus holds one rate table per utility folder rather than three different ones. The compiled tariff guide is used as the interim data source until the official NEPRA decision (TRF-100, 11.02.2026) and SRO 279(I)/2026 are saved. Rejected: using the IESCO tariff-guide web page, which still shows the 2023 schedule.
```

## Handoff checklist
- [ ] Tell Ayesha: read `field_notes_for_SCRUM-28.md`, especially sections 6 and 7 (gaps and guide errors).
- [ ] Tell Rehan: raw text is under `data/tariffs/raw/*/tariff_extract_2026.md`.
- [ ] Download S02, S04, S05, S07 and update `sources.md` status to SAVED.
- [ ] Retrospective note: SCRUM-27 was planned for 14-15 Nov and was delivered later, which delayed SCRUM-28 and SCRUM-30.

## Quick demo script (sprint review)
1. Open `data/tariffs/raw/sources.md`: every row has URL, retrieval date, effective date.
2. Open `data/tariffs/raw/k-electric/tariff_extract_2026.md`: metadata header plus verbatim rates.
3. Open `field_notes_for_SCRUM-28.md` section 7: the arithmetic error found in the guide.
