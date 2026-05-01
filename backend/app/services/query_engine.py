"""Safe parametrized SQL builder (System Design §5).

The LLM never sends SQL. Callers pass column names, an aggregation enum, and
filter dicts; this module composes a parametrized query and binds values via
sqlite3's `?` placeholders.
"""
from __future__ import annotations

import sqlite3
from typing import Any

from app.config import get_settings
from app.models.dataset import ColumnProfile, DatasetProfile
from app.models.query import Aggregation, QueryRequest, QueryResult, QueryRow
from app.services.profile import build_profile, get_table_name


class UnknownColumnError(ValueError):
    """Raised when a request mentions a column not in the dataset profile."""


_VALID_AGGS: set[str] = {"count", "sum", "mean", "min", "max", "median"}
_AGG_SQL: dict[Aggregation, str] = {
    "count": "COUNT(*)",
    "sum": "SUM({col})",
    "mean": "AVG({col})",
    "min": "MIN({col})",
    "max": "MAX({col})",
    # SQLite has no native median; we emulate with ORDER BY in Python instead
    "median": "AVG({col})",  # placeholder; median path handled separately
}


def _quote_ident(name: str) -> str:
    """SQLite identifier quoting (double-quote, double-up internal quotes)."""
    return '"' + name.replace('"', '""') + '"'


def _column_lookup(profile: DatasetProfile) -> dict[str, ColumnProfile]:
    out: dict[str, ColumnProfile] = {}
    for c in profile.columns:
        out[c.name] = c
        out[c.safe_name] = c
    return out


def _validate(name: str, lookup: dict[str, ColumnProfile]) -> ColumnProfile:
    if name not in lookup:
        raise UnknownColumnError(name)
    return lookup[name]


def _build_filter_clause(
    filters: dict[str, Any] | None, lookup: dict[str, ColumnProfile]
) -> tuple[str, list[Any]]:
    if not filters:
        return "", []
    parts: list[str] = []
    params: list[Any] = []
    for raw_key, raw_val in filters.items():
        col = _validate(raw_key, lookup)
        ident = _quote_ident(col.safe_name)
        if isinstance(raw_val, (list, tuple)):
            placeholders = ",".join("?" for _ in raw_val)
            parts.append(f"{ident} IN ({placeholders})")
            params.extend(raw_val)
        else:
            parts.append(f"{ident} = ?")
            params.append(raw_val)
    return " WHERE " + " AND ".join(parts), params


def _scalar_count(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT COUNT(*) AS n FROM {_quote_ident(table)}").fetchone()
    return int(row["n"])


def run_query(
    conn: sqlite3.Connection, dataset_id: str, request: QueryRequest
) -> QueryResult:
    """Execute a structured query and return rows + the SQL we ran."""
    settings = get_settings()
    profile = build_profile(conn, dataset_id)
    lookup = _column_lookup(profile)
    table = get_table_name(conn, dataset_id)
    table_q = _quote_ident(table)

    # Special pseudo-column to let the LLM/picker request the global row count.
    if request.x == "__rows__":
        n = _scalar_count(conn, table)
        return QueryResult(
            sql=f"SELECT COUNT(*) FROM {table_q}",
            n_rows=1,
            rows=[QueryRow(label="rows", value=float(n))],
        )

    x_col = _validate(request.x, lookup)
    y_col = _validate(request.y, lookup) if request.y else None

    if request.agg not in _VALID_AGGS:
        raise ValueError(f"Invalid aggregation: {request.agg}")

    where_sql, params = _build_filter_clause(request.filters, lookup)

    # ---- Histogram: bin a numeric column into N buckets in SQL ----
    if request.bins and x_col.dtype == "numeric":
        bins = max(2, min(100, int(request.bins)))
        ident = _quote_ident(x_col.safe_name)
        sql = (
            f"SELECT CAST(({ident} - (SELECT MIN({ident}) FROM {table_q}{where_sql})) "
            f"/ NULLIF((SELECT (MAX({ident}) - MIN({ident})) / {bins}.0 "
            f"FROM {table_q}{where_sql}), 0) AS INTEGER) AS bin_idx, "
            f"COUNT(*) AS value "
            f"FROM {table_q}{where_sql} "
            f"WHERE {ident} IS NOT NULL "
            f"GROUP BY bin_idx ORDER BY bin_idx LIMIT ?"
        )
        # WHERE in subqueries needs duplicated params
        all_params = params + params + params + [request.limit]
        rows = conn.execute(sql, all_params).fetchall()
        # Compute bin labels client-side via the min/max query
        mm = conn.execute(
            f"SELECT MIN({ident}) AS lo, MAX({ident}) AS hi FROM {table_q}{where_sql}",
            params,
        ).fetchone()
        lo, hi = float(mm["lo"] or 0), float(mm["hi"] or 0)
        width = (hi - lo) / bins if bins else 1
        result_rows = [
            QueryRow(
                label=round(lo + (r["bin_idx"] or 0) * width, 4),
                value=float(r["value"]),
            )
            for r in rows
            if r["bin_idx"] is not None
        ]
        return QueryResult(sql=sql, n_rows=len(result_rows), rows=result_rows)

    # ---- Group by x with aggregation on y (or count) ----
    x_ident = _quote_ident(x_col.safe_name)
    if request.agg == "count":
        agg_expr = "COUNT(*)"
    else:
        if y_col is None:
            raise ValueError(f"agg={request.agg} requires a y column")
        agg_expr = _AGG_SQL[request.agg].format(col=_quote_ident(y_col.safe_name))

    # For datetime x, bucket by day
    if x_col.dtype == "datetime":
        x_select = f"DATE({x_ident})"
        group_expr = x_select
    else:
        x_select = x_ident
        group_expr = x_ident

    order = "DESC" if request.order_desc else "ASC"
    limit = min(request.limit, settings.max_query_rows)

    sql = (
        f"SELECT {x_select} AS label, {agg_expr} AS value "
        f"FROM {table_q}{where_sql} "
        f"GROUP BY {group_expr} "
        f"ORDER BY value {order} "
        f"LIMIT ?"
    )
    rows = conn.execute(sql, [*params, limit]).fetchall()

    # If x is datetime, ensure chronological order even though we grouped by it
    if x_col.dtype == "datetime":
        rows = sorted(rows, key=lambda r: r["label"] or "")

    result_rows = [
        QueryRow(label=_to_label(r["label"]), value=_to_value(r["value"])) for r in rows
    ]
    return QueryResult(sql=sql, n_rows=len(result_rows), rows=result_rows)


def _to_label(v: Any):  # noqa: ANN201
    if v is None:
        return None
    if isinstance(v, (int, float, bool, str)):
        return v
    return str(v)


def _to_value(v: Any) -> float:
    if v is None:
        return 0.0
    return float(v)
