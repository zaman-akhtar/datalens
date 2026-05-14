import type { DatasetProfile } from "@/lib/types";

export function ProfileCard({ profile }: { profile: DatasetProfile }) {
  const visible = profile.columns.filter((c) => !c.is_index);
  return (
    <div data-testid="profile-card" className="rounded-xl border border-gray-700/30 bg-gray-900/60 p-3">
      <div className="flex justify-between items-baseline">
        <h2 className="font-semibold text-gray-200 text-sm">{profile.original_filename}</h2>
        <span className="text-xs text-gray-500">
          {profile.n_rows.toLocaleString()} rows × {profile.n_cols} cols
        </span>
      </div>
      <div className="mt-2 max-h-48 overflow-y-auto">
        <table className="text-xs w-full">
          <thead>
            <tr className="text-left text-gray-500 border-b border-gray-700/40">
              <th className="py-1 pr-3 font-medium">Column</th>
              <th className="py-1 pr-3 font-medium">Type</th>
              <th className="py-1 pr-3 font-medium">Unique</th>
              <th className="py-1 pr-3 font-medium">Null %</th>
              <th className="py-1 font-medium">Sample</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((c) => (
              <tr key={c.safe_name} className="border-b border-gray-800/60 last:border-0 hover:bg-gray-800/30 transition-colors">
                <td className="py-1 pr-3 font-mono text-indigo-300">{c.name}</td>
                <td className="py-1 pr-3 text-gray-400">{c.dtype}</td>
                <td className="py-1 pr-3 text-gray-300">{c.n_unique.toLocaleString()}</td>
                <td className="py-1 pr-3 text-gray-300">{(c.null_pct * 100).toFixed(1)}%</td>
                <td className="py-1 truncate max-w-[16rem] text-gray-400">
                  {c.sample_values.slice(0, 3).map((v) => String(v)).join(", ")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
