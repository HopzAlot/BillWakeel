# BillWakeel: Team Member Brief (Baig, Developer / Backend)

*Sprint 1: Mon 12 Oct to Fri 23 Oct 2026. Read together with `CONTRIBUTING.md` and `BillWakeel_DoR_DoD_Roles.md`.*

## How to use this file

This file is a complete brief for one team member. It is written so that you (or an LLM assistant you give it to) can understand the whole project and start work without asking anyone.

**If you are using an LLM (ChatGPT, Claude, Gemini, Copilot, etc.):** paste this file plus `CONTRIBUTING.md` and `BillWakeel_DoR_DoD_Roles.md` into the conversation, then say: *"Read all three documents. I am the person described in Part B. Help me complete my first story step by step, following the repo rules."* Re-paste the files in each new chat. Always run and review the code the LLM gives you. You must be able to explain every line in the viva.

**Rules any assistant must follow when helping with this project:**
1. Never put API keys or real personal bill data in code, commits or chats. Use `.env`; use anonymised samples only.
2. Never let the LLM do bill arithmetic. Money maths is done in plain Python code (Sprint 2).
3. Never invent tariff rates, clauses or contact details. Real data comes from official NEPRA/OGRA/utility documents.
4. Follow the branch, commit and PR rules in `CONTRIBUTING.md`. Every commit looks like: `SCRUM-10 #comment short description`.
5. Keep the shared contract (Part A, section 8) unchanged unless the whole team agrees. If you must change it, tell the group and the Developer who owns that piece first.
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

An "agent" here means a module that uses the Gemini model for a defined job, with strict inputs and outputs. The four run in order as a pipeline.

| # | Agent | Input | Output | Sprint |
|---|---|---|---|---|
| 1 | **Extraction Agent** | Bill image or PDF | Structured data (a `BillExtraction` object): units, billing period, each charge line, taxes, total | **1** |
| 2 | **Tariff-Grounding Agent** | Extracted data + official tariff data | Findings: "this charge differs from the tariff by Rs X", each with a cited clause | 2 |
| 3 | **Anomaly Agent** | Extracted data + the user's bill history | Flags: spikes, estimated readings, unusual jumps | 3 |
| 4 | **Dispute-Letter Agent** | Verified findings only | A formal dispute letter in the chosen tone, with a disclaimer | 3 |

**Sprint 1 builds only agent 1 plus the web plumbing around it**: upload a bill in the browser, see the extracted fields in an editable form.

## 4. Non-negotiable design rules

These are our main defences against AI errors, and they are what we will defend in the viva and the report.

1. **Maths lives in code, not the LLM.** The LLM reads, retrieves, explains and writes. A deterministic Python engine recalculates the bill. LLMs make arithmetic mistakes; code does not.
2. **Every finding must cite a real clause.** A finding with no verifiable source clause is dropped before the user sees it.
3. **Non-accusatory wording.** The tool says "this charge differs from the published tariff clause X", never "the utility is cheating you". Every letter carries a "not legal advice" disclaimer.
4. **Human in the loop.** The user reviews the extracted data and the final letter. There is no auto-submit; no public API exists for that, and a person should own a dispute.
5. **Model names live in one config setting.** Models get renamed and retired (we already hit one deprecation). Never hardcode a model name inside agent code.
6. **Prompts are versioned files**: `prompts/<agent>/v1.md`, `v2.md`, ... A released version is never edited. Each change adds a line to `prompts/CHANGELOG.md` with the Jira key. This gives us traceability from requirement to prompt to test.
7. **Privacy by default.** Do not keep bill images after extraction unless the user opts in. Use anonymised samples in the repo, demos and report.
8. **Free-tier discipline.** We use the free Gemini tier: cache repeated calls, add a rate-limit guard, avoid calling the model in loops.

## 5. Scope

| Utility | Coverage | Notes |
|---|---|---|
| Electricity | All NEPRA-regulated distribution companies, rolled out in phases. Start with K-Electric (Karachi) plus 2 more; expand in Sprint 3 | One regulator, similar slab logic, different rates |
| Gas | SNGPL and SSGC (Sprint 3) | Regulated by OGRA |
| Water | One pilot city only, a stretch goal in Sprint 4 | No single national regulator; each city authority differs |

**Out of scope (we say this openly in the report):** auto-submitting complaints, legal advice, payment, and any claim that a utility acted in bad faith.

## 6. Glossary of Pakistani bill terms

Use this to read a sample bill. Exact rates and rules come from official tariff documents we collect in Sprint 2; do not rely on anything remembered from elsewhere.

- **NEPRA**: National Electric Power Regulatory Authority. Approves electricity tariffs.
- **OGRA**: Oil and Gas Regulatory Authority. Regulates gas prices.
- **DISCO**: electricity distribution company (LESCO, FESCO, GEPCO, IESCO, MEPCO, PESCO, HESCO, SEPCO, QESCO, TESCO). **K-Electric** serves Karachi and is a separate private utility.
- **SNGPL / SSGC**: Sui Northern / Sui Southern Gas Company. The two gas utilities.
- **Slab**: a band of units with its own per-unit rate. Using more units can move you into a more expensive slab.
- **Protected / unprotected consumer**: a category that affects which rates apply, based on consumption history. Exact rules come from the tariff documents.
- **Tariff category**: the code on the bill (for example residential, commercial) that decides which rate table applies.
- **Sanctioned load**: the connection capacity (kW) the consumer is registered for.
- **FPA / FCA (fuel price / fuel charge adjustment)**: a monthly adjustment for fuel cost changes.
- **QTA (quarterly tariff adjustment)**: a periodic adjustment line.
- **GST, electricity duty, PTV fee, further tax, surcharges**: taxes and fees added to the bill. Names and amounts vary by utility and period, so we extract the line items by name rather than assuming a fixed list.
- **Arrears**: unpaid amounts carried over from earlier bills.
- **Estimated reading**: the utility billed without reading the meter. This is a common source of complaints.
- **Payable by due date / after due date**: the total before and after the late-payment surcharge.

## 7. Tech stack and repository layout

**Stack:** FastAPI (Python backend) + React with Vite (frontend) + LangChain with `langchain-google-genai` + Google Gemini (current working model: `gemini-3.8-flash`, set in config) + Pydantic for data models + SQLite/SQLAlchemy (from Sprint 2) + pytest.

```
BillWakeel/
├── backend/
│   ├── main.py            # FastAPI app creation, CORS, router registration
│   ├── config.py          # Settings read from environment (.env)
│   ├── api/               # route modules, e.g. bills.py
│   ├── agents/            # extraction.py, later grounding.py, anomaly.py, letter.py
│   ├── services/          # gemini.py (model client), storage helpers
│   ├── models/            # Pydantic schemas, e.g. bill.py
│   └── requirements.txt
├── frontend/              # React (Vite): src/pages, src/components, src/api
├── prompts/               # extraction/v1.md ... plus CHANGELOG.md
├── data/
│   ├── tariffs/           # raw/ and structured/ (Sprint 2)
│   ├── samples/           # anonymised bills + ground-truth JSON
│   └── uploads/           # runtime uploads (gitignored)
├── tests/                 # unit/, integration/, prompt/, eval/
├── docs/                  # roadmap, decisions, DoR/DoD, sprint reviews
├── CONTRIBUTING.md
└── README.md
```

Repo: https://github.com/HopzAlot/BillWakeel. Jira key: `SCRUM`. Board: https://software-ka-project.atlassian.net/jira/software/projects/SCRUM/boards/1

## 8. The shared contract (Sprint 1)

Everyone codes against this contract so the pieces fit together. **Rehan owns the schema; Baig owns the API; Ayesha consumes both.** Changes need group agreement.

### 8.1 The `BillExtraction` data shape (JSON)

```json
{
  "utility": "electricity",
  "provider": "K-Electric",
  "billing_month": "2026-09",
  "issue_date": "2026-09-10",
  "due_date": "2026-09-22",
  "tariff_category": "A-1",
  "sanctioned_load_kw": 3.0,
  "meter_reading_previous": 12000,
  "meter_reading_current": 12310,
  "units_consumed": 310,
  "charges": [
    {"name": "Energy charges", "amount_pkr": 6200.0},
    {"name": "Fuel charge adjustment", "amount_pkr": 410.5},
    {"name": "GST", "amount_pkr": 1150.0}
  ],
  "arrears_pkr": 0,
  "total_payable_by_due_date": 8000.0,
  "total_payable_after_due_date": 8400.0,
  "low_confidence_fields": ["tariff_category"],
  "notes": null
}
```

Rules: every field except `charges` and `low_confidence_fields` may be `null` when the bill does not show it or the model is unsure. Dates are ISO `YYYY-MM-DD`; `billing_month` is `YYYY-MM`. Money is in PKR as a number. `utility` is one of `electricity`, `gas`, `water`, `unknown`. The numbers above are illustrative, not real tariffs.

### 8.2 The Sprint 1 API

| Method and path | Purpose | Success | Errors |
|---|---|---|---|
| `GET /health` | Liveness check | `200 {"status": "ok"}` | none |
| `POST /bills` | Upload a bill (multipart form field `file`) | `201 {"bill_id", "filename", "content_type", "size_bytes"}` | `415` unsupported type, `413` too large, `400` empty file |
| `POST /bills/{bill_id}/extract` | Run the Extraction Agent | `200 {"bill_id", "extraction": <BillExtraction>, "prompt_version", "model"}` | `404` unknown bill, `502` model failed, `422` unreadable output |
| `PUT /bills/{bill_id}/extraction` | Save the user's corrected values | `200 <BillExtraction>` | `404`, `422` if the body fails validation |

Accepted file types: `image/jpeg`, `image/png`, `application/pdf`. Max size from `MAX_UPLOAD_MB` (default 10). All errors use the body `{"detail": "human readable message"}`. CORS allows the Vite dev origin `http://localhost:5173` (from `FRONTEND_ORIGIN`). Uploaded files are stored at `data/uploads/<bill_id>.<ext>` (gitignored); metadata and extractions sit in an in-memory store for now (a database replaces it in Sprint 2).

### 8.3 The extraction function (Rehan to Baig)

```python
# backend/agents/extraction.py
def extract_bill(file_path: str, content_type: str) -> "ExtractionResult": ...
# ExtractionResult has: extraction (BillExtraction), prompt_version (str), model (str)
```

Baig's `/extract` endpoint calls this function. Until Rehan merges the real one, Baig uses a stub that returns the example JSON from 8.1 so the frontend can be built against it.

## 9. Sprint 1 at a glance

**Sprint goal:** a user can upload a K-Electric bill in the browser and see the extracted fields in an editable form, produced by a working Extraction Agent v0.

**Dates:** Monday 12 Oct to Friday 23 Oct 2026. The P-2 assignment is submitted by Sunday 25 Oct. Burndown screenshot 1 on Monday 19 Oct, burndown screenshot 2 on Friday 23 Oct. Sprint review, demo and retrospective on Friday 23 Oct. Roles rotate on Monday 26 Oct.

**Measurable targets:** Extraction Agent v0 returns schema-valid JSON for at least 8 of 10 sample bills; field accuracy recorded for units consumed, billing period and amount due; Jira and GitHub linked with commits visible on tickets; all stories meet the Definition of Done.

| Jira | Story | Pts | Owner | Role this sprint |
|---|---|---|---|---|
| SCRUM-5 | Repo scaffold and README | 2 | Baig | Developer |
| SCRUM-6 | FastAPI skeleton, health endpoint, CORS, config | 3 | Baig | Developer |
| SCRUM-7 | React (Vite) skeleton with Upload page shell | 3 | Ayesha | Scrum Master |
| SCRUM-8 | Gemini service layer, model name in config | 2 | Rehan | Developer |
| SCRUM-9 | Bill upload endpoint with validation (and the other Sprint 1 endpoints) | 3 | Baig | Developer |
| SCRUM-10 | Extraction Agent v0 | 8 | Rehan | Developer |
| SCRUM-11 | UI shows extracted fields in an editable form | 3 | Ayesha | Scrum Master |
| SCRUM-12 | Collect and anonymise sample bills | 3 | Swati | Product Owner |
| SCRUM-13 | Prompt versioning convention and changelog | 1 | Rehan | Developer |
| SCRUM-14 | Unit tests for schema validation and upload endpoint | 2 | Swati | Product Owner |

**Team:**

| Member | Sprint 1 role |
|---|---|
| Muhammad Rehan Saqib | Developer (AI lead) |
| Muhammad Abdullah Baig | Developer (backend) |
| Ayesha Zafar | Scrum Master (also frontend stories) |
| Muhammad Abdullah Swati (GC) | Product Owner (also data and tests) |

Roles rotate every sprint (Sprint 2: Rehan SM, Baig PO, Ayesha and Swati Developers; Sprint 3: Swati SM, Ayesha PO, Rehan and Baig Developers; Sprint 4: Baig SM, Rehan PO, Ayesha and Swati Developers). Scrum Master and Product Owner still write code and make their own commits every sprint, because individual commits are graded.

## 10. Team-wide Sprint 1 timeline

| Day | What should happen |
|---|---|
| Tue 13 Oct | Rehan commits the starter docs to `main`, creates `dev` and adds the branch ruleset, then tells the group. Baig then does SCRUM-5 (scaffold) on a feature branch and merges it into `dev` by PR. Rehan posts the final schema in the group chat. Swati starts collecting bills. Ayesha confirms Jira and GitHub linking works. |
| Wed 14 Oct | Everyone branches from `dev` once SCRUM-5 is merged. SCRUM-6, 7, 8 in progress. First 3 to 5 anonymised sample bills with labels handed to Rehan. |
| Thu 15 Oct | SCRUM-6 (API skeleton + config) and SCRUM-8 (Gemini service) merged to `dev`. |
| Fri 16 Oct | SCRUM-7 (React skeleton) merged. Sample bills reach 10. SCRUM-13 (prompt versioning) merged. |
| Mon 19 Oct | **Mid-sprint check and burndown screenshot 1.** SCRUM-9 (upload) under way; SCRUM-10 first working version. |
| Tue 20 Oct | SCRUM-9 merged. Extraction Agent v0 accuracy measured on samples. |
| Wed 21 Oct | SCRUM-11 (editable form) wired to the real API. SCRUM-14 tests running. |
| Thu 22 Oct | Integration day: full flow upload to editable form on `dev`. Bug fixes. Demo rehearsal. |
| Fri 23 Oct | **Sprint review and demo. Burndown screenshot 2. Retrospective. Velocity logged. `dev` merged to `main` and tagged `sprint-1`.** |
| Sat 24 to Sun 25 Oct | Assemble and submit the P-2 package (no new coding). |

If a dependency slips, say so in the group chat the same day and re-plan; do not stay silent.

## 11. Communication and escalation

- Daily 10-minute standup (chat is fine): what I did, what I will do, what blocks me.
- Blocked more than half a day? Post in the group chat and tag the person who owns the dependency. The Scrum Master tracks blockers.
- Anything that changes the shared contract (8.1, 8.2, 8.3) goes to the whole group before code changes.
- PRs: ask a teammate who did not write the code to review. Reviews should happen within a day.

---

# PART B: YOUR BRIEF, MUHAMMAD ABDULLAH BAIG

**Sprint 1 role: Developer (backend). Stories: SCRUM-5, SCRUM-6, SCRUM-9 (8 points).**

You own the backbone: the repository structure, the FastAPI application, configuration, and the upload and bill endpoints. Everyone else's work plugs into what you build, so SCRUM-5 and SCRUM-6 are urgent in the first two days.

## B1. Your stories in order

### SCRUM-5: Repo scaffold and README (2 pts), do this TODAY (Tue 13 Oct)
**Goal:** a clean repository structure everyone can clone and branch from.

**Setup done by Rehan first.** As the repo owner, Rehan commits the starter files (`README.md`, `CONTRIBUTING.md`, `.gitignore`, `.env.example`, `docs/`, `prompts/CHANGELOG.md`) directly to `main`, creates the `dev` branch, and turns on the branch ruleset. He will message the group when that is done. Wait for that message before you start. From then on nobody pushes directly to `main` or `dev`.

1. Make sure your Git name and email match your Jira and GitHub accounts (see the bold note in `CONTRIBUTING.md`). Clone `https://github.com/HopzAlot/BillWakeel` (or `git pull` if you already have it).
2. Create your branch from `dev`:
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b feature/SCRUM-5-repo-scaffold
   ```
3. Add the folder structure from Part A section 7. Git does not store empty folders, so add a `.gitkeep` file inside each empty folder (`backend/agents`, `backend/api`, `backend/services`, `backend/models`, `frontend`, `data/tariffs`, `data/samples`, `tests/unit`, `tests/integration`, `tests/prompt`, `tests/eval`). The `docs/` and `prompts/` folders already exist from Rehan's commit.
4. Check that the README's description of the layout matches what you created, and fix the README if it does not.
5. Commit with the smart-commit format, push, and open a PR **into `dev`**, titled `SCRUM-5 Repo scaffold`. After one teammate approves, merge with **Create a merge commit**, then delete the branch.
6. Tell the group chat when it is merged. Everyone then creates their own feature branch from `dev`.

**Acceptance criteria:** folders exist; README explains setup; `.env` is gitignored and `.env.example` exists; the repo clones and nothing in it contains secrets.

**Commit example:** `SCRUM-5 #comment add folder structure with gitkeep files`

### SCRUM-6: FastAPI skeleton with health endpoint and CORS (3 pts)
Branch: `feature/SCRUM-6-fastapi-skeleton` from `dev`.

1. Create `backend/requirements.txt`: `fastapi`, `uvicorn[standard]`, `python-multipart` (needed for file upload), `pydantic`, `python-dotenv`, `langchain-google-genai`, `pytest`, `httpx` (for the test client). Pin versions once things work.
2. `backend/config.py`: a small `Settings` object that loads `.env` and exposes `GOOGLE_API_KEY`, `GEMINI_MODEL` (default `gemini-3.8-flash`), `FRONTEND_ORIGIN` (default `http://localhost:5173`), `MAX_UPLOAD_MB` (default 10), and `UPLOAD_DIR` (default `data/uploads`). Rehan imports the model name from here, so merge this early.
3. `backend/main.py`: create the `FastAPI()` app, add `CORSMiddleware` allowing `FRONTEND_ORIGIN`, include routers, expose `GET /health` returning `{"status": "ok"}`.
4. Make it run from the `backend/` folder with `uvicorn main:app --reload`, and document the commands in the README (fix the README if your actual commands differ).

```python
# backend/main.py (starting point)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings

app = FastAPI(title="BillWakeel API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}
```

**Acceptance criteria:** `GET /health` returns 200; CORS allows `http://localhost:5173`; settings come from a config module; run steps are in the README.

**Target:** merged to `dev` by Thu 15 Oct.

**Commit examples:** `SCRUM-6 #comment add settings module reading env` / `SCRUM-6 #comment add cors middleware and health endpoint`

### SCRUM-9: Bill upload endpoint with validation (3 pts), plus the other Sprint 1 endpoints
Branch: `feature/SCRUM-9-upload-endpoint`.

Implement the API exactly as in Part A section 8.2.

1. `backend/api/bills.py` with an `APIRouter(prefix="/bills")`.
2. `POST /bills`: accepts a multipart `file`. Validate content type against `image/jpeg`, `image/png`, `application/pdf` (415 otherwise). Reject empty files (400). Reject files above `MAX_UPLOAD_MB` (413); read the file in a way that does not trust the client's size header. Generate a `bill_id` (`uuid4`). Save to `data/uploads/<bill_id>.<ext>`. Return 201 with `bill_id`, `filename`, `content_type`, `size_bytes`.
3. `POST /bills/{bill_id}/extract`: look up the bill (404 if unknown) and call `extract_bill(file_path, content_type)`. Until Rehan merges the real agent, use a stub that returns the example JSON from section 8.1 so Ayesha can build against it. Translate `GeminiError` to 502 and `ExtractionError` to 422, with `{"detail": "..."}` bodies.
4. `PUT /bills/{bill_id}/extraction`: validate the body against `BillExtraction`, store it, return it. Use a simple in-memory dictionary store for now (a database comes in Sprint 2).
5. Write a note in the README listing the endpoints and an example `curl` for each.

**Security basics (worth mentioning in the viva):** never use the user-supplied filename as a path (use the generated id); check the content type and, if you have time, check the file's magic bytes; limit size; do not log file contents.

**Acceptance criteria:** `POST /bills` accepts jpg/png/pdf, rejects other types and oversized files with 4xx, returns a bill id; unit tests (Swati writes them in SCRUM-14) cover accept and reject. You review her tests.

**Commit examples:** `SCRUM-9 #comment add upload endpoint with type and size validation` / `SCRUM-9 #comment add extract endpoint using extraction stub` / `SCRUM-9 #comment add put endpoint to save corrected values`

## B2. Day-by-day plan

| Day | Tasks |
|---|---|
| Tue 13 Oct | Wait for Rehan's message (docs on `main`, `dev` created, ruleset on). Then SCRUM-5: branch from `dev`, add the scaffold, open a PR into `dev`. |
| Wed 14 Oct | SCRUM-6: requirements, config, main app, health. Open PR. |
| Thu 15 Oct | Respond to review, merge SCRUM-6. Tell Rehan and Ayesha it is on `dev`. |
| Fri 16 Oct | Start SCRUM-9: router, upload validation. |
| Mon 19 Oct | Mid-sprint check. Finish `POST /bills`, start `extract` with the stub. |
| Tue 20 Oct | Finish and merge SCRUM-9 including PUT. Swap the stub for Rehan's real `extract_bill` once merged. |
| Wed 21 Oct | Support Ayesha's frontend integration (CORS or response-shape problems). Review Swati's tests. |
| Thu 22 Oct | Integration and bug fixing. Demo rehearsal. |
| Fri 23 Oct | Demo the API (Swagger docs at `/docs` is a nice live view). Retrospective. |

## B3. Hand-offs
- **To everyone:** `dev` branch ready and the scaffold in place (Tue 13 Oct).
- **To Rehan:** `config.py` so he can read the model name from it.
- **To Ayesha:** a running `/health`, then the stubbed `/extract` so she can build against real HTTP calls.
- **To Swati:** the final list of endpoints and error codes so tests match.

## B4. Review duties
You review Rehan's SCRUM-8/10 PRs and Ayesha's SCRUM-7/11 PRs. Check: runs locally, no secrets, commit format, acceptance criteria met.

## B5. Pitfalls
- Don't commit directly to `main` after the ruleset is on; use PRs.
- Forgetting `python-multipart` makes file upload fail with a confusing error.
- Don't store uploaded files with their original filenames.
- Don't change an endpoint's response shape without telling Ayesha, Rehan and Swati.
- Don't commit anything in `data/uploads/`.

## B6. Viva preparation checklist
Be ready to explain: the folder structure and why; what CORS is and why the frontend needs it; how FastAPI validates requests with Pydantic; how uploads are validated and why filenames are not trusted; the error codes (415, 413, 400, 404, 422, 502) and what each means; why the in-memory store is temporary; each of your commits; the branch and PR flow.

## B7. Starter prompts for your LLM
- "Write `backend/config.py` and `backend/main.py` for FastAPI with CORS and a `/health` endpoint, reading settings from a `.env` file."
- "Write a FastAPI `POST /bills` route that accepts an uploaded jpg/png/pdf, validates type and size, saves it with a uuid filename, and returns JSON."
- "Explain how to write pytest tests for a FastAPI file upload using TestClient."

## B8. Sprint 1 done checklist
- [ ] SCRUM-5, 6, 9 merged to `dev` via reviewed PRs, tickets Done with points.
- [ ] `dev` merged to `main` and tagged `sprint-1` on Fri 23 Oct (coordinate with the team).
- [ ] Every commit uses `SCRUM-n #comment ...`.
- [ ] README setup steps tested on a fresh clone.
