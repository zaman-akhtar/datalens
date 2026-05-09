import { CartesianGrid, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from "recharts";
import type { QueryRow } from "@/lib/types";

export function ScatterView({ data, title }: { data: QueryRow[]; title: string }) {
  const points = data.map((r) => ({ x: Number(r.label) || 0, y: r.value }));
  return (
    <div className="rounded border bg-white p-3" data-testid="chart-scatter">
      <div className="mb-1 text-sm font-medium">{title}</div>
      <ResponsiveContainer width="100%" height={220}>
        <ScatterChart>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="x" type="number" />
          <YAxis dataKey="y" type="number" />
          <Tooltip />
          <Scatter data={points} fill="#a855f7" />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
