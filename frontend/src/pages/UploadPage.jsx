import { useRef, useState } from "react";
import ExtractionForm from "../components/ExtractionForm";
import FindingsView from "../components/FindingsView";
import {
  uploadBill,
  extractBill,
  saveExtraction,
  getFindings,
} from "../services/billApi";
import { USE_MOCK_FINDINGS } from "../config";

function UploadPage() {
  const [file, setFile] = useState(null);
  const [billId, setBillId] = useState(null);
  const [extraction, setExtraction] = useState(null);
  const [isAnalysing, setIsAnalysing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [findings, setFindings] = useState(null);
  const [isLoadingFindings, setIsLoadingFindings] = useState(false);
  const [findingsError, setFindingsError] = useState("");
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  // Bumped whenever findings become stale, so a slow response for old values
  // is ignored instead of appearing next to edited fields.
  const findingsRequest = useRef(0);

  function discardFindings() {
    findingsRequest.current += 1;
    setFindings(null);
    setFindingsError("");
    setIsLoadingFindings(false);
  }

  function handleExtractionChange(updated) {
    setExtraction(updated);
    discardFindings();
  }

  async function handleAnalyse() {
    if (!file) return;

    setError("");
    setStatus("");
    setExtraction(null);
    setBillId(null);
    discardFindings();
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

  async function loadFindings(id) {
    discardFindings();
    const requestId = findingsRequest.current;
    setIsLoadingFindings(true);

    try {
      const result = await getFindings(id);
      if (requestId === findingsRequest.current) setFindings(result);
    } catch (err) {
      if (requestId === findingsRequest.current) {
        setFindingsError(
          err.message || "Unable to check this bill against the tariff.",
        );
      }
    } finally {
      if (requestId === findingsRequest.current) setIsLoadingFindings(false);
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
      await loadFindings(billId);
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
    discardFindings();
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
          onChange={handleExtractionChange}
          onSave={handleSave}
          isSaving={isSaving}
        />
      )}

      {isLoadingFindings && (
        <p role="status">Checking your bill against the published tariff...</p>
      )}
      {findingsError && <p role="alert">{findingsError}</p>}
      {findings && <FindingsView findings={findings} isDemo={USE_MOCK_FINDINGS} />}
    </main>
  );
}

export default UploadPage;