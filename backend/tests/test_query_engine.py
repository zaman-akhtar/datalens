"""Query engine — basic agg, filters, validation, injection-attempt safety."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.db.schema import init_schema
from app.db.session import get_conn
from app.models.query import QueryRequest
from app.services.ingest import ingest_csv_path
from app.services.query_engine import UnknownColumnError, run_query


def _ingest(fixtures_dir: Path, name: str) -> str:
    with get_conn() as conn:
        init_schema(conn)
        ds_id, _, _ = ingest_csv_path(conn, fixtures_dir / name)
        return ds_id


def test_count_by_categorical(fixtures_dir: Path) -> None:
    ds_id = _ingest(fixtures_dir, "airbnb_sample.csv")
    with get_conn() as conn:
        result = run_query(
            conn, ds_id, QueryRequest(x="neighbourhood", agg="count", limit=10)
        )
    labels = {r.label for r in result.rows}
    assert "Manhattan" in labels
    assert sum(r.value for r in result.rows) == 15  # all rows accounted for


def test_mean_by_categorical(fixtures_dir: Path) -> None:
    ds_id = _ingest(fixtures_dir, "airbnb_sample.csv")
    with get_conn() as conn:
        result = run_query(
            conn, ds_id, QueryRequest(x="room_type", y="price", agg="mean", limit=10)
        )
    assert all(r.value > 0 for r in result.rows)
    assert "GROUP BY" in result.sql


def test_filter_equality(fixtures_dir: Path) -> None:
    ds_id = _ingest(fixtures_dir, "airbnb_sample.csv")
    with get_conn() as conn:
        all_rows = run_query(conn, ds_id, QueryRequest(x="neighbourhood", agg="count"))
        only_mh = run_query(
            conn,
            ds_id,
            QueryRequest(
                x="neighbourhood",
                agg="count",
                filters={"neighbourhood": "Manhattan"},
            ),
        )
    assert sum(r.value for r in only_mh.rows) < sum(r.value for r in all_rows.rows)


def test_unknown_column_raises(fixtures_dir: Path) -> None:
    ds_id = _ingest(fixtures_dir, "airbnb_sample.csv")
    with get_conn() as conn:
        with pytest.raises(UnknownColumnError):
            run_query(conn, ds_id, QueryRequest(x="not_a_column", agg="count"))


def test_sql_injection_attempt_is_safely_escaped(fixtures_dir: Path) -> None:
    """A malicious filter value cannot break out of the parameter binding."""
    ds_id = _ingest(fixtures_dir, "airbnb_sample.csv")
    bad_value = "Manhattan'; DROP TABLE datasets; --"
    with get_conn() as conn:
        result = run_query(
            conn,
            ds_id,
            QueryRequest(
                x="neighbourhood", agg="count", filters={"neighbourhood": bad_value}
            ),
        )
        # Returns zero matches, NOT an exception, NOT a dropped table.
        assert all(r.value == 0 for r in result.rows) or result.n_rows == 0
        # Datasets table still exists
        n = conn.execute("SELECT COUNT(*) AS n FROM datasets").fetchone()["n"]
        assert n >= 1


def test_histogram_bins_a_numeric_column(fixtures_dir: Path) -> None:
    ds_id = _ingest(fixtures_dir, "airbnb_sample.csv")
    with get_conn() as conn:
        result = run_query(
            conn, ds_id, QueryRequest(x="price", agg="count", bins=5)
        )
    assert 1 <= result.n_rows <= 6


def test_query_router_endpoints(client, fixtures_dir: Path) -> None:  # noqa: ANN001
    """Smoke-test /charts and /query through HTTP."""
    csv = (fixtures_dir / "airbnb_sample.csv").read_bytes()
    r = client.post("/api/upload", files={"file": ("airbnb_sample.csv", csv, "text/csv")})
    ds_id = r.json()["dataset_id"]

    charts = client.get(f"/api/datasets/{ds_id}/charts")
    assert charts.status_code == 200
    assert 4 <= len(charts.json()) <= 6

    q = client.post(
        f"/api/datasets/{ds_id}/query",
        json={"x": "neighbourhood", "agg": "count"},
    )
    assert q.status_code == 200
    assert q.json()["n_rows"] >= 1

    bad = client.post(
        f"/api/datasets/{ds_id}/query",
        json={"x": "ghost_column", "agg": "count"},
    )
    assert bad.status_code == 400
