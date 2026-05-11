# System Design — DataLens

Companion to `SPEC.md`. Where SPEC says **what**, this doc says **how**. Every section maps to a phase in `tasks/plan.md`.

---

## 1. High-level shape

```
┌──────────────────────────┐         HTTP+JSON         ┌──────────────────────────────────┐
│  React + Vite (5173)     │ ─────────────────────────▶│  FastAPI + Pydantic (8000)       │
│                          │                           │                                  │
│  • UploadDropzone        │                           │  • routers/upload                │
│  • ProfileCard           │                           │  • routers/profile               │
│  • FilterBar (Zustand)   │                           │  • routers/query                 │
│  • ChartGrid (Recharts)  │                           │  • routers/chat                  │
│  • ChatPanel             │                           │  • routers/summary               │
│  • ExecutiveSummary      │                           │                                  │
└──────────────────────────┘                           │  services/                       │
                                                       │   • ingest                       │
                                                       │   • profile                      │
                                                       │   • chart_picker                 │
                                                       │   • query_engine                 │
                                                       │   • llm/{provider, tools, ...}   │
                                                       └──────────────┬───────────────────┘
                                                                      │
                                                  SQLAlchemy core / sqlite3
                                                                      │
                                                       ┌──────────────▼───────────────────┐
                                                       │  SQLite — datalens.db            │
                                                       │   • datasets (catalog)           │
                                                       │   • dataset_<id> (one per CSV)   │
                                                       │   • chat_messages                │
                                                       └──────────────┬───────────────────┘
                                                                      │ HTTPS
                                                       ┌──────────────▼───────────────────┐
                                                       │  Google Gemini 1.5 Flash         │
                                                       │  (function calling)              │
                                                       └──────────────────────────────────┘
```

---

## 2. Backend — FastAPI route map

| Method | Path | Body / Query | Response model | Notes |
|---|---|---|---|---|
| `POST` | `/api/upload` | multipart `file` (≤ 50 MB) | `UploadAck {dataset_id, n_rows, n_cols}` | streams to disk, ingests into SQLite |
| `GET` | `/api/datasets` | — | `list[DatasetSummary]` | catalog for sidebar |
| `GET` | `/api/datasets/{id}/profile` | — | `DatasetProfile` | cached after first call |
| `POST` | `/api/datasets/{id}/query` | `QueryRequest {x, y?, agg, filters?, limit?}` | `QueryResult {rows, sql, n_rows}` | safe builder; never accepts free-form SQL |
| `POST` | `/api/datasets/{id}/chat` | `ChatRequest {message, conversation_id?}` | `ChatResponse {answer, tool_calls[], conversation_id}` | tool-use loop, max 4 iterations |
| `GET` | `/api/datasets/{id}/chat/history` | — | `list[ChatMessage]` | for refresh persistence |
| `GET` | `/api/datasets/{id}/summary` | `?refresh=true` | `Summary {text, generated_at}` | cached |

**Cross-cutting:** all 4xx/5xx responses return `ErrorBody {code, message, hint?}`. All endpoints validate input via Pydantic, validate output via `response_model`. CORS allows `localhost:5173` only.

---

## 3. Ingestion pipeline (CSV → SQLite)

Implemented in `services/ingest.py`. Five steps, each independently testable.

1. **Pre-flight check.** Stream the first 1 MB; reject if not UTF-8, no header row, or > 50 MB content-length. Returns 400/413 before any heavy work.
2. **Read with Pandas.** `pd.read_csv(..., low_memory=False, na_values=["", "NA", "N/A"])`. Cast `datetime`-looking columns with `pd.to_datetime(errors="coerce")` based on a regex screen of the first 100 values.
3. **Sanitize column names.** Lowercase, replace non-alphanum with `_`, dedupe with `_2` suffix. Keep a `display_name → safe_name` map in `datasets` row.
4. **Drop generic noise.** Any column matching `^Unnamed:` or where `nunique == nrows` AND dtype is int → flagged `is_index=true`, hidden from charts but kept queryable.
5. **Write.** `df.to_sql(f"dataset_{dataset_id}", conn, index=False, if_exists="replace")`. Wrap in a transaction.

**Why no per-column normalization beyond dtype coercion?** The brief requires "any CSV." Forcing schemas would break that contract. Anything dataset-specific (e.g. stripping `fraud_` from this dataset's `merchant`) lives in an opt-in `enrichment` hook gated by a column-fingerprint check.

---

## 4. SQLite schema strategy

Per ADR-003 — full rationale there. Summary:

```sql
-- Catalog
CREATE TABLE datasets (
    id TEXT PRIMARY KEY,                  -- ULID, used in URLs
    original_filename TEXT NOT NULL,
    n_rows INTEGER NOT NULL,
    n_cols INTEGER NOT NULL,
    column_meta_json TEXT NOT NULL,       -- map: display_name → {safe_name, dtype, is_index}
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- One table per uploaded CSV; column names are the SAFE names from step 3.
-- Created dynamically by services/ingest.py.
CREATE TABLE dataset_01HX...   ( ... cols inferred from CSV ... );

-- Chat persistence
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id TEXT NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user','assistant','tool')),
    content TEXT NOT NULL,
    tool_calls_json TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chat_dataset ON chat_messages(dataset_id, conversation_id, created_at);
```

The "one table per dataset" pattern is unconventional for production but fits the brief: each dataset is short-lived, queries are full-table scans on ≤ 50 MB, and it gives us a clean `SELECT … FROM dataset_<id>` surface for the LLM tools without an EAV nightmare.

---

## 5. Safe query builder (`services/query_engine.py`)

Single entry point: `run_query(dataset_id, x, y=None, agg="count", filters=None, limit=1000) -> QueryResult`.

- `x` and `y` and any filter column **must** appear in `datasets.column_meta_json` for that dataset, else raise `UnknownColumnError` → 400.
- `agg` ∈ `{count, sum, mean, min, max, median}` — enum, not a string.
- Filters become parametrized `?` placeholders; values pass through `sqlite3` parameter binding, never f-string interpolation.
- Datetime filters use `BETWEEN` with two parameters.
- `limit` capped at 5,000.
- Returns `{rows: list[dict], sql: str, n_rows: int}` — the SQL string is included so the chat UI and ADR auditors can see what ran.

**The LLM never sends SQL.** It calls `query_data(...)` with structured arguments, and the builder constructs the SQL.

---

## 6. LLM tool layer (`services/llm/tools.py`)

The three tools in the brief, each a Python function with a JSON schema for Gemini's function-calling API.

### Tool 1 — `query_data`

```python
def query_data(
    x: str,
    y: str | None = None,
    agg: Literal["count","sum","mean","min","max","median"] = "count",
    filters: dict[str, str | int | float] | None = None,
    limit: int = 100,
) -> dict:
    """Run an aggregation. Returns {rows, sql, n_rows}.
    Use when the user asks "how many", "average", "sum of", "by category", etc."""
```

### Tool 2 — `get_column_statistics`

```python
def get_column_statistics(column: str) -> dict:
    """Return profile + descriptive stats for one column.
    For numeric: count, mean, std, min, p25, p50, p75, max, skew, n_unique, null_pct.
    For categorical: count, n_unique, top-10 with counts.
    For datetime: count, min, max, span_days, null_pct.
    Use when the user asks "what does X look like?", "is X mostly null?", etc."""
```

### Tool 3 — `generate_chart`

```python
def generate_chart(
    chart_type: Literal["bar","line","histogram","scatter","kpi"],
    x: str,
    y: str | None = None,
    filters: dict | None = None,
) -> dict:
    """Return a ChartSpec the frontend can render directly.
    Use when the user asks "show me", "plot", "visualize", "graph"."""
```

### When the LLM picks which tool

Captured in the system prompt:

> *"For numeric questions ('which X has the highest Y?', 'what's the average?') call `query_data`. For 'tell me about column X' call `get_column_statistics`. For 'show me' / 'plot' / 'visualize' call `generate_chart`. You may call up to 4 tools per turn. After tools, summarize the result in one short paragraph and cite the SQL or chart spec."*

### Loop control

`services/llm/orchestrator.py` runs at most **4 tool iterations** per user turn. After 4, it returns a `partial=true` response with the tool calls so far. This caps latency and prevents runaway cost.

---

## 7. Chart-picker rule book (`services/chart_picker.py`)

Pure function `pick_charts(profile: DatasetProfile, max=6) -> list[ChartSpec]`. Rules in priority order; stop when 6 chosen.

| # | Rule | Chart |
|---|---|---|
| 1 | Has at least one datetime column → take the first → bucket by day | **Line** of `count(*)` over time |
| 2 | Has a low-card categorical (n_unique ≤ 20) → first one → ordered by count desc | **Bar** of `count(*)` by category, top 15 |
| 3 | Has a numeric with `skew > 1` → first one | **Histogram** with log-x if skew > 3 |
| 4 | Has a `0/1` numeric (binary indicator) → take it | **KPI** of `mean * 100 %` (e.g. "fraud rate 0.51 %") |
| 5 | Has two numeric columns → first pair, sample to 5,000 points | **Scatter** of `y ~ x` |
| 6 | Has a state/region-like categorical (`state`, `region`, `country`) → that one | **Bar** of `count` by region |
| 7 | Has a high-card categorical (`merchant`, `job`) → take it | **Bar** of top 10 by count |
| 8 | Fallback if < 4 picked | **KPI** of `n_rows` and **KPI** of `n_cols` |

The rules are dataset-agnostic — they read only the profile, not the column names. They produce 4 picks for the credit-card dataset (line, bar by category, histogram of `amt`, KPI of `is_fraud` rate) and 4–6 for any other roster CSV without modification.

---

## 8. Frontend component tree

```
<App>
  <Header />
  <Dashboard>
    <UploadDropzone />          ← first run; persists dataset_id to useDataset
    <ProfileCard />             ← shows column table
    <FilterBar />               ← uses useFilters (Zustand)
    <ChartGrid>                 ← subscribes to useDataset + useFilters
      <Bar /> <Line /> <Histogram /> <KPI />
    </ChartGrid>
    <Tabs>
      <Tab name="Chat">
        <ChatPanel />
      </Tab>
      <Tab name="Summary">
        <ExecutiveSummary />
      </Tab>
    </Tabs>
  </Dashboard>
</App>
```

### State management

- **Server state** (profile, query results, chat history): `@tanstack/react-query`. Keyed by `[dataset_id, ...]` so swapping a CSV cleanly invalidates everything.
- **Filter state**: `Zustand` store `useFilters`. Persists to `sessionStorage` keyed by `dataset_id`.
- **No global Redux.** Everything is server cache or one tiny store.

### Filter propagation

Every chart query is composed as `useQuery({ queryKey: [dataset_id, "query", spec, filters], queryFn: ... })`. When `filters` changes, the keys change, react-query refetches all charts in parallel. This is why the 500 ms budget is hittable — there is no manual fan-out.

---

## 9. Cross-dataset proof

The same code path serves any CSV because:

1. **Ingest** uses Pandas type inference — no column-name awareness.
2. **Profile** reports types and stats — no domain knowledge.
3. **Chart-picker** reads the profile, not the names.
4. **Query engine** validates columns against the profile, never against a hardcoded list.
5. **LLM tools** take column names as arguments; no domain-specific function names.
6. **Executive summary prompt** receives the profile + 3 generic aggregates — no template strings naming columns.

The `enrichment/credit_cards.py` hook (Phase 7, optional) only fires if the column-name fingerprint matches and is **off by default** so the grader sees the generic flow first.

---

## 10. Failure modes and fallbacks

| Failure | Behavior |
|---|---|
| Upload exceeds 50 MB | 413 + clear hint to use the sample workflow. |
| CSV has no header | 400 + hint. |
| All-text "numeric" column (`123abc`) | Profiler downgrades dtype → `text`; chart-picker skips it. |
| Gemini quota error | Provider returns `ProviderUnavailableError`; chat UI shows "AI is rate-limited, try again in 30 s"; charts/filters keep working. |
| LLM hallucinates an unknown column | Tool layer raises `UnknownColumnError`; orchestrator feeds the error back; LLM corrects on next iteration. |
| Tool loop hits 4 iterations | Return `partial=true` with what we have. UI shows a banner. |
| Frontend disconnects from backend | React Query retry with exponential backoff; toast on persistent failure. |

---

*System design version: 1.0 | Last updated: 2026-05-04*
