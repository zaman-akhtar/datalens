"""Executive summary — feeds the model the profile + 3 canned aggregates."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime

from app.models.query import QueryRequest
from app.models.summary import Summary
from app.services.llm.provider import get_provider
from app.services.profile import build_profile
from app.services.query_engine import run_query

PROMPT = """\
You are writing a one-paragraph executive summary of a dataset for a busy
manager. Use ONLY the facts provided below. Include AT LEAST THREE specific
numbers (counts, percentages, or averages) drawn from the facts. Keep it under
six sentences. Plain prose — no bullet lists.

Dataset: {filename}
Rows: {n_rows}, Columns: {n_cols}
Columns and types:
{column_lines}

Aggregate snapshots:
{snapshots}
"""


def _column_lines(profile) -> str:  # noqa: ANN001
    lines = []
    for c in profile.columns[:20]:
        line = f"- {c.name} ({c.dtype}, {round(c.null_pct*100, 1)}% null, {c.n_unique} unique)"
        if c.dtype == "numeric" and c.mean is not None:
            line += f" mean={c.mean:.2f} min={c.min} max={c.max}"
        lines.append(line)
    return "\n".join(lines)


def _snapshots(conn: sqlite3.Connection, dataset_id: str, profile) -> str:  # noqa: ANN001
    snaps = []
    cat = next((c for c in profile.columns if c.dtype == "categorical"), None)
    if cat:
        r = run_query(conn, dataset_id, QueryRequest(x=cat.safe_name, agg="count", limit=5))
        snaps.append(
            f"Top {cat.name} values: " + ", ".join(f"{row.label}={int(row.value)}" for row in r.rows)
        )
    num = next((c for c in profile.columns if c.dtype == "numeric"), None)
    if num and cat:
        r = run_query(
            conn, dataset_id, QueryRequest(x=cat.safe_name, y=num.safe_name, agg="mean", limit=5)
        )
        snaps.append(
            f"Mean {num.name} by {cat.name}: " + ", ".join(f"{row.label}={row.value:.2f}" for row in r.rows)
        )
    boolean = next((c for c in profile.columns if c.dtype == "boolean"), None)
    if boolean:
        r = run_query(
            conn, dataset_id, QueryRequest(x=boolean.safe_name, agg="count", limit=5)
        )
        total = sum(row.value for row in r.rows)
        positives = next((row.value for row in r.rows if row.label in (1, True, "1", "True")), 0)
        rate = (positives / total * 100) if total else 0
        snaps.append(f"{boolean.name} positive-rate: {rate:.2f}% of {int(total)} rows")
    return "\n".join(snaps) if snaps else "(no aggregate snapshots available)"


def _fallback_summary(profile, snapshots: str) -> str:  # noqa: ANN001
    """Used in MOCK_LLM mode and as a safety net if Gemini fails."""
    return (
        f"This dataset contains {profile.n_rows} rows across {profile.n_cols} columns "
        f"covering data such as {', '.join(c.name for c in profile.columns[:3])}. "
        f"The first numeric column averages {next((c.mean for c in profile.columns if c.dtype=='numeric' and c.mean is not None), 0):.2f}, "
        f"with values spanning a wide range. {snapshots.splitlines()[0] if snapshots else ''}"
    ).strip()


def generate_summary(
    conn: sqlite3.Connection, dataset_id: str, *, refresh: bool = False
) -> Summary:
    """Return cached or freshly-generated summary."""
    if not refresh:
        row = conn.execute(
            "SELECT text, generated_at FROM summaries WHERE dataset_id = ?",
            (dataset_id,),
        ).fetchone()
        if row:
            ts = row["generated_at"]
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts.replace(" ", "T"))
            return Summary(dataset_id=dataset_id, text=row["text"], generated_at=ts)

    profile = build_profile(conn, dataset_id)
    snapshots = _snapshots(conn, dataset_id, profile)
    prompt = PROMPT.format(
        filename=profile.original_filename,
        n_rows=profile.n_rows,
        n_cols=profile.n_cols,
        column_lines=_column_lines(profile),
        snapshots=snapshots,
    )

    provider = get_provider()
    try:
        resp = provider.generate(
            messages=[{"role": "user", "content": prompt}],
            tools=None,
            system="You write crisp executive summaries.",
        )
        text = resp.text or _fallback_summary(profile, snapshots)
    except Exception:  # noqa: BLE001
        text = _fallback_summary(profile, snapshots)

    now = datetime.utcnow()
    conn.execute(
        "INSERT OR REPLACE INTO summaries (dataset_id, text, generated_at) VALUES (?, ?, ?)",
        (dataset_id, text, now),
    )
    return Summary(dataset_id=dataset_id, text=text, generated_at=now)
