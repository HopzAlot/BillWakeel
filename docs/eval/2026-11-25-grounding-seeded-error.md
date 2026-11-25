# Grounding eval — 2026-11-25

Prompt version: A-1(a) / grounding v1
Model: gemini-3.5-flash-lite
Scope: 1 seeded-error K-Electric A-1(a) bill (GST inflated by Rs. 500)

## Result

PASS: 1 finding(s), expected exactly 1 (GST)

## Findings

- GST: billed Rs. 851.27, expected Rs. 351.27, diff Rs. 500.0, clause KE-3-6 (high confidence)
  Explanation: The GST charge of Rs. 851.27 differs from the expected amount of Rs. 351.27, which is calculated at the standard statutory rate of 18% applied to applicable energy, fixed, and adjustment charges under the Sales Tax Act 1990, with exemptions for lifeline domestic consumers.
