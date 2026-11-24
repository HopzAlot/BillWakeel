"""Pydantic schemas for the Tariff-Grounding Agent's output (SCRUM-31).

Proposed by Rehan per Brief §8.4, with one addition: `explanation` (Gemini's
non-accusatory phrasing, kept separate from `clause_text` so the exact quoted
source text is never edited by the model). See docs/decisions.md for why.
This is the shared contract for SCRUM-33 (DB models) and SCRUM-34 (findings
UI) — do not change field names or types without agreement from the team.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class Finding(BaseModel):
    charge_name: str
    billed_amount_pkr: float
    expected_amount_pkr: float
    difference_pkr: float
    clause_id: str
    clause_text: str  # the exact retrieved clause text, unedited by the LLM
    explanation: str  # Gemini's non-accusatory phrasing of the discrepancy
    source_url: str
    confidence: Literal["high", "medium", "low"] = "high"


class FindingsResponse(BaseModel):
    bill_id: str
    findings: list[Finding]
    recalculated_total_pkr: float
    model: str
