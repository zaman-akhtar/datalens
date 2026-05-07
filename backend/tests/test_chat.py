"""Chat orchestrator: tool loop, history persistence, max iterations."""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient


def _upload(client: TestClient, fixtures_dir: Path) -> str:
    csv = (fixtures_dir / "airbnb_sample.csv").read_bytes()
    r = client.post("/api/upload", files={"file": ("airbnb_sample.csv", csv, "text/csv")})
    return r.json()["dataset_id"]


def test_chat_turn_returns_answer(client: TestClient, fixtures_dir: Path) -> None:
    ds_id = _upload(client, fixtures_dir)
    r = client.post(
        f"/api/datasets/{ds_id}/chat",
        json={"message": "Which neighbourhood has the most listings?"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["answer"]
    assert body["conversation_id"]
    # Mock provider always issues exactly one tool call before answering
    assert len(body["tool_calls"]) >= 1


def test_chat_history_persisted(client: TestClient, fixtures_dir: Path) -> None:
    ds_id = _upload(client, fixtures_dir)
    client.post(
        f"/api/datasets/{ds_id}/chat",
        json={"message": "Plot a bar chart of neighbourhood."},
    )
    r = client.get(f"/api/datasets/{ds_id}/chat/history")
    assert r.status_code == 200
    msgs = r.json()
    roles = [m["role"] for m in msgs]
    assert "user" in roles and "assistant" in roles


def test_chat_404_on_unknown_dataset(client: TestClient) -> None:
    r = client.post(
        "/api/datasets/no-such-id/chat", json={"message": "hi"}
    )
    assert r.status_code == 404
