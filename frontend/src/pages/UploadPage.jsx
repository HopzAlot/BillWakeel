import { useState } from "react";
import ExtractionForm from "../components/ExtractionForm";
import {
  uploadBill,
  extractBill,
  saveExtraction,
} from "../services/billApi";

function UploadPage() {
  const [file, setFile] = useState(null);
  const [billId, setBillId] = useState(null);
  const [extraction, setExtraction] = useState(null);
  const [isAnalysing, setIsAnalysing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");

  async function handleAnalyse() {
    if (!file) return;

    setError("");
    setStatus("");
    setExtraction(null);
    setBillId(null);
    setIsAnalysing(true);

    try {
      const uploadedBill = await uploadBill(file);

      if (!uploadedBill?.bill_id) {
        throw new Error("The upload response did not contain a bill ID.");
      }

      setBillId(uploadedBill.bill_id);
      setStatus("Bill uploaded. Extracting its details...");

      const result = await extractBill(uploadedBill.bill_id);

      if (!result?.extraction) {
        throw new Error("The extraction response did not contain bill fields.");
      }

      setExtraction(result.extraction);
      setStatus("Extraction complete. Review and correct the fields below.");
    } catch (err) {
      setError(err.message || "Unable to analyse this bill.");
      setStatus("");
    } finally {
      setIsAnalysing(false);
    }
  }

  async function handleSave() {
    if (!billId || !extraction) return;

    setError("");
    setStatus("");
    setIsSaving(true);

    try {
      const savedExtraction = await saveExtraction(billId, extraction);

      setExtraction(savedExtraction);
      setStatus("Your corrected bill details have been saved.");
    } catch (err) {
      setError(err.message || "Unable to save your corrections.");
    } finally {
      setIsSaving(false);
    }
  }

  function handleFileChange(event) {
    setFile(event.target.files?.[0] || null);
    setBillId(null);
    setExtraction(null);
    setError("");
    setStatus("");
  }

  return (
    <main className="upload-page">
      <h1>Analyse your utility bill</h1>
      <p>Select a bill image or PDF to get started.</p>

      <input
        type="file"
        accept=".jpg,.jpeg,.png,.pdf"
        onChange={handleFileChange}
        disabled={isAnalysing || isSaving}
      />

      {file && <p>Selected file: {file.name}</p>}

      <button
        type="button"
        onClick={handleAnalyse}
        disabled={!file || isAnalysing || isSaving}
      >
        {isAnalysing ? "Analysing..." : "Analyse bill"}
      </button>

      {status && <p role="status">{status}</p>}
      {error && <p role="alert">{error}</p>}

      {extraction && (
        <ExtractionForm
          extraction={extraction}
          onChange={setExtraction}
          onSave={handleSave}
          isSaving={isSaving}
        />
      )}
    </main>
  );
}

export default UploadPage;