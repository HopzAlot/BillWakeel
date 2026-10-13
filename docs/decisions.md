# Engineering decisions

One entry per decision: date, decision, rationale.

## 2026-10-13: Arithmetic lives in code, not the LLM
A deterministic Python engine recalculates bills from structured tariff data. The LLM extracts, explains and writes, never computes. This is the main hallucination defence.

## 2026-10-13: Stack is FastAPI + React (Vite)
FastAPI fits the Python AI ecosystem (LangChain, Pydantic). React gives a flexible UI.

## 2026-10-13: Letters are never auto-submitted
No public submission API exists, and a human should own a dispute. The user reviews and sends.
