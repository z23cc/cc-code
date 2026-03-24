"""Unit tests for cc_flow.auto — OODA loop functions."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


from cc_flow.auto import (
    DEFAULT_TEAM,
    _find_auto_epic,
    _find_ready_tasks,
    _orient_findings,
    _recommend_team,
)


class TestRecommendTeam:
    """Test _recommend_team pattern matching."""

    def test_security_keyword(self):
        task = {"title": "Fix SQL injection in login"}
        result = _recommend_team(task)
        assert result["template"] == "security-fix"
        assert "security-reviewer" in result["agents"]

    def test_lint_keyword(self):
        task = {"title": "Fix ruff unused import F401"}
        result = _recommend_team(task)
        assert result["template"] == "lint-fix"

    def test_test_keyword(self):
        task = {"title": "Fix failing pytest assertion"}
        result = _recommend_team(task)
        assert result["template"] == "test-fix"

    def test_refactor_keyword(self):
        task = {"title": "Extract duplicate code into helper"}
        result = _recommend_team(task)
        assert result["template"] == "refactor"

    def test_doc_keyword(self):
        task = {"title": "Add missing docstrings to module"}
        result = _recommend_team(task)
        assert result["template"] == "docs"

    def test_type_keyword(self):
        task = {"title": "Fix mypy type annotation error"}
        result = _recommend_team(task)
        assert result["template"] == "type-fix"

    def test_performance_keyword(self):
        task = {"title": "Fix slow query bottleneck"}
        result = _recommend_team(task)
        assert result["template"] == "performance"

    def test_default_team(self):
        task = {"title": "Something completely unrelated xyz"}
        result = _recommend_team(task)
        assert result["template"] == "general-fix"
        assert result["match_score"] == 0

    def test_empty_title(self):
        task = {"title": ""}
        result = _recommend_team(task)
        assert result["template"] == DEFAULT_TEAM["template"]

    def test_match_score_counts_keywords(self):
        task = {"title": "Fix bandit security injection vulnerability"}
        result = _recommend_team(task)
        assert result["template"] == "security-fix"
        assert result["match_score"] >= 3


class TestOrientFindings:
    """Test _orient_findings priority ranking."""

    def test_empty_findings(self):
        result = _orient_findings({})
        assert result == []

    def test_severity_ordering(self):
        findings = {
            "lint": [
                {"severity": "P4", "message": "minor", "type": "lint"},
                {"severity": "P1", "message": "critical", "type": "lint"},
            ],
        }
        result = _orient_findings(findings)
        assert len(result) == 2
        assert result[0]["severity"] == "P1"
        assert result[1]["severity"] == "P4"

    def test_multiple_categories(self):
        findings = {
            "lint": [{"severity": "P3", "message": "lint issue", "type": "lint"}],
            "security": [{"severity": "P1", "message": "vuln", "type": "sec"}],
        }
        result = _orient_findings(findings)
        assert len(result) == 2
        assert result[0]["category"] == "security"

    def test_output_fields(self):
        findings = {
            "test": [{"severity": "P2", "message": "fail", "type": "test", "file": "x.py"}],
        }
        result = _orient_findings(findings)
        assert result[0]["category"] == "test"
        assert result[0]["file"] == "x.py"
        assert "score" in result[0]


class TestFindAutoEpic:
    """Test _find_auto_epic selection logic."""

    def test_explicit_epic(self):
        assert _find_auto_epic("my-epic") == "my-epic"

    def test_empty_explicit(self):
        # Just verify it doesn't crash; result depends on filesystem
        result = _find_auto_epic("")
        assert isinstance(result, str)


class TestFindReadyTasks:
    """Test _find_ready_tasks filtering."""

    def test_returns_list(self, monkeypatch):
        # Patch all_tasks to return controlled data
        monkeypatch.setattr("cc_flow.auto.all_tasks", lambda: {
            "t1": {"id": "t1", "epic": "e1", "status": "todo", "title": "A", "depends_on": []},
            "t2": {"id": "t2", "epic": "e1", "status": "done", "title": "B", "depends_on": []},
            "t3": {"id": "t3", "epic": "e2", "status": "todo", "title": "C", "depends_on": []},
        })
        ready = _find_ready_tasks("e1")
        assert len(ready) == 1
        assert ready[0]["id"] == "t1"

    def test_blocked_by_dep(self, monkeypatch):
        monkeypatch.setattr("cc_flow.auto.all_tasks", lambda: {
            "t1": {"id": "t1", "epic": "e1", "status": "todo", "title": "A", "depends_on": []},
            "t2": {"id": "t2", "epic": "e1", "status": "todo", "title": "B", "depends_on": ["t1"]},
        })
        ready = _find_ready_tasks("e1")
        assert len(ready) == 1
        assert ready[0]["id"] == "t1"

    def test_dep_satisfied(self, monkeypatch):
        monkeypatch.setattr("cc_flow.auto.all_tasks", lambda: {
            "t1": {"id": "t1", "epic": "e1", "status": "done", "title": "A", "depends_on": []},
            "t2": {"id": "t2", "epic": "e1", "status": "todo", "title": "B", "depends_on": ["t1"]},
        })
        ready = _find_ready_tasks("e1")
        assert len(ready) == 1
        assert ready[0]["id"] == "t2"

    def test_no_matching_epic(self, monkeypatch):
        monkeypatch.setattr("cc_flow.auto.all_tasks", lambda: {
            "t1": {"id": "t1", "epic": "e1", "status": "todo", "title": "A", "depends_on": []},
        })
        ready = _find_ready_tasks("nonexistent")
        assert ready == []
