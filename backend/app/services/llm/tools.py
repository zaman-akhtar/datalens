"""Three LLM tools (System Design §6).

Each tool is a thin Python function the orchestrator can call. Each returns a
JSON-serializable dict the model can read back.
"""
from __future__ import annotations

import sqlite3
from typing import Any

from app.models.chart import ChartSpec
from app.models.query import QueryRequest
from app.services.profile import build_profile, get_column_profile
from app.services.query_engine import UnknownColumnError, run_query

# JSON schemas exposed to Gemini's function-calling API.
TOOL_SCHEMAS = [
    {
        "name": "query_data",
        "description": (
            "Run a structured aggregation. Use for 'how many', 'average', "
            "'sum', 'top by', 'distribution', etc."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "x": {"type": "string", "description": "Group-by column."},
                "y": {
                    "type": "string",
                    "description": "Numeric column to aggregate. Omit for count.",
                },
                "agg": {
                    "type": "string",
                    "enum": ["count", "sum", "mean", "min", "max", "median"],
                    "description": "Aggregation function. Use 'mean' to compute rates and averages (e.g. fraud rate = mean of is_fraud).",
                },
                "filters": {
                    "type": "object",
                    "description": "Optional column → value filter map.",
                },
                "limit": {"type": "integer", "description": "Max rows to return (1–100)."},
            },
            "required": ["x"],
        },
    },
    {
        "name": "get_column_statistics",
        "description": "Return descriptive statistics for one column.",
        "parameters": {
            "type": "object",
            "properties": {
                "column": {"type": "string", "description": "Column name."}
            },
            "required": ["column"],
        },
    },
    {
        "name": "generate_chart",
        "description": (
            "Return a ChartSpec the frontend can render. Use for 'show me', "
            "'plot', 'visualize'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "chart_type": {
                    "type": "string",
                    "enum": ["bar", "line", "histogram", "scatter", "kpi"],
                },
                "x": {"type": "string"},
                "y": {"type": "string"},
                "filters": {"type": "object"},
            },
            "required": ["chart_type", "x"],
        },
    },
]


def _truncate_rows(rows: list, cap: int = 100) -> list:
    return rows[:cap]


def query_data(
    conn: sqlite3.Connection,
    dataset_id: str,
    *,
    x: str,
    y: str | None = None,
    agg: str = "count",
    filters: dict | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Tool 1 — execute a structured query."""
    try:
        result = run_query(
            conn,
            dataset_id,
            QueryRequest(x=x, y=y, agg=agg, filters=filters, limit=min(limit, 100)),
        )
    except UnknownColumnError as e:
        return {"error": f"Unknown column: {e}. Use a column from the profile."}
    except ValueError as e:
        return {"error": str(e)}
    rows = _truncate_rows([{"label": r.label, "value": r.value} for r in result.rows])
    return {"sql": result.sql, "n_rows": result.n_rows, "rows": rows}


def get_column_statistics(
    conn: sqlite3.Connection, dataset_id: str, *, column: str
) -> dict[str, Any]:
    """Tool 2 — descriptive stats for one column."""
    profile = get_column_profile(conn, dataset_id, column)
    if profile is None:
        return {"error": f"Unknown column: {column}"}
    out = profile.model_dump()
    if profile.dtype in ("categorical", "text"):
        # Top-10 value counts
        top = run_query(conn, dataset_id, QueryRequest(x=profile.safe_name, agg="count", limit=10))
        out["top_values"] = [{"label": r.label, "count": r.value} for r in top.rows]
    return out


def generate_chart(
    conn: sqlite3.Connection,
    dataset_id: str,
    *,
    chart_type: str,
    x: str,
    y: str | None = None,
    filters: dict | None = None,
) -> dict[str, Any]:
    """Tool 3 — emit a ChartSpec the frontend can render directly."""
    spec = ChartSpec(
        chart_type=chart_type,  # type: ignore[arg-type]
        title=f"{chart_type.title()} of {x}" + (f" by {y}" if y else ""),
        x=x,
        y=y,
        agg="count" if chart_type in ("bar", "line", "histogram", "kpi") else "mean",
        bins=30 if chart_type == "histogram" else None,
        note="Generated via LLM tool call.",
    )
    # Validate columns exist
    profile = build_profile(conn, dataset_id)
    valid = {c.safe_name for c in profile.columns} | {c.name for c in profile.columns}
    if x not in valid or (y is not None and y not in valid):
        return {"error": f"Unknown column in chart spec (x={x}, y={y})"}
    out = spec.model_dump()
    out["filters"] = filters or {}
    return out


TOOL_FUNCTIONS = {
    "query_data": query_data,
    "get_column_statistics": get_column_statistics,
    "generate_chart": generate_chart,
}
