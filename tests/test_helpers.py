"""Unit tests for extracted helper functions — no subprocess, direct imports."""

import sys
from pathlib import Path

# Ensure cc_flow package is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from cc_flow.quality import _check_task_integrity, _detect_cycles
from cc_flow.route_learn import _keyword_route, _keyword_search, _make_result
from cc_flow.views import _task_counts
from cc_flow.work import _calc_duration, _format_duration


class TestTaskCounts:
    def test_empty(self):
        result = _task_counts([])
        assert result == {"total": 0, "done": 0, "in_progress": 0, "blocked": 0, "todo": 0, "pct": 0}

    def test_all_done(self):
        tasks = [{"status": "done"}, {"status": "done"}]
        result = _task_counts(tasks)
        assert result["pct"] == 100
        assert result["done"] == 2

    def test_mixed(self):
        tasks = [
            {"status": "done"},
            {"status": "in_progress"},
            {"status": "blocked"},
            {"status": "todo"},
        ]
        result = _task_counts(tasks)
        assert result == {"total": 4, "done": 1, "in_progress": 1, "blocked": 1, "todo": 1, "pct": 25}


class TestCalcDuration:
    def test_none_input(self):
        assert _calc_duration(None) is None

    def test_empty_string(self):
        assert _calc_duration("") is None

    def test_invalid_iso(self):
        assert _calc_duration("not-a-date") is None

    def test_valid_iso(self):
        # A timestamp far in the past should give a large positive duration
        result = _calc_duration("2020-01-01T00:00:00+00:00")
        assert result is not None
        assert result > 0


class TestFormatDuration:
    def test_seconds(self):
        assert _format_duration(30) == "30s"

    def test_minutes(self):
        assert _format_duration(120) == "2m"

    def test_zero(self):
        assert _format_duration(0) == "0s"


class TestMakeResult:
    def test_basic(self):
        entry = {"task": "fix bug", "approach": "grep", "lesson": "read logs", "score": 4}
        result = _make_result(entry, 85, 2, "keyword")
        assert result["task"] == "fix bug"
        assert result["confidence"] == 85
        assert result["engine"] == "keyword"
        assert result["alternatives"] == 2


class TestKeywordSearch:
    def test_no_match(self):
        learnings = [{"task": "deploy", "lesson": "use CI", "approach": "auto", "score": 3}]
        assert _keyword_search("zzz_nomatch_zzz", learnings) is None

    def test_match(self):
        learnings = [
            {"task": "fix login bug", "lesson": "check auth", "approach": "debug", "score": 5},
            {"task": "deploy app", "lesson": "use CI", "approach": "auto", "score": 3},
        ]
        result = _keyword_search("fix login", learnings)
        assert result is not None
        assert result["engine"] == "keyword"
        assert result["task"] == "fix login bug"


class TestKeywordRoute:
    def test_match(self):
        matches = _keyword_route("fix bug error")
        assert len(matches) > 0
        # Should suggest debug-related command
        commands = [m["command"] for m in matches]
        assert any("debug" in c for c in commands)

    def test_no_match(self):
        matches = _keyword_route("zzz_nomatch_zzz_12345")
        assert matches == []


class TestCheckTaskIntegrity:
    def test_empty(self):
        errors, warnings = _check_task_integrity({})
        assert errors == []
        assert warnings == []


class TestDetectCycles:
    def test_no_cycles(self):
        tasks = {
            "a": {"depends_on": []},
            "b": {"depends_on": ["a"]},
        }
        errors = _detect_cycles(tasks)
        assert errors == []

    def test_cycle(self):
        tasks = {
            "a": {"depends_on": ["b"]},
            "b": {"depends_on": ["a"]},
        }
        errors = _detect_cycles(tasks)
        assert len(errors) > 0
        assert "cycle" in errors[0].lower()
