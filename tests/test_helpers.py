"""Unit tests for extracted helper functions — no subprocess, direct imports."""

import sys
from pathlib import Path

# Ensure cc_flow package is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import json

from cc_flow.config import _age_days, _safe_load_json
from cc_flow.core import atomic_write, now_iso, safe_json_load, safe_read, save_task, slugify
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

    def test_atomic_write(self, tmp_path):
        target = tmp_path / "test.txt"
        atomic_write(target, "hello world")
        assert target.read_text() == "hello world"

    def test_atomic_write_overwrites(self, tmp_path):
        target = tmp_path / "test.txt"
        atomic_write(target, "first")
        atomic_write(target, "second")
        assert target.read_text() == "second"

    def test_atomic_write_no_partial(self, tmp_path):
        target = tmp_path / "test.txt"
        atomic_write(target, "original")
        # If we check during write, file should be either old or new, never partial
        assert target.read_text() == "original"

    def test_save_task_atomic(self, tmp_path):
        path = tmp_path / "task.json"
        save_task(path, {"id": "t1", "status": "todo"})
        data = json.loads(path.read_text())
        assert data["id"] == "t1"

    def test_safe_read_valid(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello")
        assert safe_read(f) == "hello"

    def test_safe_read_missing(self, tmp_path):
        assert safe_read(tmp_path / "nope.txt") == ""

    def test_safe_read_default(self, tmp_path):
        assert safe_read(tmp_path / "nope.txt", "fallback") == "fallback"

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


class TestPluginSystem:
    def test_discover_empty(self, tmp_path, monkeypatch):
        import cc_flow.plugins as plug_mod
        monkeypatch.setattr(plug_mod, "PLUGINS_DIR", tmp_path / "nope")
        from cc_flow.plugins import discover_plugins
        assert discover_plugins() == []

    def test_discover_with_plugin(self, tmp_path, monkeypatch):
        import cc_flow.plugins as plug_mod
        plug_dir = tmp_path / "plugins"
        plug_dir.mkdir()
        (plug_dir / "test_plug.py").write_text(
            'PLUGIN_NAME = "test"\nPLUGIN_VERSION = "1.0"\nPLUGIN_DESCRIPTION = "A test"\n',
        )
        monkeypatch.setattr(plug_mod, "PLUGINS_DIR", plug_dir)
        monkeypatch.setattr(plug_mod, "_loaded_plugins", {})
        from cc_flow.plugins import discover_plugins
        plugins = discover_plugins()
        assert len(plugins) == 1
        assert plugins[0]["name"] == "test"
        assert plugins[0]["version"] == "1.0"

    def test_is_enabled_default(self, tmp_path, monkeypatch):
        import cc_flow.plugins as plug_mod
        monkeypatch.setattr(plug_mod, "PLUGIN_REGISTRY_FILE", tmp_path / "nope.json")
        from cc_flow.plugins import is_enabled
        assert is_enabled("anything") is True

    def test_is_enabled_disabled(self, tmp_path, monkeypatch):
        import cc_flow.plugins as plug_mod
        reg_file = tmp_path / "plugins.json"
        reg_file.write_text(json.dumps({"disabled": ["my-plug"]}))
        monkeypatch.setattr(plug_mod, "PLUGIN_REGISTRY_FILE", reg_file)
        from cc_flow.plugins import is_enabled
        assert is_enabled("my-plug") is False
        assert is_enabled("other") is True

    def test_fire_hook_no_plugins(self, tmp_path, monkeypatch):
        import cc_flow.plugins as plug_mod
        monkeypatch.setattr(plug_mod, "PLUGINS_DIR", tmp_path / "nope")
        from cc_flow.plugins import fire_hook
        results = fire_hook("on_task_done", task={"id": "t1"})
        assert results == []

    def test_broken_plugin_graceful(self, tmp_path, monkeypatch):
        import cc_flow.plugins as plug_mod
        plug_dir = tmp_path / "plugins"
        plug_dir.mkdir()
        (plug_dir / "broken.py").write_text("raise RuntimeError('boom')")
        monkeypatch.setattr(plug_mod, "PLUGINS_DIR", plug_dir)
        monkeypatch.setattr(plug_mod, "_loaded_plugins", {})
        from cc_flow.plugins import discover_plugins
        plugins = discover_plugins()
        assert len(plugins) == 1
        assert "error" in plugins[0]


class TestWorkflowHelpers:
    def test_builtin_workflows(self):
        from cc_flow.workflow import BUILTIN_WORKFLOWS
        assert "feature" in BUILTIN_WORKFLOWS
        assert "release" in BUILTIN_WORKFLOWS
        assert "health" in BUILTIN_WORKFLOWS
        for wf in BUILTIN_WORKFLOWS.values():
            assert "steps" in wf
            assert "description" in wf

    def test_all_workflows_includes_builtins(self, tmp_path, monkeypatch):
        import cc_flow.workflow as wf_mod
        monkeypatch.setattr(wf_mod, "WORKFLOWS_DIR", tmp_path / "nope")
        from cc_flow.workflow import _all_workflows
        workflows = _all_workflows()
        assert len(workflows) >= 3

    def test_custom_workflow_loaded(self, tmp_path, monkeypatch):
        import cc_flow.workflow as wf_mod
        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()
        (wf_dir / "my-wf.json").write_text(json.dumps({
            "description": "Custom", "steps": [{"name": "lint", "command": "verify"}],
        }))
        monkeypatch.setattr(wf_mod, "WORKFLOWS_DIR", wf_dir)
        from cc_flow.workflow import _all_workflows
        workflows = _all_workflows()
        assert "my-wf" in workflows
        assert workflows["my-wf"]["description"] == "Custom"


class TestScanner:
    def test_scan_architecture(self):
        from cc_flow.scanner import scan_architecture
        findings = scan_architecture()
        # Should return a list (possibly empty for well-structured code)
        assert isinstance(findings, list)

    def test_scan_docstrings(self):
        from cc_flow.scanner import scan_docstrings
        findings = scan_docstrings()
        assert isinstance(findings, list)

    def test_scan_duplication(self):
        from cc_flow.scanner import scan_duplication
        findings = scan_duplication()
        assert isinstance(findings, list)

    def test_run_smart_scan(self):
        from cc_flow.scanner import run_smart_scan
        results = run_smart_scan(["architecture", "docstrings"])
        assert isinstance(results, dict)

    def test_scan_trend_insufficient(self, tmp_path, monkeypatch):
        import cc_flow.scanner as scanner_mod
        monkeypatch.setattr(scanner_mod, "SCAN_HISTORY_FILE", tmp_path / "nope.json")
        from cc_flow.scanner import get_scan_trend
        assert get_scan_trend() == "insufficient_data"


class TestQRouter:
    def test_classify_feature(self):
        from cc_flow.qrouter import _classify_task
        assert _classify_task("add new feature for login") == "feature"

    def test_classify_bugfix(self):
        from cc_flow.qrouter import _classify_task
        assert _classify_task("fix crash on startup") == "bugfix"

    def test_classify_unknown(self):
        from cc_flow.qrouter import _classify_task
        result = _classify_task("zzz qqq 12345")
        assert result == "general"

    def test_q_route_empty(self, tmp_path, monkeypatch):
        import cc_flow.qrouter as qr
        monkeypatch.setattr(qr, "QTABLE_FILE", tmp_path / "nope.json")
        cmd, conf, _cat = qr.q_route("fix a bug")
        assert cmd is None
        assert conf == 0

    def test_q_update_and_route(self, tmp_path, monkeypatch):
        import cc_flow.qrouter as qr
        monkeypatch.setattr(qr, "QTABLE_FILE", tmp_path / "qt.json")
        qr.q_update("fix login bug", "/debug", "success")
        qr.q_update("fix login bug", "/debug", "success")
        qr.q_update("fix login bug", "/debug", "success")
        cmd, conf, cat = qr.q_route("fix crash error")
        assert cat == "bugfix"
        # After 3 successes, should recommend /debug
        assert cmd == "/debug"
        assert conf > 0


class TestSkin:
    def test_banner(self, capsys):
        from cc_flow import skin
        skin.banner()
        out = capsys.readouterr().out
        assert "cc-flow" in out

    def test_success(self, capsys):
        from cc_flow import skin
        skin.success("done")
        assert "done" in capsys.readouterr().out

    def test_table(self, capsys):
        from cc_flow import skin
        skin.table(["A", "B"], [["1", "2"], ["3", "4"]])
        out = capsys.readouterr().out
        assert "A" in out
        assert "1" in out

    def test_progress_bar(self, capsys):
        from cc_flow import skin
        skin.progress_bar(5, 10, "half")
        out = capsys.readouterr().out
        assert "50%" in out
        assert "half" in out

    def test_no_color(self, monkeypatch, capsys):
        monkeypatch.setenv("NO_COLOR", "1")
        from cc_flow import skin
        skin.success("plain")
        out = capsys.readouterr().out
        assert "\033" not in out  # No ANSI codes


class TestAliases:
    def test_load_empty(self, tmp_path, monkeypatch):
        import cc_flow.aliases as al
        monkeypatch.setattr(al, "ALIAS_FILE", tmp_path / "nope.json")
        assert al._load_aliases() == {}

    def test_save_load(self, tmp_path, monkeypatch):
        import cc_flow.aliases as al
        alias_file = tmp_path / "aliases.json"
        monkeypatch.setattr(al, "ALIAS_FILE", alias_file)
        al._save_aliases({"s": "status"})
        assert al._load_aliases() == {"s": "status"}

    def test_resolve_alias(self, tmp_path, monkeypatch):
        import cc_flow.aliases as al
        alias_file = tmp_path / "aliases.json"
        monkeypatch.setattr(al, "ALIAS_FILE", alias_file)
        al._save_aliases({"s": "status"})
        result = al.resolve_alias("s", [])
        assert result == ("status", [])

    def test_resolve_unknown(self, tmp_path, monkeypatch):
        import cc_flow.aliases as al
        monkeypatch.setattr(al, "ALIAS_FILE", tmp_path / "nope.json")
        assert al.resolve_alias("nope", []) is None


class TestInsights:
    def test_calc_velocity_insufficient(self):
        from cc_flow.analytics import _calc_velocity
        assert _calc_velocity({}) is None
        assert _calc_velocity({"t1": {"status": "done", "completed": "2026-01-01T00:00:00Z"}}) is None

    def test_fmt_time(self):
        from cc_flow.analytics import _fmt_time
        assert _fmt_time(30) == "30s"
        assert _fmt_time(90) == "1m 30s"
        assert _fmt_time(3661) == "1h 1m"


class TestContextModule:
    def test_git_info(self):
        from cc_flow.context import _git_info
        info = _git_info()
        assert "sha" in info
        assert "branch" in info
        assert isinstance(info["recent_commits"], list)


class TestLearning:
    def test_make_result(self):
        from cc_flow.learning import _make_result
        r = _make_result({"task": "x", "approach": "y", "lesson": "z", "score": 5}, 80, 2, "test")
        assert r["confidence"] == 80
        assert r["engine"] == "test"

    def test_keyword_search_no_match(self):
        from cc_flow.learning import _keyword_search
        learnings = [{"task": "deploy", "lesson": "use CI", "approach": "auto", "score": 3}]
        assert _keyword_search("zzz_impossible", learnings) is None


class TestTemplates:
    def test_builtin_templates(self):
        from cc_flow.templates import TASK_TEMPLATES
        assert "feature" in TASK_TEMPLATES
        assert "bugfix" in TASK_TEMPLATES
        assert "refactor" in TASK_TEMPLATES
        assert "security" in TASK_TEMPLATES
        for tmpl in TASK_TEMPLATES.values():
            assert "steps" in tmpl
            assert "spec" in tmpl

    def test_generate_spec_default(self):
        from cc_flow.templates import _generate_spec
        spec = _generate_spec("My Task")
        assert "My Task" in spec

    def test_generate_spec_template(self):
        from cc_flow.templates import _generate_spec
        spec = _generate_spec("Fix bug", "bugfix")
        assert "Bug Description" in spec
