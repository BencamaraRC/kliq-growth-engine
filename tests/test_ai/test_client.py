"""Tests for the AI client — JSON parsing, retry logic, etc."""

import json

import pytest

from app.ai.client import AIClient


class TestJsonParsing:
    """Test the _parse_json static method."""

    def test_parse_plain_json(self):
        raw = '{"key": "value", "num": 42}'
        result = AIClient._parse_json(raw)
        assert result == {"key": "value", "num": 42}

    def test_parse_json_with_markdown_fences(self):
        raw = '```json\n{"key": "value"}\n```'
        result = AIClient._parse_json(raw)
        assert result == {"key": "value"}

    def test_parse_json_with_plain_fences(self):
        raw = '```\n{"key": "value"}\n```'
        result = AIClient._parse_json(raw)
        assert result == {"key": "value"}

    def test_parse_json_with_whitespace(self):
        raw = '  \n  {"key": "value"}  \n  '
        result = AIClient._parse_json(raw)
        assert result == {"key": "value"}

    def test_parse_invalid_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            AIClient._parse_json("this is not json")

    def test_parse_nested_json(self):
        raw = '{"products": [{"name": "Basic", "price": 999}], "count": 1}'
        result = AIClient._parse_json(raw)
        assert len(result["products"]) == 1
        assert result["products"][0]["price"] == 999
