# Grounding eval — 2026-11-25

Prompt version: A-1(a) / grounding v1
Model: gemini-3.5-flash-lite
Scope: 1 seeded-error K-Electric A-1(a) bill (GST inflated by Rs. 500)

## Result

PASS: 1 finding(s), expected exactly 1 (GST)

## Findings

- GST: billed Rs. 851.27, expected Rs. 351.27, diff Rs. 500.0, clause KE-179-1 (high confidence)
  Explanation: The billed GST amount of Rs. 851.27 differs from the expected amount of Rs. 351.27, which should be reviewed against the standard 18% rate set under SRO 179(I)/2023 and the Sales Tax Act 1990.
