export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// Set VITE_MOCK_FINDINGS=populated (or "empty") to demo the findings view
// before the real GET /bills/{bill_id}/findings endpoint is available.
export const USE_MOCK_FINDINGS = import.meta.env.VITE_MOCK_FINDINGS || "";
