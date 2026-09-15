"""
Day 49 -- tests for day48_retry_logic.py, using unittest.mock so no
real API calls happen (free, instant, deterministic).

Run with: pytest tests/test_reasoning_engine.py -v
"""

import os
import sys
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from day48_retry_logic import get_structured_review, sort_by_severity


def fake_response(text):
    """Builds a fake Groq response object shaped like the real one."""
    response = MagicMock()
    response.choices[0].message.content = text
    return response


def test_successful_json_response():
    client = MagicMock()
    client.chat.completions.create.return_value = fake_response(
        '[{"issue": "x", "severity": "high", "explanation": "e", "suggested_fix": "f"}]'
    )
    result = get_structured_review(client, "mod.func", {"graph_neighbors": {}, "similar_chunks": []}, {"mod.func": {"text": "code"}})
    assert result == [{"issue": "x", "severity": "high", "explanation": "e", "suggested_fix": "f"}]
    assert client.chat.completions.create.call_count == 1


def test_retries_after_malformed_json_then_succeeds():
    client = MagicMock()
    client.chat.completions.create.side_effect = [
        fake_response("not valid json"),
        fake_response('[{"issue": "x", "severity": "low", "explanation": "e", "suggested_fix": "f"}]'),
    ]
    result = get_structured_review(client, "mod.func", {"graph_neighbors": {}, "similar_chunks": []}, {"mod.func": {"text": "code"}})
    assert len(result) == 1
    assert client.chat.completions.create.call_count == 2


def test_gives_up_after_max_retries():
    client = MagicMock()
    client.chat.completions.create.return_value = fake_response("still not valid json")
    result = get_structured_review(client, "mod.func", {"graph_neighbors": {}, "similar_chunks": []}, {"mod.func": {"text": "code"}}, max_retries=2)
    assert result == []
    assert client.chat.completions.create.call_count == 2


def test_sort_by_severity_orders_high_first():
    issues = [
        {"issue": "a", "severity": "low"},
        {"issue": "b", "severity": "high"},
        {"issue": "c", "severity": "medium"},
    ]
    sorted_issues = sort_by_severity(issues)
    assert [i["severity"] for i in sorted_issues] == ["high", "medium", "low"]
