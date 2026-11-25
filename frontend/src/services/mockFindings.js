// Mock FindingsResponse objects, shaped exactly like the Finding contract
// (docs: Sprint 2 brief section 8.4). Used only when VITE_MOCK_FINDINGS is set.
// All values below are illustrative placeholders, NOT real tariff data.

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
      source_url: "https://example.com/tariff-notification.pdf",
      confidence: "high",
    },
    {
      charge_name: "Fixed charges",
      billed_amount_pkr: 200.0,
      expected_amount_pkr: 200.0,
      difference_pkr: 0.0,
      clause_id: "EXAMPLE-CLAUSE-2",
      clause_text:
        "Placeholder clause text: fixed monthly charge for the tariff category.",
      source_url: "https://example.com/tariff-notification.pdf",
      confidence: "medium",
    },
  ],
  recalculated_total_pkr: 8210.0,
  model: "mock",
};

const EMPTY = {
  findings: [],
  recalculated_total_pkr: 8345.5,
  model: "mock",
};

export async function getMockFindings(billId) {
  const mode = import.meta.env.VITE_MOCK_FINDINGS;
  const base = mode === "empty" ? EMPTY : POPULATED;
  return { bill_id: billId, ...base };
}
