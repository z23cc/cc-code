"""Tests for ai_router.py — AI-powered routing."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from cc_flow.ai_router import (
    _cache_key,
    _cache_lookup,
    _cache_save,
    _parse_router_response,
)


class TestParseResponse:
    def test_clean_json(self):
        r = _parse_router_response('{"chain": "bugfix", "complexity": "simple", "reason": "fixing a bug"}')
        assert r["chain"] == "bugfix"
        assert r["complexity"] == "simple"

    def test_json_in_markdown(self):
        text = 'Here is my analysis:\n```json\n{"chain": "feature", "complexity": "medium", "reason": "new feature"}\n```'
        r = _parse_router_response(text)
        assert r["chain"] == "feature"

    def test_json_with_noise(self):
        text = 'I think the best chain is:\n{"chain": "hotfix", "complexity": "simple", "reason": "trivial fix"}\nLet me know if you need more.'
        r = _parse_router_response(text)
        assert r["chain"] == "hotfix"

    def test_invalid(self):
        assert _parse_router_response("no json here") is None

    def test_empty(self):
        assert _parse_router_response("") is None


class TestCache:
    def test_cache_key_deterministic(self):
        assert _cache_key("fix a bug") == _cache_key("fix a bug")
        assert _cache_key("Fix A Bug") == _cache_key("fix a bug")  # case insensitive

    def test_cache_key_unique(self):
        assert _cache_key("fix a bug") != _cache_key("add a feature")

    def test_round_trip(self, tmp_path, monkeypatch):
        import cc_flow.ai_router as mod
        monkeypatch.setattr(mod, "CACHE_DIR", tmp_path / "cache")

        result = {"chain": "bugfix", "complexity": "simple"}
        _cache_save("fix a bug", result)
        cached = _cache_lookup("fix a bug")
        assert cached is not None
        assert cached["chain"] == "bugfix"

    def test_cache_miss(self, tmp_path, monkeypatch):
        import cc_flow.ai_router as mod
        monkeypatch.setattr(mod, "CACHE_DIR", tmp_path / "cache")

        assert _cache_lookup("never cached") is None
