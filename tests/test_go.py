"""Tests for cc-flow go — unified automation entry point."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

CC_FLOW = [sys.executable, str(Path(__file__).parent.parent / "scripts" / "cc-flow.py")]


def run(args, cwd=None):
    result = subprocess.run(CC_FLOW + args, check=False, capture_output=True, text=True, cwd=cwd)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


class TestModeDecision:
    """Test that go routes to the correct mode."""

    def test_bug_fix_routes_to_chain(self):
        out, _, code = run(["go", "fix", "the", "login", "bug", "--dry-run"])
        assert code == 0
        data = json.loads(out)
        assert data["mode"] == "chain"
        assert data["dry_run"] is True

    def test_new_feature_routes_to_ralph(self):
        out, _, code = run(["go", "implement", "user", "authentication", "--dry-run"])
        assert code == 0
        data = json.loads(out)
        assert data["mode"] == "ralph"

    def test_improve_routes_to_auto(self):
        out, _, code = run(["go", "improve", "code", "quality", "--dry-run"])
        assert code == 0
        data = json.loads(out)
        assert data["mode"] == "auto"

    def test_scan_routes_to_auto(self):
        out, _, code = run(["go", "scan", "for", "lint", "errors", "--dry-run"])
        assert code == 0
        data = json.loads(out)
        assert data["mode"] == "auto"

    def test_refactor_routes_to_chain(self):
        out, _, code = run(["go", "refactor", "auth", "module", "--dry-run"])
        assert code == 0
        data = json.loads(out)
        assert data["mode"] == "chain"
        assert data["chain"] == "refactor"

    def test_deploy_routes_to_chain(self):
        out, _, code = run(["go", "deploy", "to", "production", "--dry-run"])
        assert code == 0
        data = json.loads(out)
        assert data["mode"] == "chain"
        assert data["chain"] == "deploy"

    def test_security_audit_routes_to_chain(self):
        out, _, code = run(["go", "security", "audit", "--dry-run"])
        assert code == 0
        data = json.loads(out)
        assert data["mode"] == "chain"


class TestForceMode:
    """Test --mode flag overrides routing."""

    def test_force_ralph(self):
        out, _, code = run(["go", "fix", "bug", "--mode=ralph", "--dry-run"])
        assert code == 0
        data = json.loads(out)
        assert data["mode"] == "ralph"

    def test_force_auto(self):
        out, _, code = run(["go", "fix", "bug", "--mode=auto", "--dry-run"])
        assert code == 0
        data = json.loads(out)
        assert data["mode"] == "auto"

    def test_force_chain(self):
        out, _, code = run(["go", "something", "random", "--mode=chain", "--dry-run"])
        assert code == 0
        data = json.loads(out)
        # When forced to chain but no chain matches, falls through to ralph
        assert data["mode"] in ("chain", "ralph")


class TestChainMode:
    """Test chain mode output."""

    def test_chain_has_steps(self):
        out, _, code = run(["go", "fix", "the", "login", "bug", "--dry-run"])
        assert code == 0
        data = json.loads(out)
        if data["mode"] == "chain":
            assert "steps" in data
            assert len(data["steps"]) > 0
            assert data["total_steps"] > 0

    def test_chain_steps_have_required_fields(self):
        out, _, code = run(["go", "refactor", "auth", "--dry-run"])
        assert code == 0
        data = json.loads(out)
        if data["mode"] == "chain":
            for step in data["steps"]:
                assert "step" in step
                assert "skill" in step
                assert "role" in step
                assert "required" in step


class TestRalphMode:
    """Test ralph mode output."""

    def test_ralph_has_goal(self):
        out, _, code = run(["go", "implement", "user", "auth", "--dry-run"])
        assert code == 0
        data = json.loads(out)
        assert data["mode"] == "ralph"
        assert "implement user auth" in data["goal"]
        assert data["max_iterations"] == 25

    def test_ralph_custom_max(self):
        out, _, code = run(["go", "implement", "user", "auth", "--dry-run", "--max", "50"])
        assert code == 0
        data = json.loads(out)
        assert data["mode"] == "ralph"
        assert data["max_iterations"] == 50


class TestAutoMode:
    """Test auto mode output."""

    def test_auto_has_instruction(self):
        out, _, code = run(["go", "improve", "quality", "--dry-run"])
        assert code == 0
        data = json.loads(out)
        assert data["mode"] == "auto"
        assert "instruction" in data


class TestDecideModePure:
    """Unit tests for decide_mode function."""

    def test_auto_keywords(self):
        from cc_flow.go import decide_mode
        assert decide_mode("improve code", {}, None, None) == "auto"
        assert decide_mode("scan for issues", {}, None, None) == "auto"
        assert decide_mode("autoimmune run", {}, None, None) == "auto"

    def test_chain_mode_small(self):
        from cc_flow.go import decide_mode
        chain_data = {"skills": [
            {"required": True}, {"required": True}, {"required": False}
        ]}
        assert decide_mode("fix bug", {}, "bugfix", chain_data) == "chain"

    def test_ralph_mode_no_chain(self):
        from cc_flow.go import decide_mode
        assert decide_mode("build something new", {}, None, None) == "ralph"

    def test_force_mode(self):
        from cc_flow.go import decide_mode
        assert decide_mode("anything", {}, "x", {}, force_mode="ralph") == "ralph"
        assert decide_mode("anything", {}, "x", {}, force_mode="auto") == "auto"
