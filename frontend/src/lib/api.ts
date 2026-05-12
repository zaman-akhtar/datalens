import type {
  ChartSpec,
  ChatMessageRecord,
  ChatResponse,
  DatasetProfile,
  FilterMap,
  GeoRow,
  QueryResult,
  SummaryResponse,
  UploadAck,
} from "./types";

const BASE = "/api";

async function jsonOrThrow<T>(r: Response): Promise<T> {
  if (!r.ok) {
    const body = await r.text();
    throw new Error(`${r.status} ${r.statusText}: ${body}`);
  }
  return (await r.json()) as T;
}

export const api = {
  async upload(file: File): Promise<UploadAck> {
    const fd = new FormData();
    fd.append("file", file);
    return jsonOrThrow<UploadAck>(await fetch(`${BASE}/upload`, { method: "POST", body: fd }));
  },
  async profile(datasetId: string): Promise<DatasetProfile> {
    return jsonOrThrow<DatasetProfile>(await fetch(`${BASE}/datasets/${datasetId}/profile`));
  },
  async chartPicks(datasetId: string): Promise<ChartSpec[]> {
    return jsonOrThrow<ChartSpec[]>(await fetch(`${BASE}/datasets/${datasetId}/charts`));
  },
  async runQuery(
    datasetId: string,
    spec: ChartSpec,
    filters: FilterMap
  ): Promise<QueryResult> {
    const body = {
      x: spec.x,
      y: spec.y,
      agg: spec.agg,
      bins: spec.bins,
      filters,
      limit: 100,
    };
    return jsonOrThrow<QueryResult>(
      await fetch(`${BASE}/datasets/${datasetId}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      })
    );
  },
  async chat(
    datasetId: string,
    message: string,
    conversationId: string | null
  ): Promise<ChatResponse> {
    return jsonOrThrow<ChatResponse>(
      await fetch(`${BASE}/datasets/${datasetId}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, conversation_id: conversationId }),
      })
    );
  },
  async chatHistory(datasetId: string): Promise<ChatMessageRecord[]> {
    return jsonOrThrow<ChatMessageRecord[]>(
      await fetch(`${BASE}/datasets/${datasetId}/chat/history`)
    );
  },
  async summary(datasetId: string, refresh = false): Promise<SummaryResponse> {
    const url = `${BASE}/datasets/${datasetId}/summary${refresh ? "?refresh=true" : ""}`;
    return jsonOrThrow<SummaryResponse>(await fetch(url));
  },
  async geo(datasetId: string): Promise<GeoRow[]> {
    return jsonOrThrow<GeoRow[]>(await fetch(`${BASE}/datasets/${datasetId}/geo`));
  },
};
