"""Chart-picker behaves the same on different datasets."""
from __future__ import annotations

from pathlib import Path

from app.db.schema import init_schema
from app.db.session import get_conn
from app.services.chart_picker import pick_charts
from app.services.ingest import ingest_csv_path
from app.services.profile import build_profile


def _picks(fixtures_dir: Path, name: str):  # noqa: ANN202
    with get_conn() as conn:
        init_schema(conn)
        ds_id, _, _ = ingest_csv_path(conn, fixtures_dir / name)
        return pick_charts(build_profile(conn, ds_id))


def test_picker_returns_at_least_four_charts(fixtures_dir: Path) -> None:
    picks = _picks(fixtures_dir, "with_unnamed.csv")
    assert 4 <= len(picks) <= 6


def test_picker_emits_time_series_when_datetime_present(fixtures_dir: Path) -> None:
    picks = _picks(fixtures_dir, "with_unnamed.csv")
    assert any(p.chart_type == "line" for p in picks)


def test_picker_emits_kpi_for_boolean_indicator(fixtures_dir: Path) -> None:
    picks = _picks(fixtures_dir, "with_unnamed.csv")
    assert any(p.chart_type == "kpi" and p.agg == "count" for p in picks)


def test_picker_works_on_airbnb_dataset(fixtures_dir: Path) -> None:
    """Cross-dataset proof — same code, different CSV."""
    picks = _picks(fixtures_dir, "airbnb_sample.csv")
    assert 4 <= len(picks) <= 6
    chart_types = {p.chart_type for p in picks}
    # Airbnb has categoricals (neighbourhood, room_type) and numerics (price)
    assert "bar" in chart_types
    # No date column → no line chart expected
    assert "line" not in chart_types


def test_picker_caps_at_six(fixtures_dir: Path) -> None:
    picks = _picks(fixtures_dir, "airbnb_sample.csv")
    assert len(picks) <= 6


def test_picker_is_deterministic(fixtures_dir: Path) -> None:
    a = _picks(fixtures_dir, "airbnb_sample.csv")
    b = _picks(fixtures_dir, "airbnb_sample.csv")
    assert [p.title for p in a] == [p.title for p in b]
