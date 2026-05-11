# ADR-003: SQLite Schema Strategy — One Table Per Uploaded Dataset

- **Status:** Accepted
- **Date:** 2026-05-04
- **Deciders:** Zaman + project partner
- **Supersedes:** —

---

## Context

DataLens accepts **arbitrary CSVs** with arbitrary column names and types. Two CSVs uploaded back-to-back may share zero columns. We need a SQLite layout that:

1. Lets the LLM tools issue normal `SELECT col FROM table WHERE …` queries — not joins through an attribute table.
2. Cleanly replaces the active dataset when the user uploads a new file (no row-level deletes that take seconds).
3. Stays simple enough for a 3-week project with two students.
4. Makes the column-validation guard for the safe query builder trivial.

## Options considered

### Option A — Per-dataset dynamic table (chosen)

```sql
CREATE TABLE dataset_01HX… (col1 TYPE, col2 TYPE, …);
```

A separate physical table per upload, named by the dataset's ULID, with columns inferred from the CSV.

### Option B — Single wide entity-attribute-value (EAV) table

```sql
CREATE TABLE rows (
  dataset_id TEXT, row_idx INT, col_name TEXT, val_text TEXT, val_num REAL, val_dt DATETIME
);
```

Every cell is a row. Generic schema, no DDL after install.

### Option C — Single fixed-shape "facts" table with a JSON blob per row

```sql
CREATE TABLE rows (dataset_id TEXT, row_idx INT, payload_json TEXT);
```

Use `json_extract()` for queries.

### Option D — DuckDB embedded

Replace SQLite with DuckDB; columnar, vectorized, much faster for analytical queries.

## Comparison

| Criterion | A — per-dataset table | B — EAV | C — JSON blob | D — DuckDB |
|---|---|---|---|---|
| Query speed on 50k × 20 cols | Fastest (native columns) | Slow (huge joins) | Slow (`json_extract`) | Fastest |
| LLM tool ergonomics | Best (`SELECT amt FROM dataset_x`) | Hostile (3-way self-join) | Workable but ugly | Best |
| Drop-old-dataset cost | `DROP TABLE` — instant | `DELETE FROM rows WHERE dataset_id=?` — slow on large rows | same as B | instant |
| Type fidelity | Native (INTEGER, REAL, TEXT, TIMESTAMP) | Loses types | Loses types | Native |
| Course rubric compliance | ✅ SQLite | ✅ SQLite | ✅ SQLite | ❌ deviation |
| Extra dependency | None | None | None | DuckDB binary |

## Decision

**Option A — one physical table per uploaded dataset**, named `dataset_<ulid>`. A catalog table `datasets(id, original_filename, n_rows, n_cols, column_meta_json, created_at)` tracks them.

This is unconventional in production (you'd never let users mint tables in a real warehouse), but it fits the brief: each dataset is short-lived, lives in a single-user local SQLite file, and the LLM-facing query surface stays clean.

## Trade-offs

- **DDL on user upload.** SQLite handles this fine; no `ALTER TABLE` in the hot path. Mitigated by ULID-named tables that never collide.
- **Catalog can drift from physical tables.** Mitigated: ingest is wrapped in a transaction; if the table create fails the catalog row rolls back.
- **Cleanup needs cron-like logic.** A "delete dataset" endpoint runs `DROP TABLE dataset_<id>` + `DELETE FROM datasets WHERE id=?`. Old dev datasets stay until manually wiped — acceptable for a 3-week MVP.
- **Cannot share columns across datasets in one query.** Out of scope per SPEC §9.

## Consequences

- `db/schema.py` ships with the catalog table only; per-dataset tables are created in `services/ingest.py`.
- Column names are sanitized to a "safe name" before being used in DDL (lowercase, alnum + underscore). The original "display name" is kept in `column_meta_json` and used in the UI.
- The safe query builder validates `x`, `y`, and filter keys against `column_meta_json[id]` before composing SQL. An unknown column → 400, never reaches the database.
- The `chat_messages` table lives in the catalog DB and holds chat history per `(dataset_id, conversation_id)`.

## Revisit conditions

- If we ever want cross-dataset analytics → swap to DuckDB and amend this ADR. The query engine is the only file that would change.
- If the per-dataset table count exceeds ~500 (unlikely in a course project) → consider an LRU eviction job.
