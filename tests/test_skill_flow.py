"""Tests for cc-flow skill flow — graph extraction, context protocol, CLI commands."""

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


@pytest.fixture
def skills_dir(tmp_path):
    """Create a minimal skills directory with test SKILL.md files."""
    skills = tmp_path / "skills"

    # cc-brainstorming — flows into cc-plan
    (skills / "cc-brainstorming").mkdir(parents=True)
    (skills / "cc-brainstorming" / "SKILL.md").write_text(
        '---\nname: cc-brainstorming\ndescription: >\n'
        '  Design exploration.\n'
        '  TRIGGER: brainstorm.\n'
        '  FLOWS INTO: cc-plan (turn design into plan).\n'
        '---\n# Brainstorm\n',
    )

    # cc-plan — depends on cc-brainstorming, flows into cc-tdd, cc-work
    (skills / "cc-plan").mkdir()
    (skills / "cc-plan" / "SKILL.md").write_text(
        '---\nname: cc-plan\ndescription: >\n'
        '  Create implementation plans.\n'
        '  DEPENDS ON: cc-brainstorming (design before planning).\n'
        '  FLOWS INTO: cc-tdd (implement), cc-work (execute end-to-end).\n'
        '---\n# Plan\n',
    )

    # cc-tdd — depends on cc-plan, flows into cc-review
    (skills / "cc-tdd").mkdir()
    (skills / "cc-tdd" / "SKILL.md").write_text(
        '---\nname: cc-tdd\ndescription: "Test-driven development. '
        'DEPENDS ON: cc-plan. '
        'FLOWS INTO: cc-review, cc-commit."\n'
        '---\n# TDD\n',
    )

    # cc-review — no flows (terminal)
    (skills / "cc-review").mkdir()
    (skills / "cc-review" / "SKILL.md").write_text(
        '---\nname: cc-review\ndescription: "Code review. TRIGGER: review."\n'
        '---\n# Review\n',
    )

    # cc-rp — used by cc-review
    (skills / "cc-rp").mkdir()
    (skills / "cc-rp" / "SKILL.md").write_text(
        '---\nname: cc-rp\ndescription: "RepoPrompt interface. '
        'USED BY: cc-review, cc-work."\n'
        '---\n# RP\n',
    )

    return skills


class TestBuildGraph:
    def test_parses_flows_into(self, skills_dir):
        from cc_flow.skill_flow import build_graph
        graph = build_graph(skills_dir)
        node = graph["nodes"]["cc-brainstorming"]
        assert "cc-plan" in node["flows_into"]

    def test_parses_depends_on(self, skills_dir):
        from cc_flow.skill_flow import build_graph
        graph = build_graph(skills_dir)
        node = graph["nodes"]["cc-plan"]
        assert "cc-brainstorming" in node["depends_on"]

    def test_parses_multiple_flows(self, skills_dir):
        from cc_flow.skill_flow import build_graph
        graph = build_graph(skills_dir)
        node = graph["nodes"]["cc-plan"]
        assert set(node["flows_into"]) == {"cc-tdd", "cc-work"}

    def test_parses_used_by(self, skills_dir):
        from cc_flow.skill_flow import build_graph
        graph = build_graph(skills_dir)
        node = graph["nodes"]["cc-rp"]
        assert "cc-review" in node["used_by"]
        assert "cc-work" in node["used_by"]

    def test_inline_description(self, skills_dir):
        """Inline quoted description format is parsed correctly."""
        from cc_flow.skill_flow import build_graph
        graph = build_graph(skills_dir)
        node = graph["nodes"]["cc-tdd"]
        assert "cc-plan" in node["depends_on"]
        assert "cc-review" in node["flows_into"]

    def test_terminal_skill_has_no_flows(self, skills_dir):
        from cc_flow.skill_flow import build_graph
        graph = build_graph(skills_dir)
        node = graph["nodes"]["cc-review"]
        assert node["flows_into"] == []
        assert node["depends_on"] == []

    def test_graph_has_version_and_timestamp(self, skills_dir):
        from cc_flow.skill_flow import build_graph
        graph = build_graph(skills_dir)
        assert graph["version"] == 1
        assert "built" in graph


class TestNameNormalization:
    def test_known_alias(self, skills_dir):
        from cc_flow.skill_flow import _build_alias_map, _normalize
        alias_map = _build_alias_map(skills_dir)
        assert _normalize("cc-brainstorm", alias_map) == "cc-brainstorming"

    def test_canonical_unchanged(self, skills_dir):
        from cc_flow.skill_flow import _build_alias_map, _normalize
        alias_map = _build_alias_map(skills_dir)
        assert _normalize("cc-plan", alias_map) == "cc-plan"

    def test_slash_prefix_stripped(self, skills_dir):
        from cc_flow.skill_flow import _build_alias_map, _normalize
        alias_map = _build_alias_map(skills_dir)
        assert _normalize("/cc-plan", alias_map) == "cc-plan"


class TestNextPrevSkills:
    def test_next_skills(self, skills_dir, monkeypatch):
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(skills_dir.parent))
        from cc_flow import skill_flow
        # Clear cached graph
        if skill_flow.SKILL_GRAPH_CACHE.exists():
            skill_flow.SKILL_GRAPH_CACHE.unlink()
        result = skill_flow.next_skills("cc-brainstorming")
        assert result == ["cc-plan"]

    def test_prev_skills(self, skills_dir, monkeypatch):
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(skills_dir.parent))
        from cc_flow import skill_flow
        if skill_flow.SKILL_GRAPH_CACHE.exists():
            skill_flow.SKILL_GRAPH_CACHE.unlink()
        result = skill_flow.prev_skills("cc-plan")
        assert result == ["cc-brainstorming"]


class TestSkillContext:
    def test_save_and_load(self, workspace, monkeypatch):
        monkeypatch.chdir(workspace)
        from cc_flow.skill_flow import load_skill_ctx, save_skill_ctx
        # Override skills dir to avoid needing real skills
        save_skill_ctx("cc-test", {"key": "value"})
        ctx = load_skill_ctx("cc-test")
        assert ctx is not None
        assert ctx["key"] == "value"
        assert ctx["skill"] == "cc-test"
        assert "timestamp" in ctx

    def test_load_nonexistent(self, workspace, monkeypatch):
        monkeypatch.chdir(workspace)
        from cc_flow.skill_flow import load_skill_ctx
        assert load_skill_ctx("cc-nonexistent") is None


class TestCurrentSkill:
    def test_set_and_get(self, workspace, monkeypatch):
        monkeypatch.chdir(workspace)
        from cc_flow.skill_flow import get_current, set_current
        set_current("cc-plan", chain_name="feature")
        current = get_current()
        assert current is not None
        assert current["skill"] == "cc-plan"
        assert current["chain"] == "feature"

    def test_clear(self, workspace, monkeypatch):
        monkeypatch.chdir(workspace)
        from cc_flow.skill_flow import clear_current, get_current, set_current
        set_current("cc-plan")
        clear_current()
        assert get_current() is None


class TestGraphCaching:
    def test_cache_hit(self, skills_dir, workspace, monkeypatch):
        monkeypatch.chdir(workspace)
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(skills_dir.parent))
        from cc_flow.skill_flow import SKILL_GRAPH_CACHE, load_graph
        # First call builds cache
        load_graph()
        assert SKILL_GRAPH_CACHE.exists()
        mtime1 = SKILL_GRAPH_CACHE.stat().st_mtime
        # Second call hits cache (file not rebuilt)
        load_graph()
        mtime2 = SKILL_GRAPH_CACHE.stat().st_mtime
        assert mtime1 == mtime2

    def test_cache_invalidation(self, skills_dir, workspace, monkeypatch):
        monkeypatch.chdir(workspace)
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(skills_dir.parent))
        import time

        from cc_flow.skill_flow import SKILL_GRAPH_CACHE, load_graph
        # Build cache
        load_graph()
        cache_mtime = SKILL_GRAPH_CACHE.stat().st_mtime
        # Touch a SKILL.md to invalidate
        time.sleep(0.1)
        skill_md = skills_dir / "cc-plan" / "SKILL.md"
        skill_md.write_text(skill_md.read_text() + "\n")
        # Should rebuild
        load_graph()
        new_mtime = SKILL_GRAPH_CACHE.stat().st_mtime
        assert new_mtime > cache_mtime


class TestCLI:
    def test_skill_graph_build(self):
        """Integration test: cc-flow skill graph-build works on real skills."""
        out, _, code = run(["skill", "graph-build"])
        assert code == 0
        data = json.loads(out)
        assert data["success"] is True
        assert data["total_skills"] > 0
        assert data["connected_skills"] > 0

    def test_skill_next(self):
        """Integration test: cc-flow skill next --skill works."""
        out, _, code = run(["skill", "next", "--skill", "cc-brainstorming"])
        assert code == 0
        data = json.loads(out)
        assert data["success"] is True
        assert "cc-plan" in data["next_skills"]

    def test_skill_graph_for(self):
        """Integration test: cc-flow skill graph --for works."""
        out, _, code = run(["skill", "graph", "--for", "cc-plan"])
        assert code == 0
        data = json.loads(out)
        assert data["success"] is True
        assert "flows_into" in data

    def test_skill_ctx_save_load(self, workspace):
        """Integration test: ctx save and load round-trip."""
        out, _, code = run(
            ["skill", "ctx", "save", "cc-test-skill", "--data", '{"foo": "bar"}'],
            cwd=workspace,
        )
        assert code == 0
        data = json.loads(out)
        assert data["success"] is True

        out, _, code = run(["skill", "ctx", "load", "cc-test-skill"], cwd=workspace)
        assert code == 0
        data = json.loads(out)
        assert data["success"] is True
        assert data["foo"] == "bar"
