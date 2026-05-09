import type { DatasetProfile } from "@/lib/types";

export function ProfileCard({ profile }: { profile: DatasetProfile }) {
  const visible = profile.columns.filter((c) => !c.is_index);
  return (
    <div data-testid="profile-card" className="rounded border bg-white p-3">
      <div className="flex justify-between items-baseline">
        <h2 className="font-medium">{profile.original_filename}</h2>
        <span className="text-xs text-slate-500">
          {profile.n_rows.toLocaleString()} rows × {profile.n_cols} cols
        </span>
      </div>
      <div className="mt-2 max-h-56 overflow-y-auto">
        <table className="text-xs w-full">
          <thead>
            <tr className="text-left text-slate-500 border-b">
              <th className="py-1 pr-2">Column</th>
              <th className="py-1 pr-2">Type</th>
              <th className="py-1 pr-2">Unique</th>
              <th className="py-1 pr-2">Null %</th>
              <th className="py-1">Sample</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((c) => (
              <tr key={c.safe_name} className="border-b last:border-0">
                <td className="py-1 pr-2 font-mono">{c.name}</td>
                <td className="py-1 pr-2">{c.dtype}</td>
                <td className="py-1 pr-2">{c.n_unique}</td>
                <td className="py-1 pr-2">{(c.null_pct * 100).toFixed(1)}%</td>
                <td className="py-1 truncate max-w-[16rem]">
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
