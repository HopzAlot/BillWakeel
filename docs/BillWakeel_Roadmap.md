# BillWakeel — Project Roadmap (Sprints 1–4)

**Course:** EC-360 Software Engineering (CEP), NUST CEME, Fall 2026
**Team:** Muhammad Rehan Saqib, Muhammad Abdullah Baig, Muhammad Abdullah Swati (GC), Ayesha Zafar
**Stack:** FastAPI (backend) + React/Vite (frontend) + LangChain + Google Gemini
**Repo:** https://github.com/HopzAlot/BillWakeel | **Jira:** SCRUM board (link in Sprint 0 report)

> **How to read this file.** It is a plan, not a contract. Story points and numeric targets are starting estimates. Re-plan each sprint from the velocity you actually measure. Dates below are the instructor's official deadlines. Create the Jira sprints with exactly these dates so the burndown matches.

| Sprint | Weeks | Dates | Theme |
|---|---|---|---|
| 0 | - | submitted 27 Sep | Setup, Jira, GitHub, Gemini connection (done) |
| 1 | 1–2 | Mon 12 Oct → Fri 23 Oct (P-2 due Sun 25 Oct) | Foundations and first vertical slice (bill in, structured data out) |
| 2 | 3–4 | Mon 26 Oct → Fri 6 Nov | Tariff knowledge base and grounded verification |
| 3 | 5–6 | Mon 9 Nov → Fri 20 Nov | Anomaly detection, dispute letters, full pipeline |
| 4 | 7–8 | Mon 23 Nov → Fri 4 Dec | Hardening, evaluation, deployment, demo and report |
| - | - | 7 → 14 Dec | Report assembly (P-3 due Mon 14 Dec) |
| - | - | 15 Dec rehearsal, P-4 due Wed 16 Dec | Final demo and viva |

**Instructor timeline for P-2:** 5–9 Oct was backlog preparation (Product Backlog, Sprint 1 Backlog, DoR, DoD, points and acceptance criteria on every story, role rotation). 12–23 Oct is Sprint 1 execution. Submission is 25 Oct, so Sat 24 and Sun 25 are for assembling screenshots and the write-up, not for coding.

**Key dates:** burndown #1 around Mon 19 Oct, burndown #2 on Fri 23 Oct. Role rotation on 26 Oct, 9 Nov and 23 Nov.

---

## 1. Product at a glance

**One line:** upload a utility bill, check it against the official NEPRA/OGRA tariff, cite the exact rule if something is off, and draft a dispute letter the user reviews and sends themselves.

**Pipeline (four agents):** Extraction → Tariff-Grounding (RAG) → Anomaly → Dispute-Letter.

**Scope**

| Utility | Coverage | Why |
|---|---|---|
| Electricity | All NEPRA-regulated DISCOs, rolled out in phases (start with K-Electric plus 2 more, expand in Sprint 3) | One regulator, same slab logic, different rates |
| Gas | SNGPL and SSGC (Sprint 3) | Two providers, both OGRA-regulated |
| Water | Single pilot city, stretch goal in Sprint 4 | No unified regulator (WASA, KWSB and others are separate) |

**Out of scope (say this in the report):** auto-submitting complaints to utility or regulator portals. The user always reviews and sends the letter.

---

## 2. Engineering decisions to lock in Sprint 1

These are the decisions you will be asked to defend in the viva. Write each one into `docs/decisions.md` with a date and a one-paragraph rationale.

1. **Arithmetic lives in code, not in the LLM.** A deterministic Python engine recalculates the bill from structured tariff data. The LLM extracts, explains and writes. It never does the maths. This is your main hallucination defence.
2. **Tariffs are stored twice.** Structured JSON (slabs, rates, taxes) feeds the engine. The same source documents are chunked into a vector store so agents can retrieve and quote the clause text.
3. **Citation rule.** A finding with no verifiable source clause is dropped before the user sees it. A final verification step checks that every cited clause exists in the corpus.
4. **Extraction uses Gemini's multimodal input** with a Pydantic schema, plus a user-correctable form. The user can fix a misread field before the pipeline continues.
5. **Wording of findings:** "this charge differs from the published tariff clause X", never "the utility is cheating you". Add a not-legal-advice disclaimer to every letter.
6. **Model names live in one config file** (you already hit one deprecation). Never hardcode them in agent code.
7. **Prompts are versioned files in the repo** (`prompts/<agent>/vN.md`) with a changelog entry that references a Jira ticket. This is your prompt-versioning traceability.
8. **Privacy by default:** do not retain bill images after extraction unless the user opts in, provide a "delete my data" action, and use redacted samples in demos and the report.
9. **Free-tier limits:** cache repeated calls, keep a rate-limit guard, use the fast model by default and a stronger model only where it measurably helps.

---

## 3. Repository and process conventions

```
BillWakeel/
├── backend/            # FastAPI app: api/, agents/, services/, models/
├── frontend/           # React (Vite) app
├── prompts/            # extraction/, grounding/, anomaly/, letter/  (versioned)
├── data/
│   ├── tariffs/        # raw/ (source PDFs and pages) and structured/ (JSON)
│   └── samples/        # anonymised bills + labels (golden set)
├── tests/              # unit/, integration/, prompt/, eval/
├── docs/               # architecture, decisions, sprint reviews, report drafts
└── README.md
```

- **Branches:** `main` (always demoable), `dev` (integration), `feature/SCRUM-<n>-<short-name>`.
- **Commits:** every commit uses the smart-commit format on one line: `SCRUM-14 #comment add extraction schema`. The Git email must match the Jira email. See `CONTRIBUTING.md`.
- **Pull requests:** at least one reviewer who did not write the code. Jira key in the PR title. Feature PRs into `dev` use "Create a merge commit" and the feature branch is deleted afterwards; `dev` to `main` at sprint end uses Squash and merge through GitHub, then a release tag.
- **Jira columns:** To Do, In Progress, In Review, Done (matches your board).
- **Definition of Done (use for every story):**
  - Code merged to `dev` through a reviewed PR with the Jira key
  - Unit tests written and passing
  - If an agent or prompt changed: prompt version bumped, changelog updated, prompt test run
  - No secrets committed (`.env` is gitignored)
  - Acceptance criteria demonstrated in the sprint review
  - Every commit in the smart-commit format; `docs/decisions.md` updated if an architecture decision was made
  - Jira ticket moved to Done with story points recorded

### Ceremonies (every sprint)

| Day | Ceremony | Output |
|---|---|---|
| 1 | Sprint planning | Sprint goal, committed stories with points and owners |
| Daily | 10-minute standup (async in chat is fine) | Blockers surfaced |
| 7 | Mid-sprint check | **Burndown screenshot #1**, scope adjustments |
| 13 | Sprint review and demo | Working increment shown, **burndown screenshot #2** |
| 14 | Retrospective and role rotation | 3 keep / 3 change items, velocity logged |

Record committed versus completed story points every sprint. That is your velocity chart.

### Scrum role rotation (required after every sprint)

| Sprint | Scrum Master | Product Owner | Developers |
|---|---|---|---|
| 1 | Ayesha Zafar | Muhammad Abdullah Swati | Rehan, Baig |
| 2 | Rehan | Baig | Ayesha, Swati |
| 3 | Swati | Ayesha | Rehan, Baig |
| 4 | Baig | Rehan | Ayesha, Swati |

Everyone is Scrum Master once, Product Owner once, and Developer twice. **The SM and PO still write code every sprint.** Individual commits are graded, so give them well-scoped stories (tests, tariff data entry, docs, small UI pieces).

### Work streams (assign owners at each planning session)

- **AI:** prompts, LangChain chains, Gemini calls, agent logic
- **BE:** FastAPI, database, tariff engine, data pipeline
- **FE:** React UI
- **QA/Docs:** tests, evaluation set, report drafts, Jira hygiene

With mixed skill levels, pair a stronger and a weaker teammate on each stream and rotate the pairing. Before each sprint review, run a 15-minute swap session where each person explains one component they did not build. That is direct preparation for the individual viva.

---

## 4. Sprint 1 (Weeks 1–2): Foundations and the first vertical slice

**Sprint goal:** a user can upload a K-Electric bill in the browser and see the extracted fields (editable), produced by a working Extraction Agent v0.

**Measurable targets**
- Extraction Agent v0 returns schema-valid JSON for at least 8 of 10 collected K-Electric samples
- Field-level accuracy recorded for units consumed, billing period and amount due
- Jira and GitHub linked with smart commits visible
- Burndown snapshots taken at mid-sprint and sprint end

**Candidate stories (30 points)**

| # | Story | Pts | Stream |
|---|---|---|---|
| 1.1 | Repo scaffold, folder structure, README, .gitignore, `.env.example` | 2 | QA/Docs |
| 1.2 | FastAPI skeleton: config, health endpoint, CORS | 3 | BE |
| 1.3 | React (Vite) skeleton with react-router and an upload page shell | 3 | FE |
| 1.4 | Gemini service layer in the backend, model name from config | 2 | AI |
| 1.5 | Bill upload endpoint with file type and size validation | 3 | BE |
| 1.6 | Extraction Agent v0: K-Electric bill to Pydantic-validated JSON | 8 | AI |
| 1.7 | UI shows extracted fields in an editable form | 3 | FE |
| 1.8 | Collect and anonymise at least 10 sample bills, label the true values | 3 | QA/Docs |
| 1.9 | Prompt versioning convention plus `prompts/extraction/v1.md` and changelog | 1 | AI |
| 1.10 | Unit tests: schema validation and upload endpoint | 2 | QA/Docs |

**Sprint 1 owners (30 pts).** Everyone commits code, including the Scrum Master and Product Owner.

| Person | Sprint 1 role | Stories | Pts |
|---|---|---|---|
| Rehan | Developer (AI lead) | 1.4, 1.6, 1.9 | 11 |
| Baig | Developer (backend) | 1.1, 1.2, 1.5 | 8 |
| Ayesha | Scrum Master | 1.3, 1.7 (plus Jira hygiene, ceremonies) | 6 |
| Swati | Product Owner | 1.8, 1.10 (plus backlog ownership, DoR/DoD, acceptance) | 5 |

Write each story in "As a ___, I want ___, so that ___" form with acceptance criteria and the shared Definition of Done. This is the user-stories item in the Sprint 1 rubric.

**Weekly tasks**

*Week 1*
- [ ] Sprint planning: create the stories above in Jira with points, assignees and acceptance criteria
- [ ] Verify the GitHub-for-Jira link by making one commit with a Jira key and checking it appears on the ticket
- [ ] Scaffold the repo and agree branch and PR rules (1.1)
- [ ] Stand up FastAPI and React skeletons and prove they talk to each other (1.2, 1.3)
- [ ] Start collecting sample bills right away. This is the longest-lead item, so ask family and friends and strip personal data (1.8)
- [ ] Move the Gemini call from `test_connection.py` into a reusable service (1.4)
- [ ] Write `docs/decisions.md` with the Section 2 decisions
- [ ] Mid-sprint burndown screenshot

*Week 2*
- [ ] Build the upload endpoint (1.5)
- [ ] Build Extraction Agent v0 and iterate the prompt against the sample set, bumping the prompt version each time (1.6, 1.9)
- [ ] Wire the UI to display and edit the extracted fields (1.7)
- [ ] Write unit tests (1.10)
- [ ] Measure and record extraction accuracy on the labelled samples
- [ ] Sprint review demo, burndown screenshot, retrospective, role rotation, log velocity
- [ ] Start the report: draft *Project Overview* and *Requirements* sections

**Exit criteria:** upload to editable extracted fields works end to end on `dev`, all Sprint 1 rubric artifacts are captured (stories, linked commits, burndowns, code increment).

**Risks:** bill photo quality varies, and sample collection can stall. Mitigation: start collecting on day 1 and support PDF as well as photos.

---

## 5. Sprint 2 (Weeks 3–4): Tariff knowledge base and grounded verification

**Sprint goal:** the system recalculates a bill from official tariff data and reports discrepancies, each with a cited clause.

**Measurable targets**
- Tariff corpus covers K-Electric plus 2 more DISCOs, with a source URL and retrieval date for every document
- Recalculation engine reproduces the billed total within a documented tolerance on clean samples. Pick the exact threshold after you see real bills, since FPA and tax components can need special handling
- Zero uncited findings on the seeded-error set

**Candidate stories (34 points)**

| # | Story | Pts | Stream |
|---|---|---|---|
| 2.1 | Collect raw tariff sources (NEPRA notifications, DISCO tariff pages) with source metadata | 3 | BE |
| 2.2 | Structured tariff JSON schema, populated for 3 DISCOs | 5 | BE |
| 2.3 | Deterministic bill recalculation engine with unit tests | 5 | BE |
| 2.4 | Vector store, chunking and clause retrieval over tariff documents | 5 | AI |
| 2.5 | Tariff-Grounding Agent v1: compare bill to engine output, emit findings with citations | 8 | AI |
| 2.6 | Extend extraction to a 2nd bill layout | 3 | AI |
| 2.7 | Database models (SQLAlchemy plus SQLite) for bills and findings | 3 | BE |
| 2.8 | UI: findings view showing the cited clause | 2 | FE |

**Weekly tasks**

*Week 3*
- [ ] Sprint planning, assign owners, update the Jira board
- [ ] Gather the official tariff documents and record source URL and date (2.1). These are PDFs and web pages, so expect parsing work
- [ ] Design the tariff JSON schema (slabs, per-unit rates, taxes, surcharges) and fill it for K-Electric first (2.2)
- [ ] Build the recalculation engine against the K-Electric structure (2.3)
- [ ] Set up the database models (2.7)
- [ ] Create the **seeded-error test set**: take real or anonymised bills and edit them to introduce known errors (wrong slab, inflated units, duplicated tax). Label these as synthetic in your report
- [ ] Mid-sprint burndown screenshot

*Week 4*
- [ ] Add 2 more DISCOs to the tariff JSON (2.2)
- [ ] Chunk and embed the tariff documents, then test retrieval quality on real questions (2.4)
- [ ] Build Grounding Agent v1 and enforce the citation rule (2.5)
- [ ] Add support for a 2nd bill layout (2.6)
- [ ] Build the findings UI (2.8)
- [ ] Run the first evaluation pass on the golden and seeded sets and save the numbers
- [ ] Sprint review demo, burndown screenshot, retrospective, role rotation, velocity logged
- [ ] Report: draft *Architecture and Design* (agent diagram, data flow, tariff storage design)

**Exit criteria:** an uploaded bill from a supported DISCO produces findings, each linked to a retrievable clause. Seeded errors are caught.

**Risks:** tariff documents are messy and change over time. Mitigation: always record the effective date, and keep the structured JSON as the single source of truth for maths.

---

## 6. Sprint 3 (Weeks 5–6): Anomaly detection, dispute letters, full pipeline

**Sprint goal:** a user runs the whole flow, from upload to a ready-to-review dispute letter, for electricity and gas, with history-aware anomaly flags.

**Measurable targets**
- End-to-end run completes without manual intervention on at least 90% of the golden set
- Every generated letter contains the disclaimer and at least one verified citation
- Electricity covers all DISCOs you can source tariffs for. Gas covers both SNGPL and SSGC

**Candidate stories (34 points)**

| # | Story | Pts | Stream |
|---|---|---|---|
| 3.1 | Gas support: SNGPL and SSGC tariff JSON, extraction layout, engine support | 5 | BE/AI |
| 3.2 | Remaining DISCOs added as tariff config | 3 | BE |
| 3.3 | Anomaly Agent v1: rolling baseline over bill history, spike and estimated-reading flags, LLM-written explanation | 5 | AI |
| 3.4 | Dispute-Letter Agent v1: letter bound to verified findings only, includes disclaimer | 8 | AI |
| 3.5 | Tone picker: Polite, Firm, "No More Mr. Nice Guy" (same facts, different tone) | 2 | AI/FE |
| 3.6 | Complaint-destination routing table (per DISCO and gas company), with copy, PDF download and mailto actions | 3 | BE/FE |
| 3.7 | Pipeline orchestrator tying the four agents together with retries and clear error states | 5 | AI/BE |
| 3.8 | Lightweight session or accounts so bill history persists, plus a history list view | 3 | BE/FE |

**Weekly tasks**

*Week 5*
- [ ] Sprint planning and owner assignment
- [ ] Build the orchestrator (3.7) first, since every other story plugs into it
- [ ] Gas tariff JSON, extraction and engine support (3.1)
- [ ] Build Anomaly Agent v1 using simple statistics for detection and the LLM only to explain (3.3)
- [ ] Start the Dispute-Letter Agent: the letter may only reference findings that passed citation verification (3.4)
- [ ] Add history persistence (3.8)
- [ ] Mid-sprint burndown screenshot

*Week 6*
- [ ] Finish the letter agent, then add the tone picker (3.4, 3.5)
- [ ] Complaint routing table with copy, PDF and mailto (3.6). Verify each contact against the utility's official page before you hard-code it
- [ ] Add remaining DISCOs through config (3.2)
- [ ] Run the full golden-set evaluation and record results
- [ ] Prompt tests for all four agents (versioned prompts, expected-output checks)
- [ ] Sprint review demo, burndown screenshot, retrospective, role rotation, velocity logged
- [ ] Report: draft *Implementation* and start *Testing*

**Exit criteria:** the full pipeline works on `dev` for electricity and gas, and a reviewer who was not on the team can complete one run unaided.

**Risks:** letter hallucination (mitigated by the citation-bound design) and integration slippage (mitigated by building the orchestrator first).

---

## 7. Sprint 4 (Weeks 7–8): Hardening, evaluation, deployment, demo and report

**Sprint goal:** a stable, deployed, measured product plus a complete report and a rehearsed demo.

**Measurable targets**
- Evaluation report with precision and recall for discrepancy detection, extraction field accuracy, citation validity rate, and false-accusation rate
- Zero uncited findings in the final evaluation run
- Deployed URL, plus a recorded backup demo

**Candidate stories (31 points core, plus 5 stretch)**

| # | Story | Pts | Stream |
|---|---|---|---|
| 4.1 | Evaluation harness that runs the golden and seeded sets and outputs metrics | 8 | QA |
| 4.2 | Guardrails: refuse to flag when evidence is thin, final citation verification step | 5 | AI |
| 4.3 | Prompt regression tests and final prompt versions | 3 | AI/QA |
| 4.4 | UI polish: history chart, responsive layout, empty and error states | 5 | FE |
| 4.5 | Deployment (frontend and backend), secrets handling, caching and rate-limit guard for the free tier | 5 | BE |
| 4.6 | Privacy hardening: no image retention by default, delete-my-data action, redacted demo mode | 3 | BE/FE |
| 4.7 | Demo script, seeded demo account, backup recording | 2 | All |
| 4.8 | *Stretch:* water pilot for one city | 5 | BE/AI |

**Weekly tasks**

*Week 7*
- [ ] Sprint planning. Freeze new features, so only hardening and polish from here
- [ ] Build the evaluation harness and run it (4.1)
- [ ] Fix the failure cases it exposes. Each fix should have its own prompt version and Jira ticket (4.2, 4.3)
- [ ] Deployment (4.5) and privacy hardening (4.6)
- [ ] Mid-sprint burndown screenshot
- [ ] Report: write *Testing* with real numbers, including hallucination and edge-case evidence (bad photo, missing fields, unsupported DISCO, conflicting data)

*Week 8*
- [ ] UI polish (4.4)
- [ ] Water pilot only if everything above is green (4.8)
- [ ] Rehearse the demo end to end at least twice, on the deployed version (4.7)
- [ ] Final report assembly: *Project Management* (Sprints 1–4 documentation, Jira and GitHub strategy, burndown and velocity charts), *Conclusion, Lessons Learned, Future Work, References*
- [ ] Viva preparation: each person explains the full architecture, and their own commits and design choices
- [ ] Final sprint review, retrospective and velocity log

**Exit criteria:** deployed product, final report, demo rehearsed, every team member can explain every agent.

---

## 8. Testing and evaluation plan

**Golden set:** at least 15 anonymised real bills with hand-labelled true values, plus the synthetic seeded-error bills (clearly labelled as synthetic).

| Test type | What it checks | Tool or approach |
|---|---|---|
| Unit | Schema validation, tariff engine maths, routing table | pytest |
| Integration | Upload to findings to letter through the API | pytest with FastAPI test client |
| Prompt tests | Each agent prompt version against fixed inputs, checking structure and key facts | Versioned fixtures in `tests/prompt/` |
| Hallucination | Invented clauses, invented amounts, unsupported accusations | Citation verification step plus adversarial inputs |
| Edge cases | Blurry photo, cropped bill, unknown DISCO, zero or negative units, conflicting history | Dedicated fixtures |
| Evaluation | Precision and recall of discrepancy detection, extraction accuracy, citation validity, false-accusation rate | `tests/eval/` harness, one results table per run |

Keep every evaluation run's output in `docs/eval/` with the date and the prompt versions used. These tables are your testing evidence for the report.

---

## 9. Traceability (rubric requires requirements ↔ agents/prompts ↔ tests)

Maintain one table in `docs/traceability.md` and add a row per requirement:

| Requirement | Jira | Agent and prompt version | Test |
|---|---|---|---|
| FR-3: findings must cite a source clause | SCRUM-xx | Grounding v3 | `tests/eval/test_citations.py` |

---

## 10. Report writing schedule (P-3, 30%)

Do not leave the report for the last week. Write each section while the work is fresh.

| Report section | Draft during |
|---|---|
| Project Overview, Requirements (functional, non-functional, AI constraints, backlog snapshots) | Sprint 1 |
| Architecture and Design (diagrams, agent tool-use diagram, wireframes), Implementation | Sprint 2–3 |
| Testing (unit, integration, prompt, hallucination evidence) | Sprint 3–4 |
| Project Management (Sprints 1–4, Jira, GitHub strategy, burndown, velocity) | Sprint 4, using artifacts saved each sprint |
| Conclusion, Lessons Learned, Future Work, References | Sprint 4 |

**Save every sprint:** two burndown screenshots, the sprint backlog with points, the velocity entry, the retrospective notes, and one screenshot of the working increment.

---

## 11. Demo and viva preparation (P-4, 35%)

- **Demo flow (about 3 minutes):** upload a bill, correct one field, see findings with cited clauses, view the anomaly flag, pick a tone, copy or download the letter.
- Keep a **seeded-error demo bill** that reliably triggers a finding, and a **clean bill** that correctly triggers none. Showing both proves the system does not just accuse everything.
- Keep a backup screen recording in case the network or the free-tier quota fails during the demo.
- Likely viva questions to prepare for: why the maths lives outside the LLM, why RAG plus structured JSON, why water is a pilot only, why the letter is not auto-submitted, how prompt versions map to tests, what each person personally committed.
- If you also enter competitions, the evaluation table and the clean-versus-seeded demo are the strongest material you will have.

---

## 12. Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Not enough sample bills | High | High | Start collecting in week 1, allow PDFs, build the seeded-error set |
| Bill layouts differ across DISCOs | High | Medium | Support 2–3 layouts well, manual-correction form for the rest, state the limit in the report |
| Tariff documents messy or changing | Medium | High | Record effective dates, structured JSON as the maths source, review it in pairs |
| LLM invents a claim | Medium | High | Deterministic maths, citation verification, drop uncited findings |
| Gemini model renamed or retired | Medium | Medium | Model name in config, one place to change |
| Free-tier rate limits during demo | Medium | High | Caching, rate-limit guard, backup recording |
| Uneven contribution across the team | Medium | High | Everyone owns stories every sprint, role rotation, swap sessions, check commit history at each retro |
| Sprint scope too ambitious | Medium | Medium | Commit from measured velocity, keep a stretch column that is safe to drop |

---

## 13. Rubric checklist

| Component | What to have ready |
|---|---|
| **P-1 Sprint 0 (5%)** | Done: group and roles, title and description, Jira and GitHub links, Gemini connection evidence |
| **P-2 Sprint 1 (30%)** | User stories with points, acceptance criteria and DoD; commits with Jira keys visible on tickets; story allocation plus burndown screenshots; working upload-to-extraction increment |
| **P-3 Report (30%)** | All mandatory sections, agent diagrams, evaluation tables, hallucination evidence, Sprint 1–4 documentation |
| **P-4 Demo and viva (35%)** | Stable deployed demo, backup recording, every member able to explain the architecture and their own commits |
| **Mandatory rules** | Four strict two-week sprints, role rotation each sprint, individual commits visible, Jira used for all tracking, burndown and velocity recorded, AI architecture decisions documented |
