import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { QueryRow } from "@/lib/types";

export function LineView({ data, title }: { data: QueryRow[]; title: string }) {
  const safe = data.map((r) => ({ label: String(r.label ?? ""), value: r.value }));
  return (
    <div className="rounded border bg-white p-3" data-testid="chart-line">
      <div className="mb-1 text-sm font-medium">{title}</div>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={safe}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="label" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="value" stroke="#10b981" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
