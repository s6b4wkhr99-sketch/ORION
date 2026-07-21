"use client";

type MappingRow = { uploaded_column: string; internal_field: string | null };

type MappingPreviewProps = {
  rows: MappingRow[];
  onChange: (uploadedColumn: string, internalField: string) => void;
};

const INTERNAL_FIELDS = [
  "email", "first_name", "last_name", "phone", "address", "city", "state", "zip",
  "country", "permission", "age_range", "generation", "gender", "estimated_income",
  "home_value", "household", "length_of_residence", "net_worth", "online_access",
  "retail_card", "dwelling", "bank_card", "adults", "children", "persons",
];

export function MappingPreviewPanel({ rows, onChange }: MappingPreviewProps) {
  return (
    <section className="cios-card overflow-hidden">
      <div className="border-b border-[var(--cios-border)] px-5 py-4">
        <h2 className="text-base font-semibold text-gray-900">Mapping Preview</h2>
        <p className="mt-1 text-sm text-[var(--cios-secondary)]">
          Override mappings before upload. Changes apply to the next processing run.
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-gray-50 text-xs uppercase text-[var(--cios-secondary)]">
            <tr>
              <th className="px-5 py-3">Uploaded Column</th>
              <th className="px-5 py-3">Internal Field</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.uploaded_column} className="border-t border-gray-100">
                <td className="px-5 py-3 font-medium text-gray-900">{row.uploaded_column}</td>
                <td className="px-5 py-3">
                  <select
                    className="cios-input w-full max-w-xs bg-white px-2 py-1.5"
                    value={row.internal_field ?? ""}
                    onChange={(e) => onChange(row.uploaded_column, e.target.value)}
                  >
                    <option value="">— unmapped —</option>
                    {INTERNAL_FIELDS.map((f) => (
                      <option key={f} value={f}>
                        {f}
                      </option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
