"""Chart-spec schema returned by the chart-picker and the generate_chart LLM tool."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ChartType = Literal["bar", "line", "histogram", "scatter", "kpi"]


class ChartSpec(BaseModel):
    chart_type: ChartType
    title: str
    x: str
    y: str | None = None
    agg: str = "count"
    bins: int | None = None
    note: str | None = Field(default=None, description="Why the picker chose this chart.")
