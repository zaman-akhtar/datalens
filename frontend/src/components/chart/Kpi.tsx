import type { QueryRow } from "@/lib/types";

export function KpiView({ data, title }: { data: QueryRow[]; title: string }) {
  // Boolean-rate KPIs: picker sends agg=count grouped by 0/1; positive-rate computed below.
  let display = "—";
  if (data.length === 1) {
    display = formatNumber(data[0].value);
  } else if (data.length > 1 && data.every((r) => r.label === 0 || r.label === 1 || r.label === "0" || r.label === "1")) {
    const total = data.reduce((s, r) => s + r.value, 0);
    const pos = data.find((r) => r.label === 1 || r.label === "1")?.value ?? 0;
    display = `${((pos / total) * 100).toFixed(2)}%`;
  } else if (data.length) {
    display = formatNumber(data.reduce((s, r) => s + r.value, 0));
  }
  return (
    <div className="rounded border bg-white p-3 flex flex-col items-center justify-center" data-testid="chart-kpi">
      <div className="text-xs text-slate-500">{title}</div>
      <div className="text-3xl font-semibold mt-2">{display}</div>
    </div>
  );
}

function formatNumber(n: number): string {
  if (Math.abs(n) >= 1000) return n.toLocaleString(undefined, { maximumFractionDigits: 0 });
  return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
}
