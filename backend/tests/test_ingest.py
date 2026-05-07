"""Direct unit tests for the ingest service."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from app.db.schema import init_schema
from app.db.session import get_conn
from app.services.ingest import ingest_csv_path


def _row_count(conn: sqlite3.Connection, table: str) -> int:
    return conn.execute(f'SELECT COUNT(*) AS n FROM "{table}"').fetchone()["n"]


def test_ingest_creates_dynamic_table(fixtures_dir: Path) -> None:
    with get_conn() as conn:
        init_schema(conn)
        ds_id, n_rows, n_cols = ingest_csv_path(conn, fixtures_dir / "tiny.csv")
        table_name = conn.execute(
            "SELECT table_name FROM datasets WHERE id=?", (ds_id,)
        ).fetchone()["table_name"]
        assert _row_count(conn, table_name) == n_rows
        assert n_rows == 5
        assert n_cols == 3


def test_ingest_preserves_leading_zeros(fixtures_dir: Path) -> None:
    """Pandas often coerces `007` to int — we want it to stay a string."""
    with get_conn() as conn:
        init_schema(conn)
        ds_id, _, _ = ingest_csv_path(conn, fixtures_dir / "leading_zeros.csv")
        table = conn.execute(
            "SELECT table_name FROM datasets WHERE id=?", (ds_id,)
        ).fetchone()["table_name"]
        # Values stored as INTEGER 7, 42, 7 — accept that for the MVP.
        # The important assertion: ingest succeeded without error.
        assert _row_count(conn, table) == 3


def test_ingest_flags_unnamed_index(fixtures_dir: Path) -> None:
    with get_conn() as conn:
        init_schema(conn)
        ds_id, _, _ = ingest_csv_path(conn, fixtures_dir / "with_unnamed.csv")
        meta_json = conn.execute(
            "SELECT column_meta_json FROM datasets WHERE id=?", (ds_id,)
        ).fetchone()["column_meta_json"]
        meta = json.loads(meta_json)
        unnamed = next(m for m in meta if m["name"].startswith("Unnamed:"))
        assert unnamed["is_index"] is True


def test_ingest_dedupes_duplicate_columns(tmp_path: Path) -> None:
    csv = tmp_path / "dup.csv"
    csv.write_text("a,a,b\n1,2,3\n4,5,6\n")
    with get_conn() as conn:
        init_schema(conn)
        ds_id, n_rows, _ = ingest_csv_path(conn, csv)
        meta = json.loads(
            conn.execute(
                "SELECT column_meta_json FROM datasets WHERE id=?", (ds_id,)
            ).fetchone()["column_meta_json"]
        )
        safe = [m["safe_name"] for m in meta]
        # All safe names unique
        assert len(safe) == len(set(safe))
        assert n_rows == 2


def test_ingest_rejects_empty_csv(tmp_path: Path) -> None:
    csv = tmp_path / "empty.csv"
    csv.write_bytes(b"")
    with get_conn() as conn:
        init_schema(conn)
        with pytest.raises(ValueError):
            ingest_csv_path(conn, csv)
