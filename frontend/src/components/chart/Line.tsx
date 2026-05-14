import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { QueryRow } from "@/lib/types";

export function LineView({ data, title }: { data: QueryRow[]; title: string }) {
  const safe = data.map((r) => ({ label: String(r.label ?? ""), value: r.value }));
  return (
    <div className="rounded-xl border border-gray-700/30 bg-gray-900/60 p-3" data-testid="chart-line">
      <div className="mb-1 text-sm font-medium text-gray-200">{title}</div>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={safe}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="label" tick={{ fill: "#9ca3af", fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={{ background: "#1f2937", border: "1px solid #374151", color: "#f9fafb" }} />
          <Line type="monotone" dataKey="value" stroke="#10b981" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
