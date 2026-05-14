import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useFilters } from "@/hooks/useFilters";
import type { ChartSpec, ColumnProfile } from "@/lib/types";

interface Props {
  columns: ColumnProfile[];
  datasetId: string;
}

export function FilterBar({ columns, datasetId }: Props) {
  const { filters, setFilter, clear } = useFilters();
  const [options, setOptions] = useState<Record<string, string[]>>({});

  const filterable = columns.filter(
    (c) => !c.is_index && c.dtype === "categorical" && c.n_unique <= 100
  );

  // Fetch actual unique values for each filterable column via the query endpoint.
  useEffect(() => {
    if (!datasetId || !filterable.length) return;
    setOptions({});
    Promise.all(
      filterable.map((col) => {
        const spec: ChartSpec = {
          chart_type: "bar",
          title: "",
          x: col.safe_name,
          y: null,
          agg: "count",
          bins: null,
          note: null,
        };
        return api
          .runQuery(datasetId, spec, {})
          .then((result) => ({
            key: col.safe_name,
            values: result.rows
              .map((r) => String(r.label ?? ""))
              .filter((v) => v !== "" && v !== "null")
              .sort(),
          }))
          .catch(() => ({ key: col.safe_name, values: [] }));
      })
    ).then((results) => {
      const next: Record<string, string[]> = {};
      results.forEach((r) => { next[r.key] = r.values; });
      setOptions(next);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datasetId, filterable.length]);

  if (!filterable.length)
    return (
      <div data-testid="filters-bar" className="text-xs text-gray-500 px-1 py-2">
        No categorical filters available for this dataset.
      </div>
    );

  return (
    <div
      data-testid="filters-bar"
      className="flex gap-2 flex-wrap px-3 py-2 bg-gray-900/40 border border-gray-700/30 rounded-xl items-center"
    >
      <span className="text-xs text-gray-500 mr-1">Filter:</span>
      {filterable.map((col) => {
        const values = options[col.safe_name] ?? [];
        return (
          <select
            key={col.safe_name}
            data-testid={`filter-${col.safe_name}`}
            aria-label={`Filter by ${col.name}`}
            value={(filters[col.safe_name] as string | undefined) ?? ""}
            onChange={(e) => setFilter(col.safe_name, e.target.value || null)}
            className="bg-gray-800/70 border border-gray-700/50 text-gray-300 text-xs rounded-lg px-2 py-1 focus:outline-none focus:border-indigo-500/60"
          >
            <option value="">{col.name} (all)</option>
            {values.map((v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ))}
          </select>
        );
      })}
      {Object.keys(filters).length > 0 && (
        <button
          onClick={clear}
          className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors px-1"
        >
          Clear filters
        </button>
      )}
    </div>
  );
}
