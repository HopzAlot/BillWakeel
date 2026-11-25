# Sprint 2 handover: gaps found, what was changed, and notes for next sprint

Written 2026-11-25 by Rehan (Scrum Master). All changes listed here were made on
`feature/SCRUM-31-grounding-agent` under SCRUM-31. Most gaps only showed up once the pieces were
joined and run on real bills. Reasoning and evidence are in `docs/decisions.md`; sources are in
`data/tariffs/raw/sources.md`. Owners follow the Jira assignee of each story.

## Abdullah Baig (SCRUM-27 sources, SCRUM-34 findings UI)

**Gaps in SCRUM-27**
- The sources table listed some PDFs as "to download" that were already in the repo, and others
  had not been downloaded.
- The main data source was a secondary guide. It differs from the notified SRO 279 schedule for
  B-5, D-2(b), E-1, E-2, G, H and Rawat Lab, and has only one quarterly adjustment. The extracts
  were labelled as secondary and needing a cross-check, which had not been done.

**What was changed**
- Downloaded the missing documents and added the official ones now relied on.
- Added `data/tariffs/raw/_official/`, whose rows replace the wrong guide rows in search. The guide
  extracts are unchanged.

**SCRUM-34:** nothing changed. No commits for it were visible on GitHub on 2026-11-25.

**For future items**
- The findings response now has a `warnings` list. Show it: it says what was assumed or not checked.
- Show each finding's clause text and source link. An empty findings list does not mean every charge
  was checked.
- When collecting a source, open it, record its status truthfully and prefer the notification itself.

## Ayesha Zafar (SCRUM-28 tariff data, SCRUM-33 database models)

**Gaps in SCRUM-28**
- Prepaid residential was 42.13 (should be 42.12). Prepaid bulk held the industrial rate, 35.72
  (should be 44.87). Rawat Lab was 33.75, copied from the guide (should be 42.25).
- No prepaid agricultural tariff (the guide does not have it).
- Minimum monthly charges were missing for lifeline and agricultural tariffs.
- No quarterly adjustments were recorded.
- IESCO and LESCO shared K-Electric's Electricity Duty rates, which are wrong for Punjab commercial
  and industrial consumers.
- `data/tariffs/structured/README.md` still called a live file a placeholder.

**What was changed**
- Corrected the rates, added the tariff and minimum charges, and added adjustments for December 2025
  to November 2026.
- Schema: added `effective_from_month`/`effective_to_month` on adjustments,
  `minimum_charge_includes_fixed`, and `discos` on each tax. The engine input also gained
  `billing_month` and `billed_surcharges_pkr`.
- Rewrote the README and pointed each file's `source` at SRO 279.

**For future items**
- SCRUM-33: store the finding's `explanation` and `source_url`, and the response's `warnings`.
  No commits for SCRUM-33 were visible on GitHub on 2026-11-25.
- Check each rate against the notification, not only the guide, and add a test for it.
- Add each new quarterly adjustment when notified. None is recorded after November 2026.
- Gas tariffs (Sprint 3): start from the OGRA notification.

## Abdullah Swati (SCRUM-29 engine, SCRUM-32 second bill layout)

**Gaps in SCRUM-29**, found by comparing with real bills
- GST left out Electricity Duty and surcharges, so correct bills were flagged.
- IESCO and LESCO duty is charged on energy plus the quarterly adjustment, not energy alone.
- The minimum charge could not apply to tariffs that also have a fixed charge.
- Adjustments had no time limit, and taxes could not differ by company.

**What was changed** in `tariff_engine.py`
- New tax bases for the two cases above; GST is now calculated after the other taxes.
- Time-limited adjustments, per-company taxes and the agricultural minimum floor.
- Expected totals in your engine tests were updated to match.

The tax-base evidence is two IESCO bills and one HAZECO bill. K-Electric's duty base is unchanged
because we have no K-Electric bill. The agricultural minimum is our reading of the schedule's
wording. Please review both.

**SCRUM-32:** nothing changed in the gas work.

**For future items**
- Test calculations against real bills. A test whose "correct" value comes from the engine cannot
  find an engine error.
- The extraction eval does not score individual charge lines. Add that before relying on them.

## Gaps in my own work (SCRUM-10, 30, 31)

These were as serious as any above.
- The agent guessed every household was "protected", which produced false findings on real bills.
- Retrieval often cited another tariff's row.
- The seeded eval used engine output as the correct values, so it missed both and the tax errors.
- The findings endpoint rejected the full company names that extraction returns.
- The extraction prompt picked the wrong late-payment total.

Retrieval, the eval gap and company names are fixed. The other two belong to later work:

- **Household type (SCRUM-51):** the guess is gone, but nothing replaces it yet. For household bills,
  energy, fixed charge, GST and duty are **not checked** (nor the quarterly adjustment at 100 units
  or less), and the response says so.
- **Late-payment total:** extraction stays on prompt v1 and the bug remains.

## Open items for the next sprint

| Item | Suggested owner |
|---|---|
| Extraction misreads some charge labels (April IESCO bill: duty read as "TV FEE") | Extraction |
| Capture consumer status (SCRUM-51); until then household bills are barely checked | Extraction |
| Extraction prompt v2 for the late-payment total | Extraction |
| Verify K-Electric's duty base with a real K-Electric bill | Engine |
| Official sources for surcharge rates and Islamabad duty | Tariff data |
| Monthly fuel price adjustment is not checked (needs bill history) | Engine |
| Duty on single-point (C) tariffs for IESCO and LESCO has no clause | Tariff data |
| K-Electric non-time-of-use B-3/B-4 rates and three-phase lifeline minimum | Tariff data |
| Gemini daily limit is not tracked | Backend |

Owners are suggestions until sprint planning.
