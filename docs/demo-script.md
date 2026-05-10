# DataLens — 5-Minute Live Demo Script

**Dataset:** `data/credit_card_transactions_sample_50k.csv` (50k rows, 14 MB)  
**Mode:** `MOCK_LLM=1` for rehearsal; set `MOCK_LLM=0` (or remove) for live demo with real Gemini.  
**Before you start:** Run `npm run dev:all` from the project root so both servers are up.

---

## Segment 1 — Upload & Profile (0:00 – 1:00)

**Action:** Drag `credit_card_transactions_sample_50k.csv` onto the dropzone (or click "Choose a file").

**Say:**
> "DataLens accepts any CSV. No schema configuration, no mapping wizards — just drop the file and the system profiles every column automatically."

**Point out:**
- Column types detected (datetime, categorical, numeric, boolean).
- Null percentage and cardinality for each column.
- `is_fraud` flagged as boolean (0/1 positive-rate indicator).

**Talking point:** *The profiler runs in under 2 seconds on 50k rows because it reads directly from SQLite — no ORM overhead.*

---

## Segment 2 — Auto-Dashboard (1:00 – 2:15)

**Action:** Scroll down to the chart grid (4–6 charts render automatically).

**Say:**
> "The chart-picker is a pure rule-book function — it reads only the column profile, not the data. Datetime columns become line charts, low-cardinality categoricals become bar charts, skewed numerics become histograms, and the 0/1 fraud column becomes a KPI tile."

**Point out:**
- Time-series line chart (`trans_date_trans_time`).
- Bar chart by `category` (14 categories, nicely readable).
- `amt` histogram with a clear right tail (skew > 1 was the trigger).
- `is_fraud` KPI tile showing the positive rate (~0.5%).

**Talking point:** *Every chart spec is deterministic — we can unit test it without touching a database. The 6-test suite in `test_chart_picker.py` verifies both the credit-card and Airbnb fixtures.*

---

## Segment 3 — Global Filters (2:15 – 3:00)

**Action:** Click one of the category dropdowns in the FilterBar (e.g. pick `grocery_pos`). All charts update.

**Say:**
> "Filters are global state stored in Zustand and persisted to sessionStorage. Every chart re-queries with the same filter dict — one store, one source of truth."

**Point out:**
- All charts re-render within ~500 ms.
- The KPI fraud rate changes as the category changes.
- Click "Clear" to reset — charts return to full-dataset view.

**Talking point:** *The filter dict is passed as parametrized SQL `WHERE` clauses — column names are whitelisted against the profile, so injection is structurally impossible.*

---

## Segment 4 — LLM Chat (3:00 – 4:00)

**Action:** Type in the chat box: *"Which category has the highest fraud rate?"* → Send.

**Say:**
> "The chat interface uses Gemini 1.5 Flash with a three-tool agentic loop: `query_data`, `get_column_statistics`, and `generate_chart`. The model picks which tool to call, we execute it against SQLite, feed the result back, and the model synthesizes a grounded answer."

**Point out:**
- The answer appears with a "Ran SQL" collapsible showing the actual query.
- Try a second question: *"Show me the average transaction amount by state."*
- The loop is capped at 4 tool calls per turn (hard stop, no runaway loops).

**Talking point:** *The tool layer is three thin wrapper functions — the business logic already exists in the query engine and profiler. Adding LLM capability was less than 150 lines.*

---

## Segment 5 — Executive Summary (4:00 – 5:00)

**Action:** Scroll to the Executive Summary section (loads automatically after upload).

**Say:**
> "The summary prompt is fed only the column profile and three canned aggregates — top categories, mean transaction amount, and the fraud rate. Gemini writes a manager-ready paragraph with at least three numeric facts."

**Point out:**
- Numbers are specific (row counts, percentages, averages) — not vague.
- Click "Regenerate" to get a fresh version.
- Click "Copy" to paste into a slide or email.

**Talking point:** *The Playwright test asserts `≥ 3 numeric facts` using a regex — so if the prompt ever drifts, a failing test catches it before demo day.*

---

## Closing (5:00)

**Say:**
> "Everything you saw — upload, profile, charts, filters, chat, summary — is driven by a single 50k-row SQLite table. There's no data lake, no external warehouse. The system is designed to work on a laptop, which is the right scope for a business analyst's ad hoc dataset."

---

## Rehearsal Checklist

- [ ] Both servers running (`npm run dev:all` from project root).
- [ ] `.env` has `MOCK_LLM=1` for rehearsal (deterministic, no API quota risk).
- [ ] `data/credit_card_transactions_sample_50k.csv` is in the `data/` directory.
- [ ] Cleared browser localStorage/sessionStorage before each run.
- [ ] Have a second CSV ready (e.g. Airbnb) for the "swap dataset" bonus demo if Q&A goes long.

## Live Demo Mode

Set `MOCK_LLM=0` (or remove the line from `.env`) and ensure `GEMINI_API_KEY` is populated. The mock provider is replaced by Gemini 1.5 Flash — behavior is identical, answers are real.
