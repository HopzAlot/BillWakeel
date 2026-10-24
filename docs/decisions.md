# Engineering decisions

One entry per decision: date, decision, rationale.

## 2026-10-13: Arithmetic lives in code, not the LLM
A deterministic Python engine recalculates bills from structured tariff data. The LLM extracts, explains and writes, never computes. This is the main hallucination defence.

## 2026-10-13: Stack is FastAPI + React (Vite)
FastAPI fits the Python AI ecosystem (LangChain, Pydantic). React gives a flexible UI.

## 2026-10-13: Letters are never auto-submitted
No public submission API exists, and a human should own a dispute. The user reviews and sends.

## 2026-10-24: Pin Gemini model to gemini-3.5-flash-lite, not gemini-3.8-flash
Free tier for gemini-3.8-flash is 5 RPM / 20 RPD (confirmed via AI Studio's rate-limit dashboard) — nearly unusable for eval runs across 10 sample bills plus team testing. gemini-3.5-flash-lite has 15 RPM / 500 RPD. Switched locally via .env; backend/config.py's hardcoded default and .env.example still need updating to make this the team-wide default.
