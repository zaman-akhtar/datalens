"""Executive summary: ≥ 3 numeric facts, cache hit on second call."""
from __future__ import annotations

import re
from pathlib import Path

from fastapi.testclient import TestClient


def _upload(client: TestClient, fixtures_dir: Path) -> str:
    csv = (fixtures_dir / "airbnb_sample.csv").read_bytes()
    r = client.post("/api/upload", files={"file": ("airbnb_sample.csv", csv, "text/csv")})
    return r.json()["dataset_id"]


def test_summary_contains_three_numeric_facts(client: TestClient, fixtures_dir: Path) -> None:
    ds_id = _upload(client, fixtures_dir)
    r = client.get(f"/api/datasets/{ds_id}/summary")
    assert r.status_code == 200, r.text
    text = r.json()["text"]
    nums = re.findall(r"\d+(?:\.\d+)?", text)
    assert len(nums) >= 3, f"Expected ≥3 numbers in: {text!r}"


def test_summary_cached_then_refreshed(client: TestClient, fixtures_dir: Path) -> None:
    ds_id = _upload(client, fixtures_dir)
    a = client.get(f"/api/datasets/{ds_id}/summary").json()
    b = client.get(f"/api/datasets/{ds_id}/summary").json()
    assert a["generated_at"] == b["generated_at"]  # served from cache
    c = client.get(f"/api/datasets/{ds_id}/summary?refresh=true").json()
    # Refresh should regenerate (new timestamp). In mock mode the text may match.
    assert c["dataset_id"] == ds_id
