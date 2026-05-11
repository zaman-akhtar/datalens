# Dataset Analysis — Credit Card Transactions

> Dataset 6 of the DataLens roster. This analysis is the empirical foundation for SPEC.md, the chart auto-selection logic, the LLM tool layer, and the executive-summary prompt. **DataLens itself must remain dataset-agnostic** — anything dataset-specific lives in this document or in seed prompts, never hardcoded into application logic.

---

## 1. File facts

| Property | Value |
|---|---|
| Source | Kaggle — `priyamchoksi/credit-card-transactions-dataset` |
| Filename in repo | `data/credit_card_transactions_sample_50k.csv` (dev sample) |
| Full file size | ~338 MB / 1,296,675 rows + 1 header row |
| Dev sample size | 50,000 rows (~14 MB) — used during local development |
| Time range | 2019-01-01 → 2020-12-31 (per Kaggle metadata) |
| License | Kaggle Public |

**Why a sample:** the full file exceeds the 50 MB upload cap defined in SPEC §8 and would slow every iteration. The 50k sample preserves the column distribution and ~0.5 % fraud rate. Full-file behavior is exercised in a single Playwright load test, not in unit tests.

---

## 2. Actual columns (verified from the file header)

The CSV header is **wider than the project brief**. The brief omits five real columns that the actual file contains. We treat the file as the source of truth.

| # | Column | Inferred type | Notes |
|---|---|---|---|
| 0 | `Unnamed: 0` | int (row index) | Pandas-export artifact. Drop on ingest. |
| 1 | `trans_date_trans_time` | datetime | Format `YYYY-MM-DD HH:MM:SS`. Parse on ingest. |
| 2 | `cc_num` | int / string | Treat as string — leading zeros / loss of precision risk. |
| 3 | `merchant` | string | Prefixed `fraud_` for **every** row, not just fraud. Strip prefix on ingest. |
| 4 | `category` | string (categorical) | 14 values e.g. `grocery_pos`, `gas_transport`, `misc_net`. |
| 5 | `amt` | float | Transaction amount in USD. Heavy right-skew. |
| 6 | `first` | string | Synthetic first name. PII-shaped but fake. |
| 7 | `last` | string | Synthetic last name. |
| 8 | `gender` | string | `M` / `F`. |
| 9 | `street` | string | **Not in brief.** Synthetic street. |
| 10 | `city` | string | Cardholder city. |
| 11 | `state` | string | 2-letter US state code. |
| 12 | `zip` | int | **Not in brief.** Cardholder ZIP. |
| 13 | `lat` | float | Cardholder latitude. |
| 14 | `long` | float | Cardholder longitude. |
| 15 | `city_pop` | int | Cardholder city population. |
| 16 | `job` | string | Cardholder job title (~500 distinct values). |
| 17 | `dob` | date | Cardholder date of birth. |
| 18 | `trans_num` | string | **Not in brief.** Transaction UUID. Useful as primary key. |
| 19 | `unix_time` | int | **Not in brief.** Redundant with `trans_date_trans_time`. |
| 20 | `merch_lat` | float | Merchant latitude. |
| 21 | `merch_long` | float | Merchant longitude. |
| 22 | `is_fraud` | int (0/1) | **Target label.** Imbalanced — ~0.5 %. |
| 23 | `merch_zipcode` | float (nullable) | **Not in brief.** Merchant ZIP, ~15 % null. |

### Implications for the generic profiler
The profiler must (a) detect and ignore the unnamed index column generically — i.e. treat any column matching `^Unnamed:` as a row index — and (b) cope with mixed-null numeric columns like `merch_zipcode`. Both are common Pandas-export artifacts and should be handled in the dataset-agnostic ingest layer, not via a hardcoded rule for this CSV.

---

## 3. Derived features (computed at ingest time)

These are **not** added to the application logic generically. They are added by an optional, dataset-aware **enrichment hook** that runs only if the upload looks like this dataset (column-name fingerprint match). Listed here so the chat tool layer and the executive summary can reference them.

| Derived column | Formula | Rationale |
|---|---|---|
| `hour_of_day` | `trans_date_trans_time.dt.hour` | Sample question 4 (volume by hour). |
| `day_of_week` | `trans_date_trans_time.dt.day_name()` | Spending pattern analysis. |
| `month` | `trans_date_trans_time.dt.to_period('M')` | Trend lines. |
| `age_at_txn` | `(trans_date_trans_time - dob).years` | Demographics without using names. |
| `dist_km` | Haversine(lat,long ↔ merch_lat,merch_long) | Anomaly proxy — fraud often at unusual distance. |
| `amt_log` | `log1p(amt)` | Charts of skewed amounts. |

---

## 4. Candidate user questions (seeds the LLM tool router and executive summary)

The five **brief-supplied** questions are the floor; we extend with five more that the dataset clearly supports.

1. What is the total transaction volume by category? *(brief)*
2. What is the fraud rate, and how does it vary by category? *(brief)*
3. What is the average transaction amount by state? *(brief)*
4. How does transaction volume change by hour of day? *(brief)*
5. Which merchant categories have the highest fraud rates? *(brief)*
6. How does fraud rate vary by hour of day or day of week?
7. What is the distribution of transaction amounts (overall and by category)?
8. Which states contribute the most fraudulent dollars?
9. Are fraudulent transactions geographically further from the cardholder?
10. Does fraud rate vary by cardholder age bucket or gender?

Each of these must be answerable through the three LLM tools (`query_data`, `get_column_statistics`, `generate_chart`) without writing new endpoints — that is the litmus test for the tool design in `system-design.md`.

---

## 5. Edge cases and quirks

| Quirk | Impact | Mitigation |
|---|---|---|
| **Class imbalance**: ~0.5 % fraud | Naive averages mask fraud signal | Default chart for `is_fraud` is **rate**, not count; chat tool offers `aggregation="mean"` on 0/1. |
| **`merchant` always prefixed `fraud_`** | Misleading for the LLM | Strip prefix in ingest; surface this in the executive summary. |
| **`cc_num` as int** | JS precision loss past 2^53 | Cast to string on ingest. |
| **`merch_zipcode` ~15 % null** | Profiler must handle nullable numerics | Profiler reports null pct; charts must skip nulls without crashing. |
| **`Unnamed: 0` index column** | Looks like a numeric variable | Generic rule in profiler: skip columns matching `^Unnamed:` and any column where `nunique == nrows`. |
| **High-cardinality `merchant`, `job`, `city`** | Bar charts become unreadable | Auto-select logic caps categorical bars at top-N (default 15) with an "Other" bucket. |
| **Heavy right-skew on `amt`** | Linear bar charts squash values | Default to log-scaled axis when skew > 3 (Fisher-Pearson). |
| **Two-year span, weekly seasonality, holiday spikes** | Misleading line charts if not bucketed | Time series default bucket = day; agent picks week/month for ranges > 60 days. |
| **Synthetic PII** | Looks real, isn't | Document in README; never ship as a "real demo" claim. |

---

## 6. What this means for the generic application

DataLens cannot have any of the following hardcoded:

- Column names like `is_fraud` or `category`
- The string `fraud_` as a prefix to strip
- The 14 known categories
- The 0.5 % fraud rate as an assumption

What it **can** have:

- A profiler that reports types, nulls, cardinality, skew, and min/max for each column.
- A chart-selection rule book that takes profiler output and emits 4–6 (chart_type, x, y) tuples.
- Three LLM tools that operate on the loaded SQLite table by column name and aggregation type.
- A dataset-aware **enrichment hook** mechanism (optional — the hook for this CSV strips `fraud_`, derives `hour_of_day`, etc., but only fires when the column-name fingerprint matches).

This separation is what lets the same codebase serve a different team's hotel-booking dataset without a single code change.

---

*Dataset analysis version: 1.0 | Last updated: 2026-05-04*
