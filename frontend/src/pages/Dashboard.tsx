import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useDataset } from "@/hooks/useDataset";
import { UploadDropzone } from "@/components/UploadDropzone";
import { ProfileCard } from "@/components/ProfileCard";
import { FilterBar } from "@/components/FilterBar";
import { ChartGrid } from "@/components/ChartGrid";
import { ChatPanel } from "@/components/ChatPanel";
import { ExecutiveSummary } from "@/components/ExecutiveSummary";
import { StatsTable } from "@/components/StatsTable";
import { useFilters } from "@/hooks/useFilters";
import type { DatasetProfile } from "@/lib/types";

type Tab = "charts" | "stats" | "summary";

const TABS: { id: Tab; label: string }[] = [
  { id: "charts", label: "Charts" },
  { id: "stats", label: "Statistics" },
  { id: "summary", label: "Summary" },
];

export function Dashboard() {
  const datasetId = useDataset((s) => s.datasetId);
  const filename = useDataset((s) => s.filename);
  const [profile, setProfile] = useState<DatasetProfile | null>(null);
  const [tab, setTab] = useState<Tab>("charts");

  useEffect(() => {
    setProfile(null);
    if (!datasetId) return;
    api.profile(datasetId).then(setProfile).catch(() => setProfile(null));
  }, [datasetId]);

  if (!datasetId) {
    return (
      <div className="min-h-screen bg-[#070c18] flex items-center justify-center p-6">
        <div className="w-full max-w-lg animate-fade-up">
          <div className="text-center mb-10">
            <h1 className="text-5xl font-extrabold bg-gradient-to-r from-indigo-400 via-violet-400 to-purple-400 bg-clip-text text-transparent tracking-tight">
              DataLens
            </h1>
            <p className="text-gray-400 mt-4 text-base leading-relaxed">
              Upload any CSV to see an auto-generated dashboard, ask questions in
              chat, and get an executive summary.
            </p>
          </div>
          <UploadDropzone />
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-[#070c18] flex flex-col overflow-hidden">
      <header className="flex items-center justify-between px-5 py-3 border-b border-gray-800/60 flex-shrink-0">
        <h1 className="text-lg font-extrabold bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent tracking-tight">
          DataLens
        </h1>
        {filename && (
          <span className="text-xs text-gray-500 hidden sm:block truncate max-w-xs">
            {filename}
          </span>
        )}
        <UploadDropzoneCompact />
      </header>

      <div className="flex flex-1 min-h-0 gap-3 p-3">
        <main className="flex flex-col flex-1 min-w-0 gap-3 overflow-y-auto pr-1">
          {profile && <ProfileCard profile={profile} />}
          {profile && datasetId && <FilterBar columns={profile.columns} datasetId={datasetId} />}

          <div className="flex gap-1 bg-gray-900/60 rounded-lg p-1 w-fit border border-gray-800/50">
            {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all duration-200 ${
                  tab === t.id
                    ? "bg-indigo-600 text-white shadow-lg shadow-indigo-900/40"
                    : "text-gray-400 hover:text-gray-200 hover:bg-gray-800/50"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          <div key={tab} className="animate-fade-up pb-4">
            {tab === "charts" && <ChartGrid />}
            {tab === "stats" && profile && <StatsTable profile={profile} />}
            {tab === "summary" && <ExecutiveSummary />}
          </div>
        </main>

        <aside className="w-[340px] flex-shrink-0 flex flex-col">
          <ChatPanel />
        </aside>
      </div>
    </div>
  );
}

function UploadDropzoneCompact() {
  const clear = useDataset((s) => s.clear);
  const clearFilters = useFilters((s) => s.clear);
  return (
    <button
      onClick={() => { clear(); clearFilters(); }}
      className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
    >
      ↑ Upload another CSV
    </button>
  );
}
