# Field notes for SCRUM-28 (Ayesha) and SCRUM-30 (Rehan)

Source for everything below: the tariff guide (S01) unless another source is named. Scope this sprint: K-Electric, IESCO, LESCO, electricity only.

## 1. Key finding: the schedule is uniform
All three utilities use the same Federal Government uniform consumer-end schedule for 2026 (guide section 1 and 2; KE page S06 says the same). There is **no DISCO-specific rate table** in the sources. So the schema needs one rate table, plus a `disco` list saying which utilities it applies to. Do not invent per-DISCO differences.

## 2. Domestic A-1(a), sanctioned load below 5 kW
Selector fields: tariff code `A-1a(01)`, consumer status (Lifeline / Protected / Unprotected), monthly units, sanctioned load in kW.

| Class | Slab (units) | Fixed Rs/kW | Variable Rs/kWh | Rule |
|---|---|---|---|---|
| Lifeline | 1-50 | 0 | 3.95 | no slab benefit, exempt from fixed charges |
| Lifeline | 51-100 | 0 | 7.74 | no slab benefit, exempt from fixed charges |
| Protected | 1-100 | 200 | 10.54 | telescopic: one previous slab benefit |
| Protected | 101-200 | 300 | 13.01 | first 100 units at 10.54, rest at 13.01 |
| Unprotected | 1-100 | 275 | 22.44 | landing slab: all units at the reached slab rate |
| Unprotected | 101-200 | 300 | 28.91 | landing slab |
| Unprotected | 201-300 | 350 | 33.10 | landing slab |
| Unprotected | 301-400 | 400 | 36.46 | rationalized from 37.99 |
| Unprotected | 401-500 | 500 | 38.95 | rationalized from 40.20 |
| Unprotected | 501-600 | 675 | 40.22 | rationalized from 41.62 |
| Unprotected | 601-700 | 675 | 41.85 | rationalized from 42.76 |
| Unprotected | above 700 | 675 | 47.20 | rationalized from 47.69 |

Status rule: Protected only if usage stays at or below 200 units for 6 consecutive months; one month above 200 removes protection for the next 6 months. The bill alone cannot prove status, so the engine needs it as an input (or flags low confidence).

Fixed charge rule (2026): applies to all domestic consumers except Lifeline. Non-TOU below 5 kW: per kW of sanctioned load. Where fixed charges apply, the minimum monthly charge does not. Minimum charge otherwise: Rs. 75 single phase, Rs. 150 three phase.

## 3. Domestic 5 kW and above, and prepaid
- A-1(b) TOU: Peak Rs. 46.85, Off-Peak Rs. 34.53; fixed Rs. 675/kW billed on 50% of sanctioned load or actual MDI, whichever is higher.
- A-1(c) Pre-Paid: flat Rs. 42.12, fixed Rs. 675/kW.

## 4. Commercial and general services (A-2, A-3)
A-2(a) <5 kW: Rs. 1,000/consumer/month, Rs. 37.44. A-2(b) >=5 kW: Rs. 1,250/kW, Rs. 39.76. A-2(c) TOU: Peak 43.82, Off-Peak 35.15 (fixed Rs. 1,250/kW). A-2(d) EV charging: nil fixed, Rs. 23.57. A-2(e) prepaid: Rs. 1,250/kW, Rs. 42.38. A-3(a) and A-3(c): Rs. 1,000/consumer/month, Rs. 42.48. Fixed charges billed on 25% of sanctioned load or actual MDI, whichever is higher. The full industrial (B), bulk (C), agricultural (D), E, F, G, H, K tables are in the extracts; household and shop bills are the Sprint 2 priority.

## 5. Line items that sit on top of the base charge
| Line item | Value in the guide | Applied to | GST? |
|---|---|---|---|
| FCA / FPA | monthly, about -0.37 to +6.80 Rs/kWh | per kWh | yes |
| QTA | quarterly, e.g. -1.9857 Rs/kWh for Jun-Aug 2026 (confirmed by S07) | per kWh, non-lifeline | yes |
| Financing Cost surcharge | 0.43 to 3.23 Rs/kWh, slab dependent | per kWh, not lifeline | yes |
| Neelum-Jhelum surcharge | 0.10 Rs/kWh (guide also says "up to 0.50-1.00 in specific adjustments") | per kWh, above lifeline | yes |
| Electricity Duty | 1.5% (KE page S06: Commercial 2%, Industrial 1.5%, Bulk 2%, Agricultural 1%) | base energy charges | no |
| GST | 18% | energy + fixed + FCA + QTA + FC + NJ | n/a |
| Further / Extra tax | 1-4% / 5-17% | unregistered commercial and industrial only | n/a |
| Advance income tax s.235 | domestic 7.5% if bill >= Rs. 25,000 (non-filers) | total incl. GST | no |
| PTV fee | Rs. 35 domestic, Rs. 60 commercial | flat | no |
| Meter rent | Rs. 7.50 to 40 | flat | no |
| Late payment surcharge | 10% of current bill | after due date | no |

## 6. Gaps: do NOT guess these, get the real values
1. **Financing Cost surcharge per slab.** The guide gives only the range 0.43 to 3.23. The worked example uses 0.43 for 195 units and 3.23 for 205 units. The per-slab table must come from the official schedule (S02/S03).
2. **FCA and QTA per month.** Not in the guide except the one QTA example. Needs the monthly NEPRA/utility notifications (S07 and later ones).
3. **Neelum-Jhelum**: 0.10 versus "up to 0.50-1.00" is ambiguous.
4. **Electricity duty** differs by category in the KE page but the guide gives a single 1.5%.
5. **Newer notification:** the KE page (S06) lists SRO 150 dated 07 Sep 2026, later than everything in the guide. Read it before finalising rates.

## 7. Errors and inconsistencies found in the guide
1. **Arithmetic error, worked example 5.1, Scenario A.** (100 x 10.54) + (95 x 13.01) = 1,054.00 + 1,235.95 = **Rs. 2,289.95**, but the guide prints Rs. 2,289.45. The Electricity Duty, GST and total (Rs. 3,946.00) in that column are all built on the wrong figure. Using 2,289.95 gives a total of about Rs. 3,946.59. **Do not use Scenario A's printed total as a test fixture.** Scenario B checks out.
2. **Gas slab rule contradiction.** Guide section 4.1 says gas slabs are progressive/telescopic, but worked example 5.2 bills the whole 4.9691 MMBTU at the Slab 4 rate (landing-slab style). The engine cannot be built for gas until the official OGRA rule is confirmed. Sprint 3, but flagged now.
3. **Guide is a secondary compilation.** It is not an official gazette. Every number must be confirmed against S02/S03 before it is called authoritative.

## 8. What I checked
Worked example 5.1 Scenario B and worked example 5.2 recompute correctly (10,138.05 and 10,319.34). Domestic base rates for protected, lifeline and the unprotected 601+ slabs match press reports of the NEPRA decision (Express Tribune, Jan and Mar 2026), including the pre-rationalization figures quoted as "rationalized from".
