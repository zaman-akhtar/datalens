import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useDataset } from "@/hooks/useDataset";
import { UploadDropzone } from "@/components/UploadDropzone";
import { ProfileCard } from "@/components/ProfileCard";
import { FilterBar } from "@/components/FilterBar";
import { ChartGrid } from "@/components/ChartGrid";
import { ChatPanel } from "@/components/ChatPanel";
import { ExecutiveSummary } from "@/components/ExecutiveSummary";
import type { DatasetProfile } from "@/lib/types";

export function Dashboard() {
  const datasetId = useDataset((s) => s.datasetId);
  const [profile, setProfile] = useState<DatasetProfile | null>(null);

  useEffect(() => {
    setProfile(null);
    if (!datasetId) return;
    api.profile(datasetId).then(setProfile);
  }, [datasetId]);

  if (!datasetId) {
    return (
      <div className="max-w-2xl mx-auto p-6 mt-12">
        <h1 className="text-2xl font-semibold mb-4">DataLens</h1>
        <p className="text-slate-600 mb-6">
          Upload any CSV to see an auto-generated dashboard, ask questions in chat,
          and get an executive summary.
        </p>
        <UploadDropzone />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-12 gap-3 p-4 h-screen">
      <header className="col-span-12 flex justify-between items-center">
        <h1 className="text-xl font-semibold">DataLens</h1>
        <div className="text-xs text-slate-500">
          <UploadDropzoneCompact />
        </div>
      </header>

      <main className="col-span-8 space-y-3 overflow-y-auto">
        {profile && <ProfileCard profile={profile} />}
        {profile && <FilterBar columns={profile.columns} />}
        <ChartGrid />
        <ExecutiveSummary />
      </main>

      <aside className="col-span-4">
        <ChatPanel />
      </aside>
    </div>
  );
}

function UploadDropzoneCompact() {
  return (
    <details>
      <summary className="cursor-pointer underline">Upload another CSV</summary>
      <div className="mt-2 w-72">
        <UploadDropzone />
      </div>
    </details>
  );
}
