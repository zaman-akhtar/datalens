import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { useDataset } from "@/hooks/useDataset";

export function ExecutiveSummary() {
  const datasetId = useDataset((s) => s.datasetId);
  const [text, setText] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const cancelRef = useRef(false);

  async function load(refresh = false) {
    if (!datasetId) return;
    setBusy(true);
    setError(null);
    cancelRef.current = false;
    try {
      const s = await api.summary(datasetId, refresh);
      if (!cancelRef.current) setText(s.text);
    } catch (e) {
      if (!cancelRef.current)
        setError(e instanceof Error ? e.message : "Failed to generate summary.");
    } finally {
      if (!cancelRef.current) setBusy(false);
    }
  }

  useEffect(() => {
    cancelRef.current = true;
    setText(null);
    setError(null);
    if (datasetId) void load(false);
    return () => { cancelRef.current = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datasetId]);

  if (!datasetId)
    return (
      <div className="p-3 text-sm text-gray-500">
        Upload a CSV to generate a summary.
      </div>
    );

  return (
    <div data-testid="executive-summary" className="rounded-xl border border-gray-700/30 bg-gray-900/60 p-4">
      <div className="flex justify-between items-center mb-3">
        <h3 className="font-semibold text-gray-200 text-sm">Executive Summary</h3>
        <div className="flex gap-3">
          <button
            data-testid="summary-regenerate"
            onClick={() => void load(true)}
            className="text-xs text-indigo-400 hover:text-indigo-300 disabled:opacity-40 transition-colors"
            disabled={busy}
          >
            {busy ? "Generating…" : "Regenerate"}
          </button>
          <button
            data-testid="summary-copy"
            onClick={() => { if (text) void navigator.clipboard?.writeText(text); }}
            className="text-xs text-gray-400 hover:text-gray-300 transition-colors"
          >
            Copy
          </button>
        </div>
      </div>

      {error && (
        <p className="text-sm text-red-400 mb-2">{error}</p>
      )}

      {text ? (
        <p data-testid="summary-text" className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">
          {text}
        </p>
      ) : (
        <p className="text-sm text-gray-500">{busy ? "Generating summary…" : ""}</p>
      )}
    </div>
  );
}
