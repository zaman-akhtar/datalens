import { useRef, useState } from "react";
import { api } from "@/lib/api";
import { useDataset } from "@/hooks/useDataset";

export function UploadDropzone() {
  const inputRef = useRef<HTMLInputElement>(null);
  const setDataset = useDataset((s) => s.set);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFile(file: File) {
    setBusy(true);
    setError(null);
    try {
      const ack = await api.upload(file);
      setDataset(ack.dataset_id, ack.original_filename);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      data-testid="upload-zone"
      className="border-2 border-dashed border-slate-300 rounded p-8 text-center hover:border-blue-400 bg-white"
      onDragOver={(e) => e.preventDefault()}
      onDrop={(e) => {
        e.preventDefault();
        const file = e.dataTransfer.files?.[0];
        if (file) void handleFile(file);
      }}
    >
      <p className="text-slate-600 mb-3">Drag a CSV here, or</p>
      <button
        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        onClick={() => inputRef.current?.click()}
        disabled={busy}
      >
        {busy ? "Uploading…" : "Choose a file"}
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
        }}
      />
      {error && (
        <p data-testid="upload-error" className="mt-3 text-sm text-red-600">
          {error}
        </p>
      )}
    </div>
  );
}
