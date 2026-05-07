"""GET /api/datasets and /api/datasets/{id}/profile."""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient


def _upload(client: TestClient, fixtures_dir: Path, name: str) -> str:
    csv = (fixtures_dir / name).read_bytes()
    r = client.post("/api/upload", files={"file": (name, csv, "text/csv")})
    assert r.status_code == 201
    return r.json()["dataset_id"]


def test_get_profile_ok(client: TestClient, fixtures_dir: Path) -> None:
    ds_id = _upload(client, fixtures_dir, "tiny.csv")
    r = client.get(f"/api/datasets/{ds_id}/profile")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["dataset_id"] == ds_id
    assert body["n_cols"] == 3
    names = {c["safe_name"] for c in body["columns"]}
    assert names == {"id", "name", "score"}


def test_get_profile_404(client: TestClient) -> None:
    r = client.get("/api/datasets/does-not-exist/profile")
    assert r.status_code == 404


def test_list_datasets(client: TestClient, fixtures_dir: Path) -> None:
    _upload(client, fixtures_dir, "tiny.csv")
    _upload(client, fixtures_dir, "airbnb_sample.csv")
    r = client.get("/api/datasets")
    assert r.status_code == 200
    assert len(r.json()) == 2
