"""LLM tool functions: query_data, get_column_statistics, generate_chart."""
from __future__ import annotations

from pathlib import Path

from app.db.schema import init_schema
from app.db.session import get_conn
from app.services.ingest import ingest_csv_path
from app.services.llm.tools import (
    TOOL_SCHEMAS,
    generate_chart,
    get_column_statistics,
    query_data,
)


def _setup(fixtures_dir: Path):  # noqa: ANN202
    with get_conn() as conn:
        init_schema(conn)
        ds_id, _, _ = ingest_csv_path(conn, fixtures_dir / "airbnb_sample.csv")
        return ds_id


def test_query_data_returns_rows(fixtures_dir: Path) -> None:
    ds_id = _setup(fixtures_dir)
    with get_conn() as conn:
        out = query_data(conn, ds_id, x="neighbourhood", agg="count")
    assert "rows" in out
    assert out["n_rows"] >= 1
    assert "sql" in out


def test_query_data_unknown_column_returns_error(fixtures_dir: Path) -> None:
    ds_id = _setup(fixtures_dir)
    with get_conn() as conn:
        out = query_data(conn, ds_id, x="ghost_col", agg="count")
    assert "error" in out


def test_get_column_statistics_categorical_includes_top_values(fixtures_dir: Path) -> None:
    ds_id = _setup(fixtures_dir)
    with get_conn() as conn:
        out = get_column_statistics(conn, ds_id, column="room_type")
    assert out.get("dtype") in ("categorical", "text")
    assert "top_values" in out


def test_generate_chart_validates_columns(fixtures_dir: Path) -> None:
    ds_id = _setup(fixtures_dir)
    with get_conn() as conn:
        ok = generate_chart(conn, ds_id, chart_type="bar", x="room_type")
        bad = generate_chart(conn, ds_id, chart_type="bar", x="ghost")
    assert ok.get("chart_type") == "bar"
    assert "error" in bad


def test_tool_schemas_well_formed() -> None:
    names = {t["name"] for t in TOOL_SCHEMAS}
    assert names == {"query_data", "get_column_statistics", "generate_chart"}
