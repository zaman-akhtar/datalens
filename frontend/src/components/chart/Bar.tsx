import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { QueryRow } from "@/lib/types";

export function BarView({ data, title }: { data: QueryRow[]; title: string }) {
  const safe = data.map((r) => ({ label: String(r.label ?? "—"), value: r.value }));
  return (
    <div className="rounded-xl border border-gray-700/30 bg-gray-900/60 p-3" data-testid="chart-bar">
      <div className="mb-1 text-sm font-medium text-gray-200">{title}</div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={safe} margin={{ top: 4, right: 8, bottom: 30, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="label" angle={-30} textAnchor="end" height={60} interval={0} tick={{ fill: "#9ca3af", fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={{ background: "#1f2937", border: "1px solid #374151", color: "#f9fafb" }} />
          <Bar dataKey="value" fill="#6366f1" radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
