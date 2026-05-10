export type DType = "numeric" | "categorical" | "datetime" | "boolean" | "text";
export type ChartType = "bar" | "line" | "histogram" | "scatter" | "kpi";
export type Aggregation = "count" | "sum" | "mean" | "min" | "max" | "median";

export interface ColumnProfile {
  name: string;
  safe_name: string;
  dtype: DType;
  null_pct: number;
  n_unique: number;
  sample_values: (string | number | boolean | null)[];
  is_index: boolean;
  min: number | null;
  max: number | null;
  mean: number | null;
  skew: number | null;
}

export interface DatasetProfile {
  dataset_id: string;
  original_filename: string;
  n_rows: number;
  n_cols: number;
  columns: ColumnProfile[];
  created_at: string;
}

export interface UploadAck {
  dataset_id: string;
  original_filename: string;
  n_rows: number;
  n_cols: number;
}

export interface ChartSpec {
  chart_type: ChartType;
  title: string;
  x: string;
  y: string | null;
  agg: string;
  bins: number | null;
  note: string | null;
}

export interface QueryRow {
  label: string | number | boolean | null;
  value: number;
}

export interface QueryResult {
  sql: string;
  n_rows: number;
  rows: QueryRow[];
}

export interface ToolCallRecord {
  name: string;
  args: Record<string, unknown>;
  result_preview: string;
}

export interface ChatResponse {
  answer: string;
  conversation_id: string;
  tool_calls: ToolCallRecord[];
  partial: boolean;
}

export interface ChatMessageRecord {
  role: "user" | "assistant" | "tool";
  content: string;
  created_at: string;
}

export interface SummaryResponse {
  dataset_id: string;
  text: string;
  generated_at: string;
}

export type FilterMap = Record<string, string | number | null>;
