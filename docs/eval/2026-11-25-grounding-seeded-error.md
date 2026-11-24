# Grounding eval — 2026-11-25

Prompt version: A-1(a) / grounding v1
Model: gemini-3.5-flash-lite
Scope: 1 seeded-error K-Electric A-1(a) bill (GST inflated by Rs. 500)

## Result

PASS: 1 finding(s), expected exactly 1 (GST)

## Findings

- GST: billed Rs. 851.27, expected Rs. 351.27, diff Rs. 500.0, clause KE-3-6 (medium confidence)
  Explanation: The billed GST of Rs. 851.27 differs from the expected amount of Rs. 351.27, and this charge should be reviewed against the standard statutory rate and tax calculation base defined under the Sales Tax Act 1990, keeping in mind that lifeline domestic consumers are exempt.
