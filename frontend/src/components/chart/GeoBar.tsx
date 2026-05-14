import type { GeoRow } from "@/lib/types";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  ResponsiveContainer,
} from "recharts";

function fraudColor(rate: number, maxRate: number): string {
  const t = maxRate > 0 ? Math.min(rate / maxRate, 1) : 0;
  const r = Math.round(55 + t * 200);
  const g = Math.round(160 - t * 120);
  return `rgb(${r},${g},60)`;
}

export function GeoBarView({ data, title }: { data: GeoRow[]; title: string }) {
  const maxRate = Math.max(...data.map((d) => d.fraud_rate), 0.0001);
  return (
    <div data-testid="chart-map" className="rounded-xl border border-gray-700/30 bg-gray-900/60 p-3">
      <div className="text-xs font-medium text-gray-200 mb-1">{title}</div>
      <div className="text-xs text-gray-500 mb-2">
        bar length = transactions · color = fraud rate (green → red)
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 0, right: 20, bottom: 0, left: 8 }}
        >
          <XAxis type="number" tick={{ fill: "#9ca3af", fontSize: 10 }} axisLine={false} tickLine={false} />
          <YAxis type="category" dataKey="state" width={32} tick={{ fill: "#9ca3af", fontSize: 10 }} axisLine={false} tickLine={false} />
          <Tooltip
            contentStyle={{ background: "#1f2937", border: "1px solid #374151", color: "#f9fafb" }}
            formatter={(value: number, name: string) =>
              name === "fraud_rate"
                ? [`${(value * 100).toFixed(2)}%`, "Fraud rate"]
                : [value.toLocaleString(), "Transactions"]
            }
            labelFormatter={(label) => `Region: ${label}`}
          />
          <Bar dataKey="count" maxBarSize={18}>
            {data.map((entry, i) => (
              <Cell key={i} fill={fraudColor(entry.fraud_rate, maxRate)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
