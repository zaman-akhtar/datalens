import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { QueryRow } from "@/lib/types";

export function BarView({ data, title }: { data: QueryRow[]; title: string }) {
  const safe = data.map((r) => ({ label: String(r.label ?? "—"), value: r.value }));
  return (
    <div className="rounded border bg-white p-3" data-testid="chart-bar">
      <div className="mb-1 text-sm font-medium">{title}</div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={safe} margin={{ top: 4, right: 8, bottom: 30, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="label" angle={-30} textAnchor="end" height={60} interval={0} />
          <YAxis />
          <Tooltip />
          <Bar dataKey="value" fill="#3b82f6" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
