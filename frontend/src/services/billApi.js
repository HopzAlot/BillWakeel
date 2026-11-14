
import { API_BASE_URL } from "../config";

async function handleResponse(response) {
  const contentType = response.headers.get("content-type");

  const data = contentType?.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const message =
      typeof data === "string"
        ? data
        : data.detail || data.message || `Request failed (${response.status})`;

    throw new Error(message);
  }

  return data;
}

// 1. Upload the bill file.
export async function uploadBill(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/bills`, {
    method: "POST",
    body: formData,
  });

  return handleResponse(response);
}

// 2. Extract fields from an uploaded bill.
export async function extractBill(billId) {
  const response = await fetch(
    `${API_BASE_URL}/bills/${encodeURIComponent(billId)}/extract`,
    { method: "POST" },
  );

  return handleResponse(response);
}

// 3. Save the user's corrected extraction.
export async function saveExtraction(billId, extraction) {
  const response = await fetch(
    `${API_BASE_URL}/bills/${encodeURIComponent(billId)}/extraction`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(extraction),
    },
  );

  return handleResponse(response);
}
