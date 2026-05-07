"""LLM provider — mock returns text and tool calls correctly."""
from __future__ import annotations

from app.services.llm.provider import MockProvider


def test_mock_returns_tool_call_when_tools_provided() -> None:
    p = MockProvider()
    resp = p.generate(
        messages=[{"role": "user", "content": "show me a chart of category"}],
        tools=[{"name": "generate_chart", "description": "x", "parameters": {}}],
    )
    assert resp.is_tool_call
    assert resp.tool_calls
    assert resp.tool_calls[0].name == "generate_chart"


def test_mock_returns_text_after_tool_result() -> None:
    p = MockProvider()
    resp = p.generate(
        messages=[
            {"role": "user", "content": "what is the avg price?"},
            {"role": "tool", "content": '{"rows": [{"label":"a","value":99}]}'},
        ],
        tools=[{"name": "query_data", "description": "x", "parameters": {}}],
    )
    assert resp.text
    assert not resp.is_tool_call


def test_mock_chooses_query_data_for_aggregation_question() -> None:
    p = MockProvider()
    resp = p.generate(
        messages=[{"role": "user", "content": "how many rows by category?"}],
        tools=[{"name": "query_data", "description": "x", "parameters": {}}],
    )
    assert resp.tool_calls and resp.tool_calls[0].name == "query_data"
