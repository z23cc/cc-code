"""Unit tests for context_budget, modes, repl, and worktree_cmd modules."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace

# Ensure cc_flow package is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from cc_flow.context_budget import (
    _estimate_tokens,
    _read_file_tokens,
    _scan_agents,
    _scan_hooks,
    _scan_rules,
    _scan_skills,
)
from cc_flow.modes import get_modes, set_mode
from cc_flow.repl import _COMPLETIONS, _repl_help, _repl_help_all
from cc_flow.worktree_cmd import _worktree_sh, cmd_worktree

# ---------------------------------------------------------------------------
# context_budget
# ---------------------------------------------------------------------------


class TestEstimateTokens:
    def test_empty_string(self):
        assert _estimate_tokens("") == 0

    def test_short_string(self):
        # 12 chars -> 3 tokens
        assert _estimate_tokens("hello world!") == 3

    def test_longer_string(self):
        text = "a" * 400
        assert _estimate_tokens(text) == 100


class TestReadFileTokens:
    def test_existing_file(self, tmp_path):
        f = tmp_path / "sample.txt"
        f.write_text("a" * 80)  # 80 chars -> 20 tokens
        assert _read_file_tokens(f) == 20

    def test_missing_file(self, tmp_path):
        f = tmp_path / "nope.txt"
        assert _read_file_tokens(f) == 0


class TestScanRules:
    def test_no_rules_dir(self, tmp_path):
        count, tokens = _scan_rules(tmp_path)
        assert count == 0
        assert tokens == 0

    def test_with_rules(self, tmp_path):
        rules = tmp_path / "rules"
        rules.mkdir()
        (rules / "a.md").write_text("x" * 40)
        (rules / "b.md").write_text("y" * 80)
        count, tokens = _scan_rules(tmp_path)
        assert count == 2
        assert tokens == 10 + 20  # 40/4 + 80/4


class TestScanHooks:
    def test_no_hooks(self, tmp_path):
        count, tokens = _scan_hooks(tmp_path)
        assert count == 0
        assert tokens == 0

    def test_hooks_in_hooks_dir(self, tmp_path):
        hdir = tmp_path / "hooks"
        hdir.mkdir()
        (hdir / "hooks.json").write_text('{"hooks": {}}')
        count, tokens = _scan_hooks(tmp_path)
        assert count == 1
        assert tokens > 0

    def test_hooks_in_dot_claude(self, tmp_path):
        cdir = tmp_path / ".claude"
        cdir.mkdir()
        (cdir / "hooks.json").write_text('{"hooks": {}}')
        count, tokens = _scan_hooks(tmp_path)
        assert count == 1
        assert tokens > 0


class TestScanAgents:
    def test_no_agents(self, tmp_path):
        count, tokens = _scan_agents(tmp_path)
        assert count == 0
        assert tokens == 0

    def test_with_agents(self, tmp_path):
        adir = tmp_path / "agents"
        adir.mkdir()
        (adir / "worker.md").write_text("z" * 120)
        count, tokens = _scan_agents(tmp_path)
        assert count == 1
        assert tokens == 30


class TestScanSkills:
    def test_no_skills(self, tmp_path):
        count, tokens = _scan_skills(tmp_path)
        assert count == 0
        assert tokens == 0

    def test_with_skills(self, tmp_path):
        sdir = tmp_path / "skills" / "cc-plan"
        sdir.mkdir(parents=True)
        (sdir / "SKILL.md").write_text("a" * 600)  # 600 chars -> 150 tokens -> //3 = 50
        count, tokens = _scan_skills(tmp_path)
        assert count == 1
        assert tokens == 50  # max(50, 50)


# ---------------------------------------------------------------------------
# modes
# ---------------------------------------------------------------------------


class TestGetModes:
    def test_defaults_when_no_file(self, monkeypatch, tmp_path):
        monkeypatch.setattr("cc_flow.modes._modes_file", lambda: tmp_path / "modes.json")
        modes = get_modes()
        assert modes == {"careful": False, "freeze": False, "freeze_dir": "", "guard": False}

    def test_reads_existing(self, monkeypatch, tmp_path):
        f = tmp_path / "modes.json"
        f.write_text(json.dumps({"careful": True, "freeze": False, "freeze_dir": "", "guard": False}))
        monkeypatch.setattr("cc_flow.modes._modes_file", lambda: f)
        modes = get_modes()
        assert modes["careful"] is True

    def test_corrupt_json_returns_defaults(self, monkeypatch, tmp_path):
        f = tmp_path / "modes.json"
        f.write_text("{bad json")
        monkeypatch.setattr("cc_flow.modes._modes_file", lambda: f)
        modes = get_modes()
        assert modes["careful"] is False


class TestSetMode:
    def test_enable_careful(self, monkeypatch, tmp_path):
        f = tmp_path / "modes.json"
        monkeypatch.setattr("cc_flow.modes._modes_file", lambda: f)
        result = set_mode("careful", True)
        assert result["careful"] is True
        # Persisted to disk
        assert json.loads(f.read_text())["careful"] is True

    def test_disable_careful(self, monkeypatch, tmp_path):
        f = tmp_path / "modes.json"
        monkeypatch.setattr("cc_flow.modes._modes_file", lambda: f)
        set_mode("careful", True)
        result = set_mode("careful", False)
        assert result["careful"] is False

    def test_guard_enables_both(self, monkeypatch, tmp_path):
        f = tmp_path / "modes.json"
        monkeypatch.setattr("cc_flow.modes._modes_file", lambda: f)
        result = set_mode("guard", True, freeze_dir="/tmp")
        assert result["guard"] is True
        assert result["careful"] is True
        assert result["freeze"] is True
        assert result["freeze_dir"] == "/tmp"

    def test_guard_disable_clears_all(self, monkeypatch, tmp_path):
        f = tmp_path / "modes.json"
        monkeypatch.setattr("cc_flow.modes._modes_file", lambda: f)
        set_mode("guard", True, freeze_dir="/tmp")
        result = set_mode("guard", False)
        assert result["guard"] is False
        assert result["careful"] is False
        assert result["freeze"] is False
        assert result["freeze_dir"] == ""

    def test_freeze_with_dir(self, monkeypatch, tmp_path):
        f = tmp_path / "modes.json"
        monkeypatch.setattr("cc_flow.modes._modes_file", lambda: f)
        result = set_mode("freeze", True, freeze_dir="/some/path")
        assert result["freeze"] is True
        assert result["freeze_dir"] == "/some/path"

    def test_freeze_disable_clears_dir(self, monkeypatch, tmp_path):
        f = tmp_path / "modes.json"
        monkeypatch.setattr("cc_flow.modes._modes_file", lambda: f)
        set_mode("freeze", True, freeze_dir="/some/path")
        result = set_mode("freeze", False)
        assert result["freeze"] is False
        assert result["freeze_dir"] == ""


# ---------------------------------------------------------------------------
# repl
# ---------------------------------------------------------------------------


class TestReplHelp:
    def test_repl_help_runs(self, capsys):
        _repl_help()
        out = capsys.readouterr().out
        assert "go" in out.lower()

    def test_repl_help_all_runs(self, capsys):
        _repl_help_all()
        out = capsys.readouterr().out
        assert "Automation" in out


class TestCompletions:
    def test_completions_is_list(self):
        assert isinstance(_COMPLETIONS, list)

    def test_completions_not_empty(self):
        assert len(_COMPLETIONS) > 50

    def test_core_commands_present(self):
        for cmd in ["dashboard", "go", "help", "quit", "verify", "ralph"]:
            assert cmd in _COMPLETIONS, f"{cmd} missing from _COMPLETIONS"

    def test_subcommands_present(self):
        for cmd in ["worktree create", "chain run", "rp check"]:
            assert cmd in _COMPLETIONS, f"{cmd} missing from _COMPLETIONS"


# ---------------------------------------------------------------------------
# worktree_cmd
# ---------------------------------------------------------------------------


class TestWorktreeSh:
    def test_finds_via_file_relative(self):
        # _worktree_sh falls back to Path(__file__).parent.parent / "worktree.sh"
        # which is scripts/worktree.sh — it should exist in this repo
        result = _worktree_sh()
        if result is not None:
            assert result.endswith("worktree.sh")

    def test_finds_via_env(self, monkeypatch, tmp_path):
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "worktree.sh").write_text("#!/bin/bash\n")
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
        result = _worktree_sh()
        assert result is not None
        assert result.endswith("worktree.sh")


class TestCmdWorktreeDispatch:
    def test_unknown_subcommand_exits(self):
        """Unknown subcommand should call error() which does sys.exit."""
        args = SimpleNamespace(wt_cmd="nonexistent")
        try:
            cmd_worktree(args)
            raise AssertionError("Should have raised SystemExit")
        except SystemExit:
            pass

    def test_no_subcommand_calls_info(self, monkeypatch):
        """No subcommand should call _cmd_info which calls _current_worktree_info."""
        called = {}

        def fake_info(a):
            called["info"] = True
            # _cmd_info prints JSON — fake it
            print('{"success": true, "in_worktree": false}')

        monkeypatch.setattr("cc_flow.worktree_cmd._cmd_info", fake_info)
        args = SimpleNamespace(wt_cmd=None)
        cmd_worktree(args)
        assert called.get("info") is True
