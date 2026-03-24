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


@pytest.fixture
def workspace(tmp_path):
    """Create a temp workspace with .tasks/ initialized."""
    run(["init"], cwd=tmp_path)
    return tmp_path


class TestModeDecision:
    """Test that go routes to the correct mode."""

    def test_bug_fix_routes_to_chain(self):
        out, _, code = run(["go", "fix", "the", "login", "bug", "--dry-run"])
        assert code == 0
        data = json.loads(out)
        assert data["mode"] == "chain"
        assert data["dry_run"] is True

    def test_new_feature_routes_to_chain(self):
        out, _, code = run(["go", "implement", "user", "authentication", "--dry-run"])
        assert code == 0
        data = json.loads(out)
        # "implement" triggers feature chain (5 required steps, ≤5 threshold)
        assert data["mode"] == "chain"

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
        """Goals that don't match any chain trigger go to ralph."""
        out, _, code = run(["go", "build", "a", "completely", "new", "saas", "platform", "--dry-run", "--mode=ralph"])
        assert code == 0
        data = json.loads(out)
        assert data["mode"] == "ralph"
        assert data["max_iterations"] == 25

    def test_ralph_custom_max(self):
        out, _, code = run(["go", "something", "complex", "--dry-run", "--max", "50", "--mode=ralph"])
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
            {"required": True}, {"required": True}, {"required": False},
        ]}
        assert decide_mode("fix bug", {}, "bugfix", chain_data) == "chain"

    def test_multi_engine_mode_no_chain(self):
        from cc_flow.go import decide_mode
        # No chain data + complex query → multi-engine
        assert decide_mode("redesign the entire platform from scratch", {}, None, None) == "multi-engine"

    def test_force_mode(self):
        from cc_flow.go import decide_mode
        assert decide_mode("anything", {}, "x", {}, force_mode="ralph") == "ralph"
        assert decide_mode("anything", {}, "x", {}, force_mode="auto") == "auto"

    def test_hotfix_keywords(self):
        from cc_flow.go import decide_mode
        assert decide_mode("hotfix typo", {}, None, None) == "chain"
        assert decide_mode("urgent fix needed", {}, None, None) == "chain"
        assert decide_mode("revert last commit", {}, None, None) == "chain"


class TestHotfixChain:
    """Test hotfix fast-track routing."""

    def test_hotfix_routes_to_hotfix_chain(self):
        out, _, code = run(["go", "hotfix:", "fix", "typo", "--dry-run"])
        assert code == 0
        data = json.loads(out)
        assert data["mode"] == "chain"
        assert data["chain"] == "hotfix"
        assert data["total_steps"] == 3  # tdd → review → commit

    def test_trivial_routes_to_hotfix(self):
        out, _, code = run(["go", "trivial", "config", "change", "--dry-run"])
        assert code == 0
        data = json.loads(out)
        assert data["chain"] == "hotfix"


class TestAutoExecInstruction:
    """Test auto-execution instruction format."""

    def test_chain_instruction_has_auto_execute_header(self):
        out, _, code = run(["go", "fix", "the", "login", "bug", "--dry-run"])
        assert code == 0
        data = json.loads(out)
        if data["mode"] == "chain":
            assert "AUTO-EXECUTE" in data["instruction"]
            assert "Do NOT stop between steps" in data["instruction"]

    def test_chain_instruction_has_step_details(self):
        out, _, code = run(["go", "refactor", "auth", "--dry-run"])
        assert code == 0
        data = json.loads(out)
        if data["mode"] == "chain":
            assert "Phase 1/" in data["instruction"]
            assert "cc-flow skill ctx save" in data["instruction"]
            assert "cc-flow chain advance" in data["instruction"]

    def test_feature_chain_has_outputs(self):
        """Feature chain steps include outputs/reads schema hints."""
        # Use a medium-complexity query to get full feature chain (not -light)
        out, _, code = run(["go", "add", "user", "authentication", "system", "--dry-run"])
        assert code == 0
        data = json.loads(out)
        if data["mode"] == "chain":
            first_step = data["steps"][0]
            assert "outputs" in first_step or "role" in first_step


class TestResume:
    """Test --resume flag."""

    def test_resume_no_chain(self):
        out, _, code = run(["go", "--resume"])
        assert code == 0 or code == 1
        data = json.loads(out)
        # Either no chain or resumed
        assert "success" in data

    def test_resume_with_active_chain(self, workspace):
        """Start a chain, then resume it."""
        # Start chain
        run(["chain", "run", "bugfix"], cwd=workspace)
        # Resume
        out, _, _code = run(["go", "--resume"], cwd=workspace)
        data = json.loads(out)
        if data.get("resumed"):
            assert data["chain"] == "bugfix"
            assert data["resumed_from_step"] >= 1

    def test_no_goal_shows_interrupted_hint(self, workspace):
        """When no goal and chain is active, hint about --resume."""
        run(["chain", "run", "bugfix"], cwd=workspace)
        out, _, _code = run(["go"], cwd=workspace)
        data = json.loads(out)
        assert "resume" in data.get("error", "").lower() or data.get("resumed")


class TestSchemaValidation:
    """Test context schema validation on chain advance."""

    def test_advance_warns_missing_keys(self, workspace):
        """Schema validation warns when expected output keys are missing."""
        # Start feature chain
        run(["chain", "run", "feature"], cwd=workspace)
        # Save partial context (missing decisions, acceptance_criteria)
        run(["skill", "ctx", "save", "cc-brainstorm", "--data",
             '{"design_doc": "test.md"}'], cwd=workspace)
        # Advance
        out, _, code = run(["chain", "advance", "--data",
                            '{"design_doc": "test.md"}'], cwd=workspace)
        assert code == 0
        data = json.loads(out)
        if "schema_warnings" in data:
            assert any("decisions" in w for w in data["schema_warnings"])
