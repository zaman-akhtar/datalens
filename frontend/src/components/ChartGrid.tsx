import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { useDataset } from "@/hooks/useDataset";
import { useFilters } from "@/hooks/useFilters";
import type { ChartSpec, QueryResult } from "@/lib/types";
import { BarView } from "./chart/Bar";
import { LineView } from "./chart/Line";
import { HistogramView } from "./chart/Histogram";
import { ScatterView } from "./chart/Scatter";
import { KpiView } from "./chart/Kpi";

export function ChartGrid() {
  const datasetId = useDataset((s) => s.datasetId);
  const filters = useFilters((s) => s.filters);
  const [specs, setSpecs] = useState<ChartSpec[] | null>(null);
  const [results, setResults] = useState<Record<number, QueryResult>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setSpecs(null);
    setResults({});
    if (!datasetId) return;
    api
      .chartPicks(datasetId)
      .then(setSpecs)
      .catch((e) => setError(String(e)));
  }, [datasetId]);

  const filterKey = useMemo(() => JSON.stringify(filters), [filters]);

  useEffect(() => {
    if (!datasetId || !specs) return;
    let cancelled = false;
    Promise.all(
      specs.map((spec) =>
        api.runQuery(datasetId, spec, filters).catch(
          () => ({ sql: "", n_rows: 0, rows: [] }) as QueryResult
        )
      )
    ).then((rs) => {
      if (cancelled) return;
      const next: Record<number, QueryResult> = {};
      rs.forEach((r, i) => (next[i] = r));
      setResults(next);
    });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datasetId, specs, filterKey]);

  if (!datasetId) return null;
  if (error) return <div className="p-3 text-red-600 text-sm">{error}</div>;
  if (!specs)
    return (
      <div data-testid="chart-grid-loading" className="grid grid-cols-2 gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="rounded border bg-white h-56 animate-pulse" />
        ))}
      </div>
    );

  return (
    <div data-testid="charts-grid" className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {specs.map((spec, i) => {
        const rows = results[i]?.rows ?? [];
        if (!rows.length && results[i])
          return (
            <div key={i} className="rounded border bg-white p-3 text-xs text-slate-400">
              {spec.title} — no data after filters
            </div>
          );
        const props = { data: rows, title: spec.title };
        switch (spec.chart_type) {
          case "bar":
            return <BarView key={i} {...props} />;
          case "line":
            return <LineView key={i} {...props} />;
          case "histogram":
            return <HistogramView key={i} {...props} />;
          case "scatter":
            return <ScatterView key={i} {...props} />;
          case "kpi":
            return <KpiView key={i} {...props} />;
          default:
            return null;
        }
      })}
    </div>
  );
}
