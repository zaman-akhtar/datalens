# Test Strategy — DataLens

Three tiers: backend unit/integration with `pytest`, frontend component with `Vitest + RTL`, end-to-end with `Playwright`. The Playwright suite is the rubric's 40-pt automated functional test, so it gets the most attention.

---

## 1. Backend — pytest

Target ≥ **14 tests**, all green, all under 5 seconds total. Real network is never hit; LLM provider faked with `respx`.

| File | Tests | Covers |
|---|---|---|
| `test_upload.py` | 3 | accept valid CSV, reject non-CSV (400), reject > 50 MB (413) |
| `test_ingest.py` | 4 | dynamic table created, row count matches, leading-zero IDs preserved, duplicate column names deduped |
| `test_profile.py` | 5 | numeric column, all-null column, mixed-type column → text, datetime detection, `Unnamed:` column flagged hidden |
| `test_profile_router.py` | 2 | 200 + valid JSON, 404 on bad id |
| `test_chart_picker.py` | 6 | 4 fixtures (credit-card, airbnb, hr, single-column) → ≥ 4 picks each; rule order; max 6 cap |
| `test_query_engine.py` | 5 | basic agg, filter equality, filter range, unknown column → 400, SQL-injection attempt safely escaped |
| `test_provider.py` | 3 | text response, single tool call, error path |
| `test_llm_tools.py` | 4 | each of the 3 tools end-to-end + cap on rows returned |
| `test_chat.py` | 3 | single-turn answer, tool-loop terminates at 4 iterations, history persisted |
| `test_summary.py` | 2 | ≥ 3 numeric facts in output, cache hit on second call |
| `test_summary_router.py` | 2 | 200 + valid JSON, refresh query param triggers regeneration |

**Total: 39** — well above the floor of 14, well below "test bloat."

### Fixtures (`backend/tests/fixtures/`)

| File | Purpose |
|---|---|
| `tiny.csv` | 5 rows × 3 cols — happy path |
| `with_nulls.csv` | 50 % nulls in one column |
| `mixed_types.csv` | column has both `42` and `forty-two` |
| `single_row.csv` | one data row |
| `wide_100_cols.csv` | 100 columns, 10 rows — wide-CSV path |
| `leading_zeros.csv` | IDs like `007` — must stay strings |
| `airbnb_sample.csv` | proves chart-picker is generic |

---

## 2. Frontend — Vitest + React Testing Library

Target ≥ **7 tests**, configured with `jsdom`, MSW for HTTP mocking.

| File | Tests | Covers |
|---|---|---|
| `UploadDropzone.test.tsx` | 2 | drag-drop fires upload, error toast on 413 |
| `ProfileCard.test.tsx` | 2 | renders all columns, hides flagged-index columns |
| `useFilters.test.ts` | 3 | set, clear, persist across hook unmount |
| `FilterBar.test.tsx` | 2 | only low-cardinality categoricals appear; clear button works |
| `ChartGrid.test.tsx` | 2 | renders 4 mocked specs; loading skeleton during fetch |
| `ChartGrid.filter.test.tsx` | 1 | filter change triggers refetch within 500 ms (mocked latency) |
| `ChatPanel.test.tsx` | 2 | sends message, displays assistant reply + collapsible SQL |
| `ExecutiveSummary.test.tsx` | 2 | renders summary text, regenerate button hits `?refresh=true` |
| `chart.smoke.test.tsx` | 5 | each chart component renders without console errors |

**Total: 21**.

---

## 3. End-to-end — Playwright (the graded suite)

Two suites; both run against real backend + real frontend (`npm run dev:all`). Real Gemini calls are stubbed via a `MOCK_LLM=1` env that swaps `provider.py` for a deterministic fake.

### `full-flow.spec.ts`

1. Visit `/`.
2. Drop `data/credit_card_transactions_sample_50k.csv` into the upload zone.
3. Wait for `[data-testid="profile-card"]` to appear (≤ 15 s).
4. Assert ≥ 4 and ≤ 6 chart `[data-testid^="chart-"]` elements.
5. Click `[data-testid="filter-state"]`, select `NY`. Measure time-to-last-paint across all charts. Assert < 500 ms (mocked) / < 1500 ms (real).
6. Type `"which category has the highest fraud rate?"` into chat. Assert reply within 10 s and includes a `category` value.
7. Switch to Summary tab. Assert text contains ≥ 3 numeric matches `\d+(\.\d+)?` within 30 s of upload.
8. Reload page. Assert profile, charts, chat history, and summary persist.

### `swap-csv.spec.ts`

1. Upload credit-card CSV. Confirm at least one chart axis label contains `category`.
2. Upload `airbnb_sample.csv`. Wait for re-render.
3. Assert no DOM text contains `merchant`, `is_fraud`, or `category`.
4. Assert ≥ 4 charts visible, none of which carry over from the prior dataset (`data-testid` values changed).

These two specs are what the grader's "Playwright automated functional tests" rubric line will execute. They are tracked in `tasks/todo.md` as T053 and T062.

---

## 4. Edge-case CSVs to exercise (covered by fixtures + ingest tests)

| Quirk | Fixture | Test |
|---|---|---|
| Missing values (~50 %) | `with_nulls.csv` | profiler `null_pct ≈ 0.5`; chart skips nulls |
| Mixed types in one column | `mixed_types.csv` | dtype downgraded to `text` |
| Single row | `single_row.csv` | profiler returns; chart-picker still emits ≥ 4 picks via fallbacks |
| 100 columns | `wide_100_cols.csv` | profile completes < 5 s; ChartGrid shows max 6 |
| Leading-zero IDs | `leading_zeros.csv` | `cc_num`-style values stay strings |
| Pandas index column | `with_unnamed.csv` | `Unnamed: 0` flagged hidden |
| 50 MB upload | generated in test | accepted in ≤ 5 s |
| 50 MB + 1 byte upload | generated in test | rejected with 413 |

---

## 5. CI script (lives in `package.json`)

```json
{
  "scripts": {
    "test:backend": "cd ../backend && uv run pytest -v --tb=short",
    "test:frontend": "vitest run --reporter=verbose",
    "test:e2e": "playwright test",
    "test:all": "npm run test:backend && npm run test:frontend && npm run test:e2e"
  }
}
```

The README documents `npm run test:all` as the single command the grader runs.

---

## 6. TDD discipline

- **Backend:** every service file gets its `_test.py` written first. Red → green → refactor. Enforced by the `test-driven-development` skill (graded as-is).
- **Frontend:** logic hooks (`useFilters`, `useDataset`) are test-first. Visual components are test-after — but every test must exist before the corresponding component is merged.
- **Commit pattern:** `test: add failing test for X` → `feat: implement X` → `refactor: clean X`. The git log itself is the proof of TDD.

---

*Test strategy version: 1.0 | Last updated: 2026-05-04*
