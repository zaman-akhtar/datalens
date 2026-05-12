"""DataLens MCP server — exposes the same 3 query tools as the LLM chat layer.

Run (stdio, for Claude Desktop):
    uv run mcp_server/server.py

The server reads DATABASE_URL from the environment (same as the FastAPI backend).
Each tool accepts a dataset_id parameter; use list_datasets to discover IDs.
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from app.db.schema import init_schema
from app.db.session import get_conn
from app.services.llm.tools import (
    generate_chart as _generate_chart,
    get_column_statistics as _get_column_statistics,
    query_data as _query_data,
)
from app.services.profile import list_datasets

mcp = FastMCP(
    "DataLens",
    instructions=(
        "Analytical assistant for CSV datasets loaded into DataLens. "
        "Call list_datasets first to discover available dataset IDs, "
        "then use query_data, get_column_statistics, or generate_chart."
    ),
)


@mcp.tool()
def list_datasets_tool() -> list[dict]:
    """Return all datasets currently loaded in the DataLens database."""
    with get_conn() as conn:
        init_schema(conn)
        rows = list_datasets(conn)
    return [
        {
            "dataset_id": r.dataset_id,
            "filename": r.original_filename,
            "n_rows": r.n_rows,
            "n_cols": r.n_cols,
        }
        for r in rows
    ]


@mcp.tool()
def query_data(
    dataset_id: str,
    x: str,
    y: str | None = None,
    agg: str = "count",
    filters: dict | None = None,
    limit: int = 20,
) -> dict:
    """Run a structured aggregation query on a dataset.

    Args:
        dataset_id: The dataset ID returned by list_datasets_tool.
        x: Column to group by (or '__rows__' for total row count).
        y: Numeric column to aggregate. Omit for count.
        agg: Aggregation function — count | sum | mean | min | max | median.
        filters: Optional dict mapping column names to filter values.
        limit: Maximum rows to return (capped at 100).
    """
    with get_conn() as conn:
        return _query_data(conn, dataset_id, x=x, y=y, agg=agg, filters=filters, limit=limit)


@mcp.tool()
def get_column_statistics(dataset_id: str, column: str) -> dict:
    """Return descriptive statistics for one column in a dataset.

    Args:
        dataset_id: The dataset ID returned by list_datasets_tool.
        column: Column name (display name or safe name both accepted).
    """
    with get_conn() as conn:
        return _get_column_statistics(conn, dataset_id, column=column)


@mcp.tool()
def generate_chart(
    dataset_id: str,
    chart_type: str,
    x: str,
    y: str | None = None,
    filters: dict | None = None,
) -> dict:
    """Return a ChartSpec the DataLens frontend can render directly.

    Args:
        dataset_id: The dataset ID returned by list_datasets_tool.
        chart_type: bar | line | histogram | scatter | kpi | map.
        x: Column for the x-axis / grouping.
        y: Optional column for the y-axis (required for scatter and mean/sum aggs).
        filters: Optional column → value filter map.
    """
    with get_conn() as conn:
        return _generate_chart(
            conn, dataset_id, chart_type=chart_type, x=x, y=y, filters=filters
        )


if __name__ == "__main__":
    mcp.run()
