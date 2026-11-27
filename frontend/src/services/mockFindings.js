// Mock FindingsResponse objects, shaped like the backend contract in
// backend/models/finding.py (Finding.explanation, FindingsResponse.warnings).
// Used only when VITE_MOCK_FINDINGS is "populated" or "empty".
// All values below are illustrative placeholders, NOT real tariff data.

import { MOCK_FINDINGS_MODE } from "../config";

const POPULATED = {
  findings: [
    {
      charge_name: "Electricity charges (slab)",
      billed_amount_pkr: 4120.0,
      expected_amount_pkr: 3985.5,
      difference_pkr: 134.5,
      clause_id: "EXAMPLE-CLAUSE-1",
      clause_text:
        "Placeholder clause text: the per-unit rate for this slab as published in the tariff notification.",
      explanation:
        "Placeholder explanation: the billed amount is higher than the amount we calculated from the published rate for this slab. You may want to ask your utility how this charge was worked out.",
      source_url: "https://example.com/tariff-notification.pdf",
      confidence: "high",
    },
  ],
  recalculated_total_pkr: 8210.0,
  model: "mock",
  warnings: [
    "Placeholder warning: fixed charges were not checked because the consumer status could not be worked out from the bill.",
    "Placeholder warning: sales tax was calculated on an assumed base.",
  ],
};

const EMPTY = {
  findings: [],
  recalculated_total_pkr: 8345.5,
  model: "mock",
  warnings: [],
};

export async function getMockFindings(billId) {
  const base = MOCK_FINDINGS_MODE === "empty" ? EMPTY : POPULATED;
  return { bill_id: billId, ...base };
}
