"""Query request / response schemas — used by /query, the chart picker, and LLM tools."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Aggregation = Literal["count", "sum", "mean", "min", "max", "median"]


class FilterClause(BaseModel):
    column: str
    op: Literal["eq", "in", "between"] = "eq"
    value: Any  # validated server-side against the column profile


class QueryRequest(BaseModel):
    x: str = Field(description="Group-by column.")
    y: str | None = Field(default=None, description="Numeric column to aggregate (omit for count).")
    agg: Aggregation = "count"
    filters: dict[str, str | int | float | bool | None] | None = None
    limit: int = Field(default=1000, ge=1, le=5000)
    order_desc: bool = True
    bins: int | None = Field(default=None, ge=2, le=100, description="For histogram: bin count.")


class QueryRow(BaseModel):
    """One row of a query result."""

    label: str | int | float | bool | None
    value: float


class QueryResult(BaseModel):
    sql: str
    n_rows: int
    rows: list[QueryRow]
