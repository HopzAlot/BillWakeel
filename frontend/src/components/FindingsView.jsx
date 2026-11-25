const CONFIDENCE_LABELS = {
  high: "High confidence",
  medium: "Medium confidence",
  low: "Low confidence",
};

function formatPkr(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "N/A";
  }

  return `Rs ${Number(value).toLocaleString("en-PK", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function formatDifference(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "N/A";
  }

  const n = Number(value);
  const sign = n > 0 ? "+" : n < 0 ? "-" : "";

  return `${sign}${formatPkr(Math.abs(n))}`;
}

// Only link to real http(s) URLs, so a bad source_url can never become a
// javascript: link.
function isSafeUrl(url) {
  return typeof url === "string" && /^https?:\/\//i.test(url);
}

function FindingCard({ finding }) {
  const confidence = finding.confidence || "high";

  return (
    <li className="finding-card">
      <div className="finding-header">
        <h3>{finding.charge_name}</h3>
        <span className={`finding-confidence confidence-${confidence}`}>
          {CONFIDENCE_LABELS[confidence] || confidence}
        </span>
      </div>

      <dl className="finding-amounts">
        <div>
          <dt>Billed</dt>
          <dd>{formatPkr(finding.billed_amount_pkr)}</dd>
        </div>
        <div>
          <dt>Expected per tariff</dt>
          <dd>{formatPkr(finding.expected_amount_pkr)}</dd>
        </div>
        <div>
          <dt>Difference</dt>
          <dd className="finding-difference">
            {formatDifference(finding.difference_pkr)}
          </dd>
        </div>
      </dl>

      <figure className="finding-clause">
        <figcaption>
          Published tariff clause: <strong>{finding.clause_id}</strong>
        </figcaption>
        <blockquote>{finding.clause_text}</blockquote>
        {isSafeUrl(finding.source_url) ? (
          <a href={finding.source_url} target="_blank" rel="noopener noreferrer">
            View source document
          </a>
        ) : (
          <span className="finding-no-source">Source link unavailable</span>
        )}
      </figure>
    </li>
  );
}

function FindingsView({ findings }) {
  if (!findings) return null;

  const list = findings.findings ?? [];

  return (
    <section className="findings-view" aria-label="Tariff findings">
      <h2>Tariff check</h2>

      {list.length === 0 ? (
        <div className="findings-empty" role="status">
          <p>
            <strong>No discrepancies found.</strong>
          </p>
          <p>
            We recalculated this bill from the published tariff and did not
            find any charge that differs from it.
          </p>
        </div>
      ) : (
        <>
          <p className="findings-intro">
            {list.length === 1
              ? "1 charge differs from the published tariff."
              : `${list.length} charges differ from the published tariff.`}{" "}
            Each is shown with the clause it was compared against.
          </p>
          <ul className="findings-list">
            {list.map((finding, index) => (
              <FindingCard
                key={`${finding.clause_id}-${finding.charge_name}-${index}`}
                finding={finding}
              />
            ))}
          </ul>
        </>
      )}

      {findings.recalculated_total_pkr !== undefined &&
        findings.recalculated_total_pkr !== null && (
          <p className="findings-total">
            Recalculated total from tariff:{" "}
            <strong>{formatPkr(findings.recalculated_total_pkr)}</strong>
          </p>
        )}

      <p className="findings-note">
        These results compare your bill with the published tariff. They are
        not legal advice, and nothing is sent anywhere on your behalf.
      </p>
    </section>
  );
}

export default FindingsView;
