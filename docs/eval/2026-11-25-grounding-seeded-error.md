# Grounding eval — 2026-11-25

Prompt version: A-1(a) / grounding v1
Model: gemini-3.5-flash-lite
Scope: 1 seeded-error K-Electric A-1(a) bill (GST inflated by Rs. 500)

## Result

PASS: 1 finding(s), expected exactly 1 (GST)

## Findings

- GST: billed Rs. 903.1, expected Rs. 403.1, diff Rs. 500.0, clause KE-3-6 (medium confidence)
  Explanation: The GST billed amount of Rs. 903.10 differs from the expected amount of Rs. 403.10, which should be calculated using the standard statutory rate of 18% applied to the specified billing components under the Sales Tax Act 1990, with exemptions for lifeline domestic consumers.
