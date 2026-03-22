"""Unit tests for extracted helper functions — no subprocess, direct imports."""

import sys
from pathlib import Path

# Ensure cc_flow package is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from cc_flow.config import _age_days, _safe_load_json
from cc_flow.core import now_iso, safe_json_load, slugify
from cc_flow.doctor import _check_python, _chk
from cc_flow.embeddings import _content_hash, cosine_similarity
from cc_flow.graph import STATUS_STYLE, _mermaid
from cc_flow.quality import _check_task_integrity, _detect_cycles, _detect_language
from cc_flow.route_learn import _calc_confidence, _keyword_route, _keyword_search, _make_result
from cc_flow.session import _git_state
from cc_flow.views import _task_counts
from cc_flow.work import _calc_duration, _consolidation_hint, _format_duration


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

    def test_three_node_cycle(self):
        tasks = {
            "a": {"depends_on": ["c"]},
            "b": {"depends_on": ["a"]},
            "c": {"depends_on": ["b"]},
        }
        errors = _detect_cycles(tasks)
        assert len(errors) > 0


class TestCoreUtils:
    def test_now_iso_format(self):
        result = now_iso()
        assert result.endswith("Z")
        assert "T" in result
        assert len(result) == 20  # 2026-03-22T12:00:00Z

    def test_slugify(self):
        assert slugify("Hello World") == "hello-world"
        assert slugify("  Foo  Bar  ") == "foo-bar"

    def test_safe_json_load_missing(self, tmp_path):
        result = safe_json_load(tmp_path / "nope.json", default={"x": 1})
        assert result == {"x": 1}

    def test_safe_json_load_corrupt(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("not json")
        result = safe_json_load(bad, default={})
        assert result == {}

    def test_safe_json_load_valid(self, tmp_path):
        good = tmp_path / "good.json"
        good.write_text('{"a": 1}')
        result = safe_json_load(good)
        assert result == {"a": 1}


class TestDoctorHelpers:
    def test_chk_format(self):
        result = _chk("Test", "pass", "ok")
        assert result == {"name": "Test", "status": "pass", "message": "ok", "fix": None}

    def test_chk_with_fix(self):
        result = _chk("Git", "fail", "missing", "brew install git")
        assert result["fix"] == "brew install git"

    def test_check_python(self):
        results = _check_python()
        assert len(results) == 1
        assert results[0]["name"] == "Python"
        # We must be running 3.9+ in CI
        assert results[0]["status"] in ("pass", "warn")


class TestCalcConfidence:
    def test_no_signals(self):
        assert _calc_confidence(None, None, None, {}) == 0

    def test_keyword_only(self):
        best = {"score": 3, "command": "/debug", "team": "bug-fix", "description": "debug"}
        result = _calc_confidence(best, None, None, {})
        assert result == 75  # 3 * 25, capped at 80 → 75

    def test_past_match_dominates(self):
        best = {"score": 1, "command": "/debug", "team": "bug-fix", "description": "debug"}
        past = {"confidence": 90}
        result = _calc_confidence(best, past, None, {})
        assert result == 90

    def test_capped_at_99(self):
        past = {"confidence": 100}
        result = _calc_confidence(None, past, None, {})
        assert result == 99

    def test_history_blend(self):
        best = {"score": 2, "command": "/tdd", "team": "dev", "description": "tdd"}
        cmd_stats = {"success": 8, "failure": 2}  # 80% success
        result = _calc_confidence(best, None, None, cmd_stats)
        # 50 * 0.7 + 80 * 0.3 = 35 + 24 = 59
        assert result == 59


class TestGraphHelpers:
    def test_status_style_keys(self):
        assert set(STATUS_STYLE.keys()) == {"todo", "in_progress", "done", "blocked"}
        for style in STATUS_STYLE.values():
            assert "icon" in style
            assert "mermaid" in style

    def test_mermaid_output(self, capsys):
        tasks = {
            "t1": {"title": "Task 1", "status": "done", "depends_on": []},
            "t2": {"title": "Task 2", "status": "todo", "depends_on": ["t1"]},
        }
        edges = [("t1", "t2")]
        _mermaid(tasks, edges)
        output = capsys.readouterr().out
        assert "graph TD" in output
        assert "t1" in output
        assert "t2" in output
        assert "-->" in output


class TestConfigHelpers:
    def test_safe_load_json_valid(self, tmp_path):
        f = tmp_path / "test.json"
        f.write_text('{"key": "value"}')
        result = _safe_load_json(f)
        assert result == {"key": "value"}

    def test_safe_load_json_corrupt(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("not json")
        assert _safe_load_json(f) is None


class TestSessionHelpers:
    def test_git_state_returns_triple(self):
        sha, branch, dirty = _git_state()
        # In a git repo, sha should be non-empty
        assert isinstance(sha, str)
        assert isinstance(branch, str)
        assert isinstance(dirty, str)


class TestConsolidationHint:
    def test_no_hint_when_no_learnings(self, tmp_path, monkeypatch):
        import cc_flow.work as work_mod
        monkeypatch.setattr(work_mod, "LEARNINGS_DIR", tmp_path / "nope")
        assert _consolidation_hint() is None


class TestDetectLanguage:
    def test_detects_python(self):
        # We have pyproject.toml in this project
        result = _detect_language()
        assert result == "python"


class TestAgeDays:
    def test_recent_file(self, tmp_path):
        f = tmp_path / "new.txt"
        f.write_text("hi")
        assert _age_days(f) == 0

    def test_returns_int(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hi")
        result = _age_days(f)
        assert isinstance(result, int)
        assert result >= 0


class TestEmbeddings:
    def test_cosine_similarity_identical(self):
        v = [1.0, 2.0, 3.0]
        assert cosine_similarity(v, v) > 0.999

    def test_cosine_similarity_orthogonal(self):
        assert cosine_similarity([1, 0], [0, 1]) == 0.0

    def test_cosine_similarity_opposite(self):
        assert cosine_similarity([1, 0], [-1, 0]) < -0.999

    def test_cosine_similarity_zero_vector(self):
        assert cosine_similarity([0, 0], [1, 2]) == 0.0

    def test_content_hash_deterministic(self):
        assert _content_hash("hello") == _content_hash("hello")
        assert _content_hash("hello") != _content_hash("world")

    def test_content_hash_length(self):
        assert len(_content_hash("test")) == 16
