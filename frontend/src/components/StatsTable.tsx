import type { DatasetProfile } from "@/lib/types";

export function StatsTable({ profile }: { profile: DatasetProfile }) {
  const numeric = profile.columns.filter((c) => !c.is_index && c.dtype === "numeric");
  const categorical = profile.columns.filter((c) => !c.is_index && c.dtype === "categorical");
  const other = profile.columns.filter(
    (c) => !c.is_index && c.dtype !== "numeric" && c.dtype !== "categorical"
  );

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard label="Total Rows" value={profile.n_rows.toLocaleString()} color="indigo" />
        <StatCard label="Columns" value={String(profile.n_cols)} color="violet" />
        <StatCard label="Numeric" value={String(numeric.length)} color="cyan" />
        <StatCard label="Categorical" value={String(categorical.length)} color="emerald" />
      </div>

      {numeric.length > 0 && (
        <Section title="Numeric Columns">
          <div className="overflow-x-auto">
            <table className="text-xs w-full">
              <thead>
                <tr className="text-gray-500 border-b border-gray-700/40">
                  <Th left>Column</Th>
                  <Th>Min</Th>
                  <Th>Max</Th>
                  <Th>Mean</Th>
                  <Th>Skew</Th>
                  <Th>Unique</Th>
                  <Th>Null %</Th>
                </tr>
              </thead>
              <tbody>
                {numeric.map((c, i) => (
                  <tr
                    key={c.safe_name}
                    className={`border-b border-gray-800/60 transition-colors hover:bg-gray-800/30 ${
                      i % 2 === 1 ? "bg-gray-800/10" : ""
                    }`}
                  >
                    <td className="px-4 py-2 font-mono text-indigo-300">{c.name}</td>
                    <td className="px-4 py-2 text-right text-gray-300">{fmt(c.min)}</td>
                    <td className="px-4 py-2 text-right text-gray-300">{fmt(c.max)}</td>
                    <td className="px-4 py-2 text-right text-gray-300">{fmt(c.mean)}</td>
                    <td className="px-4 py-2 text-right text-gray-300">{fmt(c.skew)}</td>
                    <td className="px-4 py-2 text-right text-gray-300">
                      {c.n_unique.toLocaleString()}
                    </td>
                    <td className="px-4 py-2 text-right">
                      <NullBadge pct={c.null_pct} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      )}

      {categorical.length > 0 && (
        <Section title="Categorical Columns">
          <div className="overflow-x-auto">
            <table className="text-xs w-full">
              <thead>
                <tr className="text-gray-500 border-b border-gray-700/40">
                  <Th left>Column</Th>
                  <Th>Unique Values</Th>
                  <Th>Null %</Th>
                  <Th left>Sample Values</Th>
                </tr>
              </thead>
              <tbody>
                {categorical.map((c, i) => (
                  <tr
                    key={c.safe_name}
                    className={`border-b border-gray-800/60 transition-colors hover:bg-gray-800/30 ${
                      i % 2 === 1 ? "bg-gray-800/10" : ""
                    }`}
                  >
                    <td className="px-4 py-2 font-mono text-violet-300">{c.name}</td>
                    <td className="px-4 py-2 text-right text-gray-300">
                      {c.n_unique.toLocaleString()}
                    </td>
                    <td className="px-4 py-2 text-right">
                      <NullBadge pct={c.null_pct} />
                    </td>
                    <td className="px-4 py-2 text-gray-400 truncate max-w-[240px]">
                      {c.sample_values
                        .filter((v) => v !== null && v !== "")
                        .slice(0, 4)
                        .map(String)
                        .join(", ")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      )}

      {other.length > 0 && (
        <Section title="Other Columns">
          <div className="overflow-x-auto">
            <table className="text-xs w-full">
              <thead>
                <tr className="text-gray-500 border-b border-gray-700/40">
                  <Th left>Column</Th>
                  <Th left>Type</Th>
                  <Th>Unique</Th>
                  <Th>Null %</Th>
                  <Th left>Sample</Th>
                </tr>
              </thead>
              <tbody>
                {other.map((c, i) => (
                  <tr
                    key={c.safe_name}
                    className={`border-b border-gray-800/60 transition-colors hover:bg-gray-800/30 ${
                      i % 2 === 1 ? "bg-gray-800/10" : ""
                    }`}
                  >
                    <td className="px-4 py-2 font-mono text-cyan-300">{c.name}</td>
                    <td className="px-4 py-2 text-gray-400">{c.dtype}</td>
                    <td className="px-4 py-2 text-right text-gray-300">
                      {c.n_unique.toLocaleString()}
                    </td>
                    <td className="px-4 py-2 text-right">
                      <NullBadge pct={c.null_pct} />
                    </td>
                    <td className="px-4 py-2 text-gray-400 truncate max-w-[180px]">
                      {c.sample_values.slice(0, 3).map(String).join(", ")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-gray-700/30 bg-gray-900/50 overflow-hidden">
      <div className="px-4 py-2.5 border-b border-gray-700/30">
        <h3 className="text-sm font-semibold text-gray-200">{title}</h3>
      </div>
      {children}
    </div>
  );
}

function Th({ children, left }: { children: React.ReactNode; left?: boolean }) {
  return (
    <th className={`px-4 py-2 font-medium ${left ? "text-left" : "text-right"}`}>
      {children}
    </th>
  );
}

function fmt(n: number | null | undefined): string {
  if (n === null || n === undefined) return "—";
  if (Math.abs(n) >= 1e6) return n.toExponential(2);
  return n.toLocaleString(undefined, { maximumFractionDigits: 3 });
}

function NullBadge({ pct }: { pct: number }) {
  const p = pct * 100;
  const cls =
    p === 0 ? "text-emerald-400" : p < 5 ? "text-yellow-400" : "text-red-400";
  return <span className={cls}>{p.toFixed(1)}%</span>;
}

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: "indigo" | "violet" | "cyan" | "emerald";
}) {
  const styles: Record<string, string> = {
    indigo: "text-indigo-400 border-indigo-500/20",
    violet: "text-violet-400 border-violet-500/20",
    cyan: "text-cyan-400 border-cyan-500/20",
    emerald: "text-emerald-400 border-emerald-500/20",
  };
  return (
    <div className={`rounded-xl border bg-gray-900/50 px-4 py-3 ${styles[color]}`}>
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className={`text-2xl font-bold ${styles[color].split(" ")[0]}`}>{value}</div>
    </div>
  );
}
