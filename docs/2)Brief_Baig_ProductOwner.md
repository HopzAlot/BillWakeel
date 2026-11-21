# BillWakeel: Team Member Brief (Baig, Product Owner / Backend)

*Sprint 2 (Jira dates): Fri 14 Nov to Sun 22 Nov 2026. Read together with `CONTRIBUTING.md` and `BillWakeel_DoR_DoD_Roles.md`.*

## How to use this file

This file is a complete brief for one team member. It is written so that you (or an LLM assistant you give it to) can understand the whole project and start work without asking anyone.

**If you are using an LLM (ChatGPT, Claude, Gemini, Copilot, etc.):** paste this file plus `CONTRIBUTING.md` and `BillWakeel_DoR_DoD_Roles.md` into the conversation, then say: *"Read all three documents. I am the person described in Part B. Help me complete my first story step by step, following the repo rules."* Re-paste the files in each new chat. Always run and review the code the LLM gives you. You must be able to explain every line in the viva.

**Rules any assistant must follow when helping with this project:**
1. Never put API keys or real personal bill data in code, commits or chats. Use `.env`; use anonymised samples only.
2. Never let the LLM do bill arithmetic. Money maths is done in plain Python code — this is the whole point of Sprint 2's recalculation engine.
3. Never invent tariff rates, clauses or contact details. Real data comes from official NEPRA/OGRA/utility documents.
4. Follow the branch, commit and PR rules in `CONTRIBUTING.md`. Every commit looks like: `SCRUM-27 #comment short description`.
5. Keep the shared contracts (Part A, section 8) unchanged unless the whole team agrees. If you must change one, tell the group and the owner of that piece first.
6. Prefer small, tested, working pieces over large unfinished ones.

---

# PART A: THE PROJECT (same in every member's brief)

## 1. The project in one paragraph

**BillWakeel** is an agentic web platform for Pakistan. A user uploads a photo or PDF of a utility bill (electricity first, then gas, with water as a one-city pilot). The system reads the bill, recalculates what it should be using the official regulator-approved tariff, and, if something does not match, shows exactly which published clause it differs from and drafts a polite, firm, or very blunt ("No More Mr. Nice Guy") dispute letter. The user reviews the letter and sends it themselves. The platform never submits anything on the user's behalf.

This is our group project for **EC-360 Software Engineering (CEP), NUST CEME, Fall 2026** (instructor: Dr. Farooque Azam). We deliver it in four two-week Scrum sprints, using Jira for tracking and GitHub for code, with Google Gemini (via LangChain) as the AI model. We are also aiming to enter it in competitions, so quality and measured evidence matter, not only a demo.

## 2. The problem and the users

Utility bills in Pakistan are dense and confusing: slab-based unit rates, adjustments that change monthly, several taxes and surcharges, and meter readings that are sometimes estimated rather than measured. Most people pay without checking because checking is hard. When a bill is wrong, complaining is slow and intimidating because people do not know which rule the bill broke.

BillWakeel gives an ordinary person three things: (1) the bill explained in plain language, (2) a clear answer to "is this bill consistent with the published tariff?", and (3) a ready-to-send complaint letter that cites the exact tariff clause.

**Primary users:** households and small shops paying electricity or gas bills. **Secondary users:** consumer-rights volunteers helping others.

## 3. How the system works: the four agents

| # | Agent | Input | Output | Sprint | Status |
|---|---|---|---|---|---|
| 1 | **Extraction Agent** | Bill image or PDF | `BillExtraction`: units, billing period, each charge line, taxes, total | 1 | **Done, merged, working for real.** |
| 2 | **Tariff-Grounding Agent** | Extracted data + official tariff data | `Finding` list: "this charge differs from the tariff by Rs X", each with a cited clause | **2** | **This sprint.** |
| 3 | **Anomaly Agent** | Extracted data + the user's bill history | Flags: spikes, estimated readings, unusual jumps | 3 | Not started |
| 4 | **Dispute-Letter Agent** | Verified findings only | A formal dispute letter in the chosen tone, with a disclaimer | 3 | Not started |

**Sprint 2 builds agent 2**: a deterministic engine recalculates the bill from structured tariff data, a vector store retrieves the exact clause text, and the Grounding Agent ties the two together into cited findings the frontend can display.

## 4. Non-negotiable design rules

1. **Maths lives in code, not the LLM.** A deterministic Python engine (SCRUM-29, Swati) recalculates the bill. The LLM reads, retrieves, explains and writes — it never computes. This is our main hallucination defence, and it becomes real this sprint.
2. **Every finding must cite a real clause.** A finding with no verifiable source clause is dropped before the user sees it. This is the Grounding Agent's central job.
3. **Non-accusatory wording.** "this charge differs from the published tariff clause X", never "the utility is cheating you". Every letter (Sprint 3) carries a "not legal advice" disclaimer.
4. **Human in the loop.** No auto-submit; the user reviews everything.
5. **Model names live in one config setting.** Never hardcode a model name inside agent code. (Loose end: `backend/config.py`'s hardcoded fallback still says `gemini-3.8-flash`; the team actually runs `gemini-3.5-flash-lite` via `.env` after Sprint 1's free-tier rate-limit problem — see `docs/decisions.md`, 2026-10-24. Someone should update the fallback to match.)
6. **Prompts are versioned files**: `prompts/<agent>/v1.md`, `v2.md`, ... never edit a released version. Each change adds a line to `prompts/CHANGELOG.md` with the Jira key.
7. **Privacy by default.** No bill image retention beyond extraction unless opted in. Anonymised samples only in the repo.
8. **Free-tier discipline.** Cache repeated calls, rate-limit guard, avoid model calls in loops. **This sprint's embedding choice is a direct application of this rule** — see section 8.4.

**Known issue from Sprint 1, not in scope this sprint:** `prompts/extraction/v1.md` sometimes picks the *second* (later) payment tier instead of the first for `total_payable_after_due_date` on bills with two tiers. Deferred to a v2 extraction prompt. Not your problem this sprint unless you finish early.

## 5. Scope

| Utility | Coverage | Notes |
|---|---|---|
| Electricity | K-Electric plus 2 more DISCOs this sprint, more in Sprint 3 | One regulator, similar slab logic, different rates |
| Gas | SNGPL and SSGC (Sprint 3) | Regulated by OGRA | 
| Water | One pilot city only, Sprint 4 stretch | No single regulator |

**Out of scope:** auto-submitting complaints, legal advice, payment, claiming bad faith.

## 6. Glossary of Pakistani bill and tariff terms

- **NEPRA**: National Electric Power Regulatory Authority. Approves electricity tariffs. **OGRA**: Oil and Gas Regulatory Authority.
- **DISCO**: electricity distribution company (LESCO, FESCO, GEPCO, IESCO, MEPCO, PESCO, HESCO, SEPCO, QESCO, TESCO). **K-Electric** is a separate private utility.
- **Slab**: a band of units with its own per-unit rate.
- **Tariff category**: the code on the bill (e.g. `A-1a(01)`) that picks which rate table applies.
- **Clause**: a specific numbered or titled provision in a tariff notification — a citation names the clause, not just the document.
- **FPA/FCA, QTA**: fuel/fuel-charge and quarterly tariff adjustments — monthly/quarterly changing line items.
- **Sanctioned load**: the connection capacity (kW) registered.
- **Estimated reading**: billed without an actual meter reading — a common complaint source.

## 7. Tech stack and repository layout (current, as of Sprint 2 start)

**Stack:** FastAPI + React (Vite) + LangChain/`langchain-google-genai` + Google Gemini (`gemini-3.5-flash-lite` via `.env`) + Pydantic + **SQLite/SQLAlchemy (this sprint)** + **sentence-transformers for local embeddings (this sprint)** + pytest.

```
BillWakeel/ 
├── backend/
│   ├── main.py            # FastAPI app, CORS, router registration — working
│   ├── config.py          # Settings from .env — working
│   ├── api/
│   │   └── bills.py        # /bills endpoints — working end to end; you add the sources
│   │                        # table / data gathering, and later the /findings route wiring
│   ├── agents/
│   │   ├── extraction.py   # Extraction Agent v0 — real, working
│   │   └── grounding.py     # Rehan adds this: Tariff-Grounding Agent (SCRUM-31)
│   ├── services/
│   │   ├── gemini.py        # get_llm(), invoke_with_retry(), GeminiError — working
│   │   ├── tariff_engine.py # Swati adds this: deterministic recalculation (SCRUM-29)
│   │   └── tariff_retrieval.py # Rehan adds this: vector store + retrieval (SCRUM-30)
│   ├── models/
│   │   ├── bill.py          # BillExtraction, ChargeLine — working
│   │   ├── tariff.py        # Ayesha adds this: structured tariff schema (SCRUM-28)
│   │   ├── finding.py       # Rehan adds this: Finding, FindingsResponse
│   │   └── db_models.py     # Ayesha adds this: SQLAlchemy ORM models (SCRUM-33)
│   └── requirements.txt
├── frontend/                # working upload → extract → editable form → save flow
│   └── src/components/
│       └── FindingsView.jsx # ← you add this (SCRUM-34)
├── prompts/extraction/v1.md # working, known tier-selection bug, not this sprint's problem
├── data/
│   ├── tariffs/
│   │   ├── raw/             # ← you add this: source PDFs/pages (SCRUM-27)
│   │   └── structured/      # ← Ayesha adds this: tariff JSON (SCRUM-28)
│   ├── samples/              # 10 anonymised bills + ground truth — done
│   └── uploads/               # gitignored, runtime
├── tests/
├── docs/                      # decisions.md, roadmap, this brief
├── CONTRIBUTING.md
└── README.md
```

Repo: https://github.com/HopzAlot/BillWakeel. Jira key: `SCRUM`. Board: https://software-ka-project.atlassian.net/jira/software/projects/SCRUM/boards/1

## 8. The shared contracts

### 8.1 `BillExtraction` (Sprint 1, unchanged, finalized)
Still the Extraction Agent's output, in `backend/models/bill.py`. Meter readings and `units_consumed` are floats, not ints — don't redeclare them.

### 8.2 The Sprint 1 API (unchanged, working)
`GET /health`, `POST /bills`, `POST /bills/{bill_id}/extract`, `PUT /bills/{bill_id}/extraction` — all live in `backend/api/bills.py`, which you own.

### 8.3 The structured tariff JSON (Sprint 2 — Ayesha owns, document what you give her)
Your SCRUM-27 is the raw input to Ayesha's SCRUM-28 schema. When you collect sources, note down for each document: DISCO, tariff category it covers, effective date, and the exact fields you can see (slab boundaries, per-unit rates, fixed charges, named taxes/surcharges). The clearer your notes, the faster Ayesha can design the schema around real data instead of guessing.

### 8.4 The `Finding` contract (Sprint 2 — Rehan proposes, you consume for SCRUM-34)
Rehan is proposing this for his Grounding Agent (SCRUM-31). Expect roughly:

```python
class Finding(BaseModel):
    charge_name: str
    billed_amount_pkr: float
    expected_amount_pkr: float
    difference_pkr: float
    clause_id: str
    clause_text: str
    source_url: str
    confidence: Literal["high", "medium", "low"] = "high"

class FindingsResponse(BaseModel):
    bill_id: str
    findings: list[Finding]
    recalculated_total_pkr: float
    model: str
```

via `GET /bills/{bill_id}/findings`. Confirm the exact field names with Rehan before you build SCRUM-34's UI against it — don't guess.

### 8.5 Embedding choice (locked decision)
SCRUM-30's vector store uses a local embedding model (`sentence-transformers`), not Gemini's embedding API — logged in `docs/decisions.md`, 2026-11-14, because Gemini's free tier is already tight after Sprint 1's rate-limit problem. Not your story, but good context for the viva.

## 9. Sprint 2 at a glance

**Sprint goal:** the system recalculates a bill from official tariff data and reports discrepancies, each with a cited clause.

**Measurable targets:** tariff corpus covers K-Electric plus 2 more DISCOs with source URL and retrieval date for every document; recalculation engine reproduces the billed total within a documented tolerance on clean samples; zero uncited findings on the seeded-error set.

**Jira dates:** Fri 14 Nov → Sun 22 Nov 2026. **Note honestly:** the roadmap's official Sprint 2 dates were 26 Oct–6 Nov; the team is running about a week late. The Jira sprint uses the real working dates instead of the official ones so the burndown reflects what actually happened — this should be named plainly in the retrospective.

| Jira | Story | Pts | Owner | Role this sprint |
|---|---|---|---|---|
| SCRUM-27 | Collect raw tariff sources with source metadata | 3 | **Baig** | **Product Owner** |
| SCRUM-28 | Structured tariff JSON schema for 3 DISCOs | 5 | Ayesha | Developer |
| SCRUM-29 | Deterministic bill recalculation engine | 5 | Swati | Developer |
| SCRUM-30 | Vector store and clause retrieval over tariff documents | 5 | Rehan | Scrum Master |
| SCRUM-31 | Tariff-Grounding Agent v1 with citations | 8 | Rehan | Scrum Master |
| SCRUM-32 | Support a second bill layout in extraction | 3 | Swati | Developer |
| SCRUM-33 | Database models for bills and findings | 3 | Ayesha | Developer |
| SCRUM-34 | UI: findings view with cited clause | 2 | **Baig** | **Product Owner** |

**Role rotation (required every sprint):**

| Sprint | Scrum Master | Product Owner | Developers |
|---|---|---|---|
| 1 | Ayesha | Swati | Rehan, Baig |
| **2 (now)** | Rehan | **Baig** | Ayesha, Swati |
| 3 | Swati | Ayesha | Rehan, Baig |
| 4 | **Baig** | Rehan | Ayesha, Swati |

Everyone is Scrum Master once, Product Owner once, Developer twice across the four sprints. **SM and PO still write code and make individual commits every sprint — that's graded**, which is why you have SCRUM-27 and SCRUM-34 as a Product Owner this time, same pattern as Swati's PO stories in Sprint 1 (sample collection + tests — concrete, well-scoped, not the hardest technical lift). Note for context: Rehan (SM this sprint) deliberately took the two heaviest, most AI-experience-dependent stories instead of lighter SM-typical work, because he built Sprint 1's Extraction Agent and judged it lower-risk for him to be hands-on there. That's his call to explain in the viva, not yours — but it's why the point distribution looks uneven this sprint.

## 10. Team-wide Sprint 2 timeline

| Day | What should happen |
|---|---|
| Fri 14 Nov | Sprint planning. Jira sprint confirmed (14–22 Nov). Everyone branches from `dev`. You start SCRUM-27 — urgent, it unblocks Ayesha and Rehan. |
| Sat 15 Nov | You continue/finish SCRUM-27, hand raw sources to Ayesha and Rehan. |
| Sun 16 Nov | Ayesha starts SCRUM-28 using your sources. Rehan starts SCRUM-30 (doesn't need Ayesha's schema, just your raw text). |
| Mon 17 Nov | **Mid-sprint check, burndown screenshot 1.** Ayesha continues SCRUM-28. Swati starts SCRUM-29. |
| Tue 18 Nov | Ayesha merges SCRUM-28. Swati finishes SCRUM-29. Rehan merges SCRUM-30 and shares the `Finding` contract proposal — confirm it. |
| Wed 19 Nov | Rehan starts SCRUM-31. Ayesha starts SCRUM-33 against the confirmed `Finding` shape. Swati starts SCRUM-32. |
| Thu 20 Nov | Ayesha merges SCRUM-33. You start SCRUM-34 once Rehan's `/findings` endpoint has at least a stub. Swati finishes SCRUM-32. |
| Fri 21 Nov | Rehan merges SCRUM-31. You finish SCRUM-34 wired to the real endpoint, merge. Integration day. |
| Sat 22 Nov | **Sprint review and demo. Burndown screenshot 2. Retrospective. Role rotation to Sprint 3. Velocity logged.** |

## 11. Communication and escalation

- Daily 10-minute standup (chat is fine) — Rehan runs this as SM.
- Blocked more than half a day? Post in the group chat and tag the dependency owner.
- Anything that changes a shared contract (8.1–8.5) goes to the whole group before code changes.
- PRs: a teammate who did not write the code reviews. Reviews should happen within a day.

---

# PART B: YOUR BRIEF, MUHAMMAD ABDULLAH BAIG

**Sprint 2 role: Product Owner. Stories: SCRUM-27, SCRUM-34 (5 points).**

You're the Product Owner this sprint — backlog ownership, acceptance criteria, demo prep — same pattern Swati had in Sprint 1 as PO. Your two stories are deliberately well-scoped rather than the hardest technical lift: gathering real source data (SCRUM-27, which everyone else depends on) and a focused UI piece (SCRUM-34).

## B1. Your stories in order

### SCRUM-27: Collect raw tariff sources with source metadata (3 pts), start TODAY (Fri 14 Nov)
**Goal:** official NEPRA/DISCO tariff documents, saved with enough metadata that every number in the system is traceable back to a real source.

**This is urgent — Ayesha's SCRUM-28 and Rehan's SCRUM-30 both wait on you.**

1. Find the official tariff notification for K-Electric plus 2 more DISCOs (pick ones with clearly published PDFs — NEPRA's website and the DISCOs' own tariff pages are the primary sources). Never invent or approximate a rate — if you can't find an official document for a DISCO, pick a different one rather than guess.
2. Save the raw PDFs/pages under `data/tariffs/raw/<disco>/`.
3. Build a sources table (a simple CSV or Markdown table is fine) listing, for each document: DISCO, URL, retrieval date (today), effective date (as printed on the document, not assumed).
4. As you read each document, jot down the fields you can see for Ayesha (slab boundaries and rates, fixed charges, named taxes) — this feeds section 8.3.

**Acceptance criteria:** "Raw PDFs/pages saved under data/tariffs/raw; a sources table lists URL, retrieval date and effective date for each."

**Commit example:** `SCRUM-27 #comment add K-Electric, IESCO and LESCO tariff PDFs with sources table`

### SCRUM-34: UI: findings view with cited clause (2 pts)
Branch: `feature/SCRUM-34-findings-view`.

**Goal:** the user sees each discrepancy and the exact clause it's based on.

1. `frontend/src/components/FindingsView.jsx`: given a `FindingsResponse` (section 8.4), render each finding as billed amount vs. expected amount vs. difference, plus the quoted clause text and a link to `source_url`.
2. An empty state when `findings` is an empty list — a bill with no discrepancies should say so clearly, not look broken.
3. Wire it into `UploadPage.jsx` (or wherever makes sense given the existing flow) to call `GET /bills/{bill_id}/findings` once an extraction exists, following the same `frontend/src/services/billApi.js` pattern as the existing `uploadBill`/`extractBill`/`saveExtraction` calls.

**Acceptance criteria:** "Findings list shows amount difference and quoted clause with source link; empty state shown when nothing is found."

**Commit examples:** `SCRUM-34 #comment add FindingsView component` / `SCRUM-34 #comment wire findings fetch into upload page` / `SCRUM-34 #comment add empty state for zero findings`

## B2. Day-by-day plan

| Day | Tasks |
|---|---|
| Fri 14 Nov | Sprint planning. Start SCRUM-27 immediately — this blocks two other people. |
| Sat 15 Nov | Finish SCRUM-27: sources table complete, hand notes to Ayesha and Rehan. |
| Sun 16 Nov | SCRUM-27 PR review and merge. As PO, check in on acceptance criteria wording for the other stories if anyone's unsure. |
| Mon 17 Nov | **Mid-sprint check, burndown screenshot 1** (support Rehan, who runs it). |
| Tue 18 Nov | Confirm the `Finding` contract Rehan shares — ask questions now, not after you've built against it. |
| Wed 19 Nov | Start sketching SCRUM-34's UI against a mocked `FindingsResponse` while Rehan's endpoint isn't ready yet. |
| Thu 20 Nov | Wire SCRUM-34 to Rehan's real stub/endpoint once available. |
| Fri 21 Nov | Finish and merge SCRUM-34. Integration day. |
| Sat 22 Nov | **Sprint review and demo** — you can demo the findings UI. Burndown screenshot 2. Retrospective. |

## B3. Hand-offs
- **To Ayesha:** raw tariff sources + your field notes (needed to start SCRUM-28).
- **To Rehan:** raw tariff sources (needed to start SCRUM-30).
- **From Rehan:** the confirmed `Finding` schema and a working `/findings` endpoint (needed for SCRUM-34).

## B4. Review duties
You review **Rehan's** PRs (SCRUM-30, SCRUM-31). **Swati** reviews yours (SCRUM-27, SCRUM-34). Check: runs locally, no secrets, commit format, acceptance criteria met.

## B5. Pitfalls
- Don't approximate or guess a tariff rate if you can't find the official document — pick a DISCO you can actually source, or flag the gap to the group.
- Don't build SCRUM-34 against a `Finding` shape you haven't confirmed with Rehan — same mistake Sprint 1 warned about with endpoint response shapes.
- Don't skip the empty-state case — a findings view with no empty-state handling looks broken the first time someone uploads a clean bill in the demo.

## B6. Viva preparation checklist
Be ready to explain: where your tariff sources actually came from and why they're authoritative (official NEPRA/DISCO documents, not scraped third-party summaries); how the sources table gives traceability from a number in the system back to a real published document; what the findings UI shows and why an empty state matters; your role as Product Owner this sprint and what backlog/acceptance-criteria work you did beyond your two coding stories.

## B7. Starter prompts for your LLM
- "Help me find the official published electricity tariff notification pages for K-Electric, IESCO and LESCO from NEPRA or the DISCOs' own websites."
- "Write a React component that renders a list of findings, each showing billed vs. expected amount, a difference, a quoted clause with a source link, and an empty state when the list is empty."
- "Write a fetch function matching this existing billApi.js pattern for a new GET /bills/{bill_id}/findings endpoint."

## B8. Sprint 2 done checklist
- [ ] SCRUM-27, SCRUM-34 merged to `dev` via reviewed PRs, tickets Done with points.
- [ ] Sources table complete with URL, retrieval date, effective date for every document.
- [ ] Findings UI demonstrated with both a populated list and an empty state.
- [ ] Every commit uses `SCRUM-n #comment ...`.
