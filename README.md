# BillWakeel

An agentic web platform that checks Pakistani utility bills against official tariffs and drafts a cited dispute letter you can review and send yourself.

Course project for **EC-360 Software Engineering (CEP)**, NUST CEME, Fall 2026. Instructor: Dr. Farooque Azam.

> **Disclaimer:** BillWakeel is not legal advice. It points out where a bill differs from published tariff clauses. You review every letter before sending it.

## What it does

1. **Upload** a utility bill (photo or PDF).
2. **Extraction Agent** reads it into structured data. You can correct any field.
3. **Tariff-Grounding Agent** recalculates the bill in code from NEPRA/OGRA tariff data and retrieves the exact clause for any difference.
4. **Anomaly Agent** compares against your bill history.
5. **Dispute-Letter Agent** drafts a letter that cites only verified findings, in a tone you choose (Polite, Firm, "No More Mr. Nice Guy").

Design rules: arithmetic is done in deterministic Python, never by the LLM; a finding without a verifiable cited clause is dropped; letters are never auto-submitted.

**Scope:** electricity (NEPRA-regulated DISCOs, phased rollout), gas (SNGPL, SSGC), water as a single-city pilot.

## Tech stack

- Backend: FastAPI (Python)
- Frontend: React with Vite
- AI: Google Gemini via LangChain (`langchain-google-genai`)
- Storage: SQLite with SQLAlchemy, vector store for tariff clauses

## Repository layout

```
BillWakeel/
├── backend/        # FastAPI app: api/, agents/, services/, models/
├── frontend/       # React (Vite) app
├── prompts/        # versioned prompts per agent + CHANGELOG.md
├── data/
│   ├── tariffs/    # raw/ source documents, structured/ JSON
│   └── samples/    # anonymised bills and ground-truth labels
├── tests/          # unit/, integration/, prompt/, eval/
├── docs/           # roadmap, decisions, DoR/DoD, sprint reviews, eval results
├── CONTRIBUTING.md
└── README.md
```

## Getting started

Prerequisites: Python 3.11+, Node 18+, a Google AI (Gemini) API key.

```bash
git clone https://github.com/HopzAlot/BillWakeel.git
cd BillWakeel
cp .env.example .env        # then add your GOOGLE_API_KEY
```

**Backend**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload   # adjust the module path to match the code
```
Health check: http://localhost:8000/health

**Frontend**
```bash
cd frontend
npm install
npm run dev
```
App: http://localhost:5173

**Verify the Gemini connection**
```bash
python check_connection.py
```

## Team and roles (Sprint 1)

| Member | Sprint 1 role |
|---|---|
| Muhammad Rehan Saqib | Developer |
| Muhammad Abdullah Baig | Developer |
| Ayesha Zafar | Scrum Master |
| Muhammad Abdullah Swati (GC) | Product Owner |

Roles rotate every sprint. See `docs/` for the schedule.

## Project management

- Jira board: https://software-ka-project.atlassian.net/jira/software/projects/SCRUM/boards/1
- Process, branch names, commit format, PRs and Definition of Done: see [CONTRIBUTING.md](CONTRIBUTING.md)
- Plan and sprint dates: see `docs/BillWakeel_Roadmap.md`

## Sprint schedule

| Sprint | Dates |
|---|---|
| 1 | 12 Oct – 23 Oct 2026 |
| 2 | 26 Oct – 6 Nov 2026 |
| 3 | 9 Nov – 20 Nov 2026 |
| 4 | 23 Nov – 4 Dec 2026 |
