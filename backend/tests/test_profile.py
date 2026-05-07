"""Profiler — covers numeric, all-null, mixed-type, datetime, and Unnamed-flagged columns."""
from __future__ import annotations

from pathlib import Path

from app.db.schema import init_schema
from app.db.session import get_conn
from app.services.ingest import ingest_csv_path
from app.services.profile import build_profile


def _ingest(fixtures_dir: Path, name: str) -> str:
    with get_conn() as conn:
        init_schema(conn)
        ds_id, _, _ = ingest_csv_path(conn, fixtures_dir / name)
        return ds_id


def test_profile_numeric_column(fixtures_dir: Path) -> None:
    ds_id = _ingest(fixtures_dir, "tiny.csv")
    with get_conn() as conn:
        prof = build_profile(conn, ds_id)
    score = next(c for c in prof.columns if c.safe_name == "score")
    assert score.dtype == "numeric"
    assert score.min == 6.4
    assert score.max == 9.9
    assert score.null_pct == 0.0


def test_profile_high_null_column(fixtures_dir: Path) -> None:
    ds_id = _ingest(fixtures_dir, "with_nulls.csv")
    with get_conn() as conn:
        prof = build_profile(conn, ds_id)
    cat = next(c for c in prof.columns if c.safe_name == "category")
    assert cat.null_pct > 0.0


def test_profile_mixed_types_becomes_text_or_categorical(fixtures_dir: Path) -> None:
    ds_id = _ingest(fixtures_dir, "mixed_types.csv")
    with get_conn() as conn:
        prof = build_profile(conn, ds_id)
    val = next(c for c in prof.columns if c.safe_name == "value")
    # mixed → object → categorical (low cardinality) is acceptable
    assert val.dtype in ("text", "categorical")


def test_profile_datetime_detected(fixtures_dir: Path) -> None:
    ds_id = _ingest(fixtures_dir, "with_unnamed.csv")
    with get_conn() as conn:
        prof = build_profile(conn, ds_id)
    date = next(c for c in prof.columns if c.safe_name == "date")
    assert date.dtype == "datetime"


def test_profile_unnamed_flagged_index(fixtures_dir: Path) -> None:
    ds_id = _ingest(fixtures_dir, "with_unnamed.csv")
    with get_conn() as conn:
        prof = build_profile(conn, ds_id)
    unnamed = next(c for c in prof.columns if c.name.startswith("Unnamed:"))
    assert unnamed.is_index is True


def test_profile_binary_indicator_is_boolean(fixtures_dir: Path) -> None:
    ds_id = _ingest(fixtures_dir, "with_unnamed.csv")
    with get_conn() as conn:
        prof = build_profile(conn, ds_id)
    flag = next(c for c in prof.columns if c.safe_name == "is_flag")
    assert flag.dtype == "boolean"
