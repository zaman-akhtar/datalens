"""Tests for GET /api/datasets/{id}/geo."""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient


def _upload(client: TestClient, fixtures_dir: Path, name: str) -> str:
    csv = (fixtures_dir / name).read_bytes()
    r = client.post("/api/upload", files={"file": (name, csv, "text/csv")})
    assert r.status_code == 201
    return r.json()["dataset_id"]


def test_geo_returns_rows_with_fraud_rate(client: TestClient, fixtures_dir: Path) -> None:
    ds_id = _upload(client, fixtures_dir, "with_state.csv")
    r = client.get(f"/api/datasets/{ds_id}/geo")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 3  # TX, CA, NY
    states = {row["state"] for row in rows}
    assert states == {"TX", "CA", "NY"}
    # TX: 3 rows, 1 fraud → rate = 1/3
    tx = next(row for row in rows if row["state"] == "TX")
    assert tx["count"] == 3
    assert tx["fraud_count"] == 1
    assert abs(tx["fraud_rate"] - 1 / 3) < 1e-6


def test_geo_ordered_by_count_descending(client: TestClient, fixtures_dir: Path) -> None:
    ds_id = _upload(client, fixtures_dir, "with_state.csv")
    rows = client.get(f"/api/datasets/{ds_id}/geo").json()
    counts = [r["count"] for r in rows]
    assert counts == sorted(counts, reverse=True)


def test_geo_returns_empty_without_region_col(client: TestClient, fixtures_dir: Path) -> None:
    ds_id = _upload(client, fixtures_dir, "tiny.csv")
    r = client.get(f"/api/datasets/{ds_id}/geo")
    assert r.status_code == 200
    assert r.json() == []


def test_geo_neighbourhood_col(client: TestClient, fixtures_dir: Path) -> None:
    ds_id = _upload(client, fixtures_dir, "airbnb_sample.csv")
    r = client.get(f"/api/datasets/{ds_id}/geo")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) > 0
    # No fraud column in airbnb → fraud_count=0, fraud_rate=0
    assert all(row["fraud_count"] == 0 for row in rows)
    assert all(row["fraud_rate"] == 0.0 for row in rows)


def test_geo_404(client: TestClient) -> None:
    r = client.get("/api/datasets/nonexistent/geo")
    assert r.status_code == 404
