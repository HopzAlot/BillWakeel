
const TEXT_FIELDS = [
  ["provider", "Utility provider", "text"],
  ["billing_month", "Billing month (YYYY-MM)", "month"],
  ["issue_date", "Issue date", "date"],
  ["due_date", "Due date", "date"],
  ["tariff_category", "Tariff category", "text"],
  ["sanctioned_load_kw", "Sanctioned load (kW)", "number"],
  ["meter_reading_previous", "Previous meter reading", "number"],
  ["meter_reading_current", "Current meter reading", "number"],
  ["units_consumed", "Units consumed", "number"],
  ["arrears_pkr", "Arrears (PKR)", "number"],
  ["total_payable_by_due_date", "Total payable by due date (PKR)", "number"],
  ["total_payable_after_due_date", "Total payable after due date (PKR)", "number"],
];

function ExtractionForm({
  extraction,
  onChange,
  onSave,
  isSaving,
}) {
  if (!extraction) return null;

  function updateField(name, value, type) {
    const parsedValue =
      value === ""
        ? null
        : type === "number"
          ? Number(value)
          : value;

    onChange({ ...extraction, [name]: parsedValue });
  }

  function updateCharge(index, key, value) {
    const charges = extraction.charges.map((charge, i) =>
      i === index
        ? {
            ...charge,
            [key]: key === "amount_pkr"
              ? (value === "" ? null : Number(value))
              : value,
          }
        : charge,
    );

    onChange({ ...extraction, charges });
  }

  function addCharge() {
    onChange({
      ...extraction,
      charges: [
        ...extraction.charges,
        { name: "", amount_pkr: null },
      ],
    });
  }

  function removeCharge(index) {
    onChange({
      ...extraction,
      charges: extraction.charges.filter((_, i) => i !== index),
    });
  }

  return (
    <form
      className="extraction-form"
      onSubmit={(event) => {
        event.preventDefault();
        onSave();
      }}
    >
      <h2>Review extracted details</h2>
      <p>Check the values and correct anything the AI extracted incorrectly.</p>

      <label className="extraction-field">
        Utility type
        <select
          value={extraction.utility ?? ""}
          onChange={(event) =>
            updateField("utility", event.target.value, "text")
          }
        >
          <option value="">Select utility</option>
          <option value="electricity">Electricity</option>
          <option value="gas">Gas</option>
          <option value="water">Water</option>
          <option value="unknown">Unknown</option>
        </select>
      </label>

      {TEXT_FIELDS.map(([name, label, type]) => (
        <label className="extraction-field" key={name}>
          {label}
          <input
            type={type}
            step={type === "number" ? "any" : undefined}
            value={extraction[name] ?? ""}
            onChange={(event) =>
              updateField(name, event.target.value, type)
            }
          />
        </label>
      ))}

      <section className="charges-section">
        <h3>Bill charges</h3>

        {(extraction.charges ?? []).map((charge, index) => (
          <div className="charge-row" key={index}>
            <label className="extraction-field">
              Charge name
              <input
                type="text"
                value={charge.name ?? ""}
                onChange={(event) =>
                  updateCharge(index, "name", event.target.value)
                }
              />
            </label>

            <label className="extraction-field">
              Amount (PKR)
              <input
                type="number"
                step="any"
                value={charge.amount_pkr ?? ""}
                onChange={(event) =>
                  updateCharge(index, "amount_pkr", event.target.value)
                }
              />
            </label>

            <button
              type="button"
              className="secondary-button"
              onClick={() => removeCharge(index)}
            >
              Remove
            </button>
          </div>
        ))}

        <button
          type="button"
          className="secondary-button"
          onClick={addCharge}
        >
          Add charge
        </button>
      </section>

      <label className="extraction-field">
        Notes
        <textarea
          rows={3}
          value={extraction.notes ?? ""}
          onChange={(event) =>
            updateField("notes", event.target.value, "text")
          }
        />
      </label>

      <button type="submit" disabled={isSaving}>
        {isSaving ? "Saving..." : "Save corrected details"}
      </button>
    </form>
  );
}

export default ExtractionForm;
