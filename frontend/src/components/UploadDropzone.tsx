import { useRef, useState } from "react";
import { api } from "@/lib/api";
import { useDataset } from "@/hooks/useDataset";
import { useFilters } from "@/hooks/useFilters";

const MAX_DISPLAY_MB = 500;

export function UploadDropzone() {
  const inputRef = useRef<HTMLInputElement>(null);
  const setDataset = useDataset((s) => s.set);
  const clearFilters = useFilters((s) => s.clear);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);

  async function handleFile(file: File) {
    if (!file.name.toLowerCase().endsWith(".csv")) {
      setError("Only .csv files are accepted.");
      return;
    }
    const sizeMB = file.size / 1024 / 1024;
    if (sizeMB > MAX_DISPLAY_MB) {
      setError(`File is ${sizeMB.toFixed(0)} MB — maximum is ${MAX_DISPLAY_MB} MB.`);
      return;
    }

    setBusy(true);
    setError(null);
    setNotice(null);
    setProgress(
      sizeMB > 50
        ? `Uploading ${sizeMB.toFixed(0)} MB — this may take a moment…`
        : "Uploading…"
    );

    try {
      const ack = await api.upload(file);
      clearFilters();
      setProgress(null);
      if (ack.sampled_from) {
        setNotice(
          `Large file: loaded a representative ${ack.n_rows.toLocaleString()}-row sample from ${ack.sampled_from.toLocaleString()} total rows.`
        );
      }
      setDataset(ack.dataset_id, ack.original_filename);
    } catch (e) {
      setProgress(null);
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      data-testid="upload-zone"
      className={`border-2 border-dashed rounded-xl p-10 text-center transition-colors cursor-pointer ${
        dragging
          ? "border-indigo-400 bg-indigo-950/20"
          : "border-gray-700 hover:border-indigo-500/60 bg-gray-900/40"
      }`}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        const file = e.dataTransfer.files?.[0];
        if (file) void handleFile(file);
      }}
      onClick={() => !busy && inputRef.current?.click()}
    >
      <div className="text-4xl mb-3 text-gray-600">↑</div>
      <p className="text-gray-400 mb-4 text-sm leading-relaxed">
        Drag a CSV here, or click to browse
        <br />
        <span className="text-gray-600 text-xs">Up to {MAX_DISPLAY_MB} MB · auto-sampled if large</span>
      </p>
      <button
        className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
        onClick={(e) => { e.stopPropagation(); inputRef.current?.click(); }}
        disabled={busy}
      >
        {busy ? "Processing…" : "Choose file"}
      </button>
      <input
        ref={inputRef}
        type="file"
        accept=".csv,text/csv"
        className="hidden"
        data-testid="upload-input"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) void handleFile(file);
          e.target.value = "";
        }}
      />
      {progress && (
        <p className="mt-4 text-sm text-indigo-400 animate-pulse">{progress}</p>
      )}
      {notice && (
        <p data-testid="upload-notice" className="mt-3 text-sm text-amber-400">
          {notice}
        </p>
      )}
      {error && (
        <p data-testid="upload-error" className="mt-3 text-sm text-red-400">
          {error}
        </p>
      )}
    </div>
  );
}
