"""CSV → SQLite ingestion (Phase 2 / ADR-003).

Steps:
1. Read CSV with Pandas; coerce datetime-looking columns.
2. Sanitize column names → unique snake_case.
3. Flag any `Unnamed:` index columns or unique-id columns as `is_index`.
4. Write to a per-dataset table `dataset_<id>`.
5. Insert a row in the `datasets` catalog with column metadata.
"""
from __future__ import annotations

import json
import re
import sqlite3
import uuid
from io import BytesIO
from pathlib import Path

import pandas as pd

from app.db.schema import init_schema


def _new_dataset_id() -> str:
    """Short opaque ID. Not a real ULID, just unique enough for a course project."""
    return uuid.uuid4().hex[:16]


def _sanitize(name: str) -> str:
    """Lowercase, collapse non-alphanumerics to underscore."""
    safe = re.sub(r"[^0-9a-zA-Z]+", "_", name).strip("_").lower()
    if not safe:
        safe = "col"
    if safe[0].isdigit():
        safe = f"c_{safe}"
    return safe


def _dedupe(names: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    out: list[str] = []
    for n in names:
        if n in seen:
            seen[n] += 1
            out.append(f"{n}_{seen[n]}")
        else:
            seen[n] = 1
            out.append(n)
    return out


def _looks_like_datetime(series: pd.Series) -> bool:
    """Cheap regex check on first 100 non-null values."""
    sample = series.dropna().astype(str).head(100)
    if sample.empty:
        return False
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2})?)?$|^\d{1,2}/\d{1,2}/\d{2,4}")
    matches = sample.str.match(pattern).sum()
    return matches >= len(sample) * 0.8


def _coerce_datetimes(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        # pandas 3.x uses StringDtype whose str() is "str" or "string"; legacy uses "object"
        if str(df[col].dtype) in ("object", "str", "string") and _looks_like_datetime(df[col]):
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def _is_unique_id(series: pd.Series) -> bool:
    """A column where every row is unique is almost certainly an ID, not a feature."""
    n = len(series)
    if n == 0:
        return False
    return series.nunique(dropna=True) == n


def _build_column_meta(df: pd.DataFrame, safe_names: list[str]) -> list[dict]:
    """Lightweight metadata stored in the catalog. Profiling is separate."""
    meta = []
    for orig, safe in zip(df.columns, safe_names, strict=True):
        col = df[orig]
        is_unnamed = orig.startswith("Unnamed:")
        is_unique = _is_unique_id(col) and pd.api.types.is_integer_dtype(col)
        meta.append(
            {
                "name": orig,
                "safe_name": safe,
                "pandas_dtype": str(col.dtype),
                "is_index": is_unnamed or is_unique,
            }
        )
    return meta


def _insert_catalog_row(
    conn: sqlite3.Connection,
    dataset_id: str,
    original_filename: str,
    table_name: str,
    n_rows: int,
    n_cols: int,
    column_meta: list[dict],
) -> None:
    conn.execute(
        """
        INSERT INTO datasets (id, original_filename, table_name, n_rows, n_cols, column_meta_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            dataset_id,
            original_filename,
            table_name,
            n_rows,
            n_cols,
            json.dumps(column_meta),
        ),
    )


_MAX_ROWS = 150_000


def ingest_csv(
    conn: sqlite3.Connection,
    csv_bytes: bytes,
    original_filename: str,
) -> tuple[str, int, int, int | None]:
    """Ingest CSV bytes into SQLite. Returns (dataset_id, n_rows, n_cols, sampled_from).

    sampled_from is the original row count when the file was automatically sampled;
    None when the full file is loaded. Raises ValueError on parse failure.
    """
    init_schema(conn)

    try:
        df = pd.read_csv(BytesIO(csv_bytes), low_memory=False, na_values=["", "NA", "N/A"])
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"Could not parse CSV: {e}") from e

    if df.shape[1] == 0:
        raise ValueError("CSV has no columns")

    sampled_from: int | None = None
    if len(df) > _MAX_ROWS:
        sampled_from = len(df)
        df = df.sample(n=_MAX_ROWS, random_state=42).reset_index(drop=True)

    df = _coerce_datetimes(df)

    safe_names = _dedupe([_sanitize(str(c)) for c in df.columns])
    column_meta = _build_column_meta(df, safe_names)

    dataset_id = _new_dataset_id()
    table_name = f"dataset_{dataset_id}"

    df_renamed = df.copy()
    df_renamed.columns = safe_names

    df_renamed.to_sql(table_name, conn, index=False, if_exists="replace")

    _insert_catalog_row(
        conn,
        dataset_id=dataset_id,
        original_filename=original_filename,
        table_name=table_name,
        n_rows=int(df.shape[0]),
        n_cols=int(df.shape[1]),
        column_meta=column_meta,
    )

    return dataset_id, int(df.shape[0]), int(df.shape[1]), sampled_from


def ingest_csv_path(conn: sqlite3.Connection, csv_path: Path) -> tuple[str, int, int]:
    """Convenience wrapper for tests — drops the sampled_from 4th element."""
    dataset_id, n_rows, n_cols, _ = ingest_csv(conn, csv_path.read_bytes(), csv_path.name)
    return dataset_id, n_rows, n_cols
