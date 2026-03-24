"""Unit tests for cc_flow.wisdom — wisdom store, exploration cache, checkpoints."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from cc_flow.wisdom import (
    _cache_key,
    append_wisdom,
    cache_exploration,
    load_wisdom,
    lookup_exploration,
    record_chain_wisdom,
    search_wisdom,
    should_checkpoint,
)


class TestAppendAndLoadWisdom:
    """Test wisdom append/load cycle."""

    def test_append_and_load(self, tmp_path, monkeypatch):
        monkeypatch.setattr("cc_flow.wisdom.WISDOM_DIR", tmp_path)
        append_wisdom("learnings", {"content": "test insight"})
        entries = load_wisdom("learnings")
        assert len(entries) == 1
        assert entries[0]["content"] == "test insight"
        assert "timestamp" in entries[0]

    def test_invalid_category_ignored(self, tmp_path, monkeypatch):
        monkeypatch.setattr("cc_flow.wisdom.WISDOM_DIR", tmp_path)
        append_wisdom("invalid_cat", {"content": "nope"})
        # File should not be created
        assert not (tmp_path / "invalid_cat.jsonl").exists()

    def test_multiple_entries(self, tmp_path, monkeypatch):
        monkeypatch.setattr("cc_flow.wisdom.WISDOM_DIR", tmp_path)
        append_wisdom("decisions", {"content": "first"})
        append_wisdom("decisions", {"content": "second"})
        entries = load_wisdom("decisions")
        assert len(entries) == 2
        assert entries[0]["content"] == "first"
        assert entries[1]["content"] == "second"

    def test_load_with_limit(self, tmp_path, monkeypatch):
        monkeypatch.setattr("cc_flow.wisdom.WISDOM_DIR", tmp_path)
        for i in range(5):
            append_wisdom("conventions", {"content": f"item-{i}"})
        entries = load_wisdom("conventions", limit=3)
        assert len(entries) == 3
        # Should be the last 3
        assert entries[0]["content"] == "item-2"

    def test_load_empty_category(self, tmp_path, monkeypatch):
        monkeypatch.setattr("cc_flow.wisdom.WISDOM_DIR", tmp_path)
        entries = load_wisdom("learnings")
        assert entries == []


class TestSearchWisdom:
    """Test cross-category wisdom search."""

    def test_search_finds_match(self, tmp_path, monkeypatch):
        monkeypatch.setattr("cc_flow.wisdom.WISDOM_DIR", tmp_path)
        append_wisdom("learnings", {"content": "caching improved speed"})
        append_wisdom("decisions", {"content": "use redis for sessions"})
        results = search_wisdom("caching")
        assert len(results) == 1
        assert results[0]["_category"] == "learnings"

    def test_search_no_match(self, tmp_path, monkeypatch):
        monkeypatch.setattr("cc_flow.wisdom.WISDOM_DIR", tmp_path)
        append_wisdom("learnings", {"content": "something else"})
        results = search_wisdom("nonexistent_xyz")
        assert results == []

    def test_search_case_insensitive(self, tmp_path, monkeypatch):
        monkeypatch.setattr("cc_flow.wisdom.WISDOM_DIR", tmp_path)
        append_wisdom("learnings", {"content": "Docker compose works"})
        results = search_wisdom("docker")
        assert len(results) == 1


class TestRecordChainWisdom:
    """Test chain auto-recording."""

    def test_record_creates_entry(self, tmp_path, monkeypatch):
        monkeypatch.setattr("cc_flow.wisdom.WISDOM_DIR", tmp_path)
        record_chain_wisdom("feature", "success", 3, "built auth")
        entries = load_wisdom("learnings")
        assert len(entries) == 1
        assert entries[0]["chain"] == "feature"
        assert entries[0]["outcome"] == "success"


class TestCacheKey:
    """Test cache key generation."""

    def test_deterministic(self):
        assert _cache_key("hello") == _cache_key("hello")

    def test_different_queries_different_keys(self):
        assert _cache_key("hello") != _cache_key("world")

    def test_key_length(self):
        assert len(_cache_key("test query")) == 16


class TestExplorationCache:
    """Test exploration caching and lookup."""

    def test_cache_and_lookup(self, tmp_path, monkeypatch):
        monkeypatch.setattr("cc_flow.wisdom.EXPLORATIONS_DIR", tmp_path)
        key = cache_exploration("how does auth work", {"files": ["auth.py"]})
        assert len(key) == 16
        result = lookup_exploration("how does auth work")
        assert result is not None
        assert result["findings"]["files"] == ["auth.py"]

    def test_lookup_miss(self, tmp_path, monkeypatch):
        monkeypatch.setattr("cc_flow.wisdom.EXPLORATIONS_DIR", tmp_path)
        result = lookup_exploration("never cached this")
        assert result is None

    def test_fuzzy_lookup(self, tmp_path, monkeypatch):
        monkeypatch.setattr("cc_flow.wisdom.EXPLORATIONS_DIR", tmp_path)
        cache_exploration("how does authentication work", {"answer": "JWT"})
        # Fuzzy match: high word overlap
        result = lookup_exploration("how does authentication work today")
        assert result is not None
        assert result.get("_fuzzy_match") is True


class TestShouldCheckpoint:
    """Test checkpoint gate logic."""

    def test_short_chain_no_checkpoint(self):
        assert should_checkpoint("chain", 1, 3) is False
        assert should_checkpoint("chain", 2, 3) is False

    def test_step_zero_no_checkpoint(self):
        assert should_checkpoint("chain", 0, 5) is False

    def test_checkpoint_at_odd_indices(self):
        # 0-indexed: checkpoint at 1, 3, 5
        assert should_checkpoint("chain", 1, 5) is True
        assert should_checkpoint("chain", 3, 5) is True

    def test_no_checkpoint_at_even_indices(self):
        assert should_checkpoint("chain", 2, 5) is False
        assert should_checkpoint("chain", 4, 5) is False

    def test_long_chain(self):
        results = [should_checkpoint("c", i, 10) for i in range(10)]
        assert results == [False, True, False, True, False, True, False, True, False, True]
