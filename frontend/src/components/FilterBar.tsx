import { useFilters } from "@/hooks/useFilters";
import type { ColumnProfile } from "@/lib/types";

export function FilterBar({ columns }: { columns: ColumnProfile[] }) {
  const { filters, setFilter, clear } = useFilters();
  const filterable = columns.filter(
    (c) => !c.is_index && c.dtype === "categorical" && c.n_unique <= 50
  );

  if (!filterable.length)
    return (
      <div data-testid="filters-bar" className="text-xs text-slate-400 p-2">
        No categorical filters available for this dataset.
      </div>
    );

  return (
    <div data-testid="filters-bar" className="flex gap-2 flex-wrap p-2 bg-slate-100 rounded">
      {filterable.map((col) => (
        <select
          key={col.safe_name}
          data-testid={`filter-${col.safe_name}`}
          aria-label={`Filter by ${col.name}`}
          value={(filters[col.safe_name] as string | undefined) ?? ""}
          onChange={(e) => setFilter(col.safe_name, e.target.value || null)}
          className="border rounded px-2 py-1 text-sm bg-white"
        >
          <option value="">{col.name} (all)</option>
          {col.sample_values
            .filter((v) => v !== null && v !== "")
            .map((v) => (
              <option key={String(v)} value={String(v)}>
                {String(v)}
              </option>
            ))}
        </select>
      ))}
      <button onClick={clear} className="text-xs underline px-2 self-center">
        Clear
      </button>
    </div>
  );
}
