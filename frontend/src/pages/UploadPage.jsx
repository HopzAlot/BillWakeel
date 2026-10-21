import { useState } from "react";

function UploadPage() {
  const [file, setFile] = useState(null);

  return (
    <main className="upload-page">
      <h1>Analyse your utility bill</h1>

      <p>Select a bill image or PDF to get started.</p>

      <input
        type="file"
        accept=".jpg,.jpeg,.png,.pdf"
        onChange={(event) => setFile(event.target.files[0] || null)}
      />

      <button type="button" disabled={!file}>
        Analyse bill
      </button>

      {file && <p>Selected file: {file.name}</p>}
    </main>
  );
}

export default UploadPage;