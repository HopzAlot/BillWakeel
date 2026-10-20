# Sample bills

Real utility bills used to evaluate the Extraction Agent. Each bill image has a
ground-truth JSON with the same base name (e.g. `hazeco_001.jpg` + `hazeco_001.json`).

| File | Provider | Utility | Billing month | Units | Payable by due date (Rs) | Notes |
|---|---|---|---|---|---|---|
| hazeco_001 | HAZECO | electricity | 2026-08 | 145 | 2,485 | phone photo, clear |
| hazeco_002 | HAZECO | electricity | 2026-08 | 99 | 1,620 | phone photo, clear |
| hazeco_003 | HAZECO | electricity | 2026-07 | 100 | 1,562 | faint print, values misaligned (edge case) |
| hazeco_004 | HAZECO | electricity | 2026-07 | 114 | 1,637 | phone photo, clear |
| iesco_001 | IESCO | electricity | 2026-04 | 181 | 7,626 | values printed one row low (edge case) |
| iesco_002 | IESCO | electricity | 2026-07 | 323 | 15,128 | phone photo, clear |
| sngpl_001 | SNGPL | gas | 2023-06 | 0.389 HM3 | 2,110 | phone photo, clear |
| sngpl_002 | SNGPL | gas | 2023-09 | 0.430 HM3 | 1,050 | faint current reading |
| sngpl_003 | SNGPL | gas | 2026-07 | 0.194 HM3 | 1,040 | phone photo, clear |
| sngpl_004 | SNGPL | gas | 2026-08 | 0.234 HM3 | 970 | phone photo, clear |

## Anonymisation
Blacked out with opaque boxes: names, addresses, consumer/account IDs, old A/C
numbers, reference numbers, bill IDs, meter numbers, CNIC, zone/book/page numbers,
feeder names, barcodes, QR codes, meter-reader photos and GPS lines, handwritten
notes with phone numbers. Images were re-saved as new JPEGs, so no original
metadata remains. Bills shared with the owners' permission; originals kept offline.

## Labelling rules
- Ground truth drafted with AI assistance and verified by hand against each bill.
- Charge lines: every printed line except subtotals/totals, named as printed.
- Blank arrears = null.
- total_payable_after_due_date = first after-due amount; the second tier is in notes.
- Gas: units_consumed = gas consumed in HM3 (MMBTU in notes); readings as printed.
- Each file checked in code: charges + arrears match the payable amount within bill rounding.
