export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// Set VITE_MOCK_FINDINGS=populated or VITE_MOCK_FINDINGS=empty to demo the
// findings view without the backend. Any other value (or unset) uses the real
// GET /bills/{bill_id}/findings endpoint.
const MOCK_FINDINGS_MODES = ["populated", "empty"];
const requestedMock = import.meta.env.VITE_MOCK_FINDINGS;

export const MOCK_FINDINGS_MODE = MOCK_FINDINGS_MODES.includes(requestedMock)
  ? requestedMock
  : "";
export const USE_MOCK_FINDINGS = MOCK_FINDINGS_MODE !== "";
