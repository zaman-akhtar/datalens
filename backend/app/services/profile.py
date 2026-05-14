"""Dataset profiling — translates a catalog row + the live table into a DatasetProfile."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime

import pandas as pd

from app.config import get_settings
from app.models.dataset import ColumnProfile, DatasetProfile, DatasetSummary, DType

# Keyed by (db_path, dataset_id); datasets are immutable after ingest so this is safe.
_profile_cache: dict[tuple[str, str], DatasetProfile] = {}

# Read at most this many rows into pandas for distribution stats (mean/skew/sample).
# n_unique is fetched accurately from the full table via SQL separately.
_PROFILE_SAMPLE = 10_000


class DatasetNotFoundError(KeyError):
    """Raised when the dataset id has no catalog row."""


def _classify_dtype(series: pd.Series, n_unique: int, total_rows: int) -> DType:
    """Profiler's view of the column type — independent of the storage dtype."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_numeric_dtype(series):
        # Treat 0/1 numeric as boolean if cardinality ≤ 2
        if series.dropna().isin([0, 1]).all() and n_unique <= 2:
            return "boolean"
        return "numeric"
    # object — categorical if low cardinality relative to the full dataset
    if total_rows > 0 and (n_unique <= 50 or (n_unique / total_rows) < 0.05):
        return "categorical"
    return "text"


def _safe_value(v):  # noqa: ANN001, ANN202
    """Make a Pandas value JSON-serializable for sample_values."""
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(v, (int, float, bool, str)):
        return v
    if isinstance(v, pd.Timestamp):
        return v.isoformat()
    return str(v)


def _profile_column(
    name: str,
    safe_name: str,
    series: pd.Series,
    is_index: bool,
    n_unique: int,
    total_rows: int,
) -> ColumnProfile:
    n = len(series)
    null_pct = float(series.isna().mean()) if n else 0.0
    dtype = _classify_dtype(series, n_unique, total_rows)
    sample_values = [_safe_value(v) for v in series.dropna().head(5).tolist()]

    cmin = cmax = cmean = cskew = None
    if dtype in ("numeric", "boolean"):
        try:
            cmin = float(series.min())
            cmax = float(series.max())
            cmean = float(series.mean())
            if n_unique > 1:
                cskew = float(series.skew())
        except (TypeError, ValueError):
            pass

    return ColumnProfile(
        name=name,
        safe_name=safe_name,
        dtype=dtype,
        null_pct=round(null_pct, 4),
        n_unique=n_unique,
        sample_values=sample_values,
        is_index=is_index,
        min=cmin,
        max=cmax,
        mean=cmean,
        skew=cskew,
    )


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _sql_n_unique(conn: sqlite3.Connection, table: str, safe_names: list[str]) -> dict[str, int]:
    """One-pass COUNT(DISTINCT) for all columns — accurate even when pandas uses a sample."""
    if not safe_names:
        return {}
    select = ", ".join(f"COUNT(DISTINCT {_quote(s)})" for s in safe_names)
    try:
        row = conn.execute(f"SELECT {select} FROM {_quote(table)}").fetchone()
        return {safe_names[i]: int(row[i]) for i in range(len(safe_names))}
    except Exception:  # noqa: BLE001
        return {}


def _load_catalog_row(conn: sqlite3.Connection, dataset_id: str) -> sqlite3.Row:
    try:
        row = conn.execute("SELECT * FROM datasets WHERE id = ?", (dataset_id,)).fetchone()
    except sqlite3.OperationalError as e:
        raise DatasetNotFoundError(dataset_id) from e
    if row is None:
        raise DatasetNotFoundError(dataset_id)
    return row


def list_datasets(conn: sqlite3.Connection) -> list[DatasetSummary]:
    try:
        rows = conn.execute(
            "SELECT id, original_filename, n_rows, n_cols, created_at FROM datasets ORDER BY created_at DESC"
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    return [
        DatasetSummary(
            dataset_id=r["id"],
            original_filename=r["original_filename"],
            n_rows=r["n_rows"],
            n_cols=r["n_cols"],
            created_at=_parse_ts(r["created_at"]),
        )
        for r in rows
    ]


def _parse_ts(v) -> datetime:  # noqa: ANN001
    if isinstance(v, datetime):
        return v
    return datetime.fromisoformat(str(v).replace(" ", "T"))


def build_profile(conn: sqlite3.Connection, dataset_id: str) -> DatasetProfile:
    """Profile a previously-ingested dataset."""
    key = (str(get_settings().db_path), dataset_id)
    if key in _profile_cache:
        return _profile_cache[key]

    row = _load_catalog_row(conn, dataset_id)
    table = row["table_name"]
    column_meta = json.loads(row["column_meta_json"])
    total_rows: int = row["n_rows"]

    # Sample pandas read for distribution stats — fast even for large tables.
    sample_sql = (
        f'SELECT * FROM {_quote(table)} LIMIT {_PROFILE_SAMPLE}'
        if total_rows > _PROFILE_SAMPLE
        else f'SELECT * FROM {_quote(table)}'
    )
    df = pd.read_sql_query(sample_sql, conn)
    for meta in column_meta:
        safe = meta["safe_name"]
        if safe in df.columns and "datetime" in meta["pandas_dtype"]:
            df[safe] = pd.to_datetime(df[safe], errors="coerce")

    # Accurate n_unique from the full table — one SQL scan, all columns.
    present_safe = [m["safe_name"] for m in column_meta if m["safe_name"] in df.columns]
    n_unique_map = _sql_n_unique(conn, table, present_safe)

    columns: list[ColumnProfile] = []
    for meta in column_meta:
        safe = meta["safe_name"]
        if safe not in df.columns:
            continue
        n_unique = n_unique_map.get(safe, int(df[safe].nunique(dropna=True)))
        columns.append(
            _profile_column(
                name=meta["name"],
                safe_name=safe,
                series=df[safe],
                is_index=bool(meta.get("is_index", False)),
                n_unique=n_unique,
                total_rows=total_rows,
            )
        )

    profile = DatasetProfile(
        dataset_id=dataset_id,
        original_filename=row["original_filename"],
        n_rows=row["n_rows"],
        n_cols=row["n_cols"],
        columns=columns,
        created_at=_parse_ts(row["created_at"]),
    )
    _profile_cache[key] = profile
    return profile


def get_safe_name_map(conn: sqlite3.Connection, dataset_id: str) -> dict[str, str]:
    row = _load_catalog_row(conn, dataset_id)
    column_meta = json.loads(row["column_meta_json"])
    out: dict[str, str] = {}
    for m in column_meta:
        out[m["name"]] = m["safe_name"]
        out[m["safe_name"]] = m["safe_name"]
    return out


def get_table_name(conn: sqlite3.Connection, dataset_id: str) -> str:
    return _load_catalog_row(conn, dataset_id)["table_name"]


def get_column_profile(
    conn: sqlite3.Connection, dataset_id: str, column: str
) -> ColumnProfile | None:
    """Look up a single column profile by display or safe name."""
    profile = build_profile(conn, dataset_id)
    for c in profile.columns:
        if c.name == column or c.safe_name == column:
            return c
    return None
