import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { useDataset } from "@/hooks/useDataset";
import { useFilters } from "@/hooks/useFilters";
import type { ChartSpec, GeoRow, QueryResult } from "@/lib/types";
import { BarView } from "./chart/Bar";
import { LineView } from "./chart/Line";
import { HistogramView } from "./chart/Histogram";
import { ScatterView } from "./chart/Scatter";
import { KpiView } from "./chart/Kpi";
import { GeoBarView } from "./chart/GeoBar";

export function ChartGrid() {
  const datasetId = useDataset((s) => s.datasetId);
  const filters = useFilters((s) => s.filters);
  const [specs, setSpecs] = useState<ChartSpec[] | null>(null);
  const [results, setResults] = useState<Record<number, QueryResult>>({});
  const [geoData, setGeoData] = useState<GeoRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setSpecs(null);
    setResults({});
    setGeoData(null);
    if (!datasetId) return;
    api
      .chartPicks(datasetId)
      .then(setSpecs)
      .catch((e) => setError(String(e)));
  }, [datasetId]);

  const hasMapSpec = specs?.some((s) => s.chart_type === "map") ?? false;

  useEffect(() => {
    if (!datasetId || !hasMapSpec) return;
    setGeoData(null);
    api.geo(datasetId).then(setGeoData).catch(() => setGeoData([]));
  }, [datasetId, hasMapSpec]);

  const filterKey = useMemo(() => JSON.stringify(filters), [filters]);

  useEffect(() => {
    if (!datasetId || !specs) return;
    setResults({});
    let cancelled = false;
    Promise.all(
      specs.map((spec) =>
        spec.chart_type === "map"
          ? Promise.resolve({ sql: "", n_rows: 0, rows: [] } as QueryResult)
          : api.runQuery(datasetId, spec, filters).catch(
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
  if (error) return <div className="p-3 text-red-400 text-sm">{error}</div>;

  const skeletonCount = specs?.length ?? 4;
  const queriesLoading = specs !== null && specs.length > 0 && Object.keys(results).length < specs.length;

  if (!specs || queriesLoading)
    return (
      <div data-testid="chart-grid-loading" className="grid grid-cols-2 gap-3">
        {Array.from({ length: skeletonCount }).map((_, i) => (
          <div
            key={i}
            className="rounded-xl border border-gray-700/30 bg-gray-900/40 h-[268px] animate-pulse"
          />
        ))}
      </div>
    );

  return (
    <div data-testid="charts-grid" className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {specs.map((spec, i) => {
        if (spec.chart_type === "map") {
          if (!geoData)
            return (
              <div
                key={i}
                className="rounded-xl border border-gray-700/30 bg-gray-900/40 h-[268px] animate-pulse"
              />
            );
          if (!geoData.length)
            return (
              <div
                key={i}
                className="rounded-xl border border-gray-700/30 bg-gray-900/40 p-3 text-xs text-gray-500"
              >
                {spec.title} — no geographic data
              </div>
            );
          return <GeoBarView key={i} data={geoData} title={spec.title} />;
        }

        const rows = results[i]?.rows ?? [];
        if (!rows.length && results[i])
          return (
            <div
              key={i}
              className="rounded-xl border border-gray-700/30 bg-gray-900/40 p-3 text-xs text-gray-500"
            >
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
