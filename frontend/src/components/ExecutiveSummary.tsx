import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { useDataset } from "@/hooks/useDataset";

export function ExecutiveSummary() {
  const datasetId = useDataset((s) => s.datasetId);
  const [text, setText] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const cancelRef = useRef(false);

  async function load(refresh = false) {
    if (!datasetId) return;
    setBusy(true);
    cancelRef.current = false;
    try {
      const s = await api.summary(datasetId, refresh);
      if (!cancelRef.current) setText(s.text);
    } finally {
      if (!cancelRef.current) setBusy(false);
    }
  }

  useEffect(() => {
    cancelRef.current = true;
    setText(null);
    if (datasetId) void load(false);
    return () => { cancelRef.current = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datasetId]);

  if (!datasetId)
    return <div className="p-3 text-sm text-slate-400">Upload a CSV to generate a summary.</div>;

  return (
    <div data-testid="executive-summary" className="rounded border bg-white p-3">
      <div className="flex justify-between items-center mb-2">
        <h3 className="font-medium">Executive summary</h3>
        <div className="space-x-2">
          <button
            data-testid="summary-regenerate"
            onClick={() => void load(true)}
            className="text-xs underline disabled:opacity-50"
            disabled={busy}
          >
            {busy ? "Generating…" : "Regenerate"}
          </button>
          <button
            data-testid="summary-copy"
            onClick={() => {
              if (text) void navigator.clipboard?.writeText(text);
            }}
            className="text-xs underline"
          >
            Copy
          </button>
        </div>
      </div>
      {text ? (
        <p data-testid="summary-text" className="text-sm whitespace-pre-wrap leading-relaxed">
          {text}
        </p>
      ) : (
        <p className="text-sm text-slate-400">{busy ? "Generating…" : ""}</p>
      )}
    </div>
  );
}
