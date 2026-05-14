import { CartesianGrid, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from "recharts";
import type { QueryRow } from "@/lib/types";

export function ScatterView({ data, title }: { data: QueryRow[]; title: string }) {
  const points = data.map((r) => ({ x: Number(r.label) || 0, y: r.value }));
  return (
    <div className="rounded-xl border border-gray-700/30 bg-gray-900/60 p-3" data-testid="chart-scatter">
      <div className="mb-1 text-sm font-medium text-gray-200">{title}</div>
      <ResponsiveContainer width="100%" height={220}>
        <ScatterChart>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="x" type="number" tick={{ fill: "#9ca3af", fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis dataKey="y" type="number" tick={{ fill: "#9ca3af", fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={{ background: "#1f2937", border: "1px solid #374151", color: "#f9fafb" }} />
          <Scatter data={points} fill="#a855f7" />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
