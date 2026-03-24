"""Tests for adversarial_review.py — 3-engine debate."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from cc_flow.adversarial_review import (
    _compute_verdict,
    _parse_issues,
    _parse_verdict,
)


class TestParseVerdict:
    def test_ship(self):
        assert _parse_verdict("## Verdict: SHIP") == "SHIP"

    def test_needs_work(self):
        assert _parse_verdict("## Verdict: NEEDS_WORK") == "NEEDS_WORK"

    def test_major_rethink(self):
        assert _parse_verdict("MAJOR_RETHINK needed") == "MAJOR_RETHINK"

    def test_fallback_ship(self):
        assert _parse_verdict("I recommend we SHIP this") == "SHIP"

    def test_unknown(self):
        assert _parse_verdict("no verdict") == "UNKNOWN"


class TestParseIssues:
    def test_markdown_table(self):
        text = (
            "| **high** | `auth.py` | Missing validation |\n"
            "| **medium** | `db.py` | N+1 query |\n"
        )
        issues = _parse_issues(text)
        assert len(issues) == 2
        assert issues[0]["severity"] == "high"

    def test_no_table(self):
        assert _parse_issues("All clear") == []


class TestComputeVerdict:
    def _make(self, r1, r2, issues=None):
        return {"r1_verdict": r1, "r2_verdict": r2, "issues": issues or []}

    def test_unanimous_ship(self):
        results = {
            "claude": self._make("SHIP", "SHIP"),
            "codex": self._make("SHIP", "SHIP"),
            "gemini": self._make("SHIP", "SHIP"),
        }
        v, reason = _compute_verdict(results)
        assert v == "SHIP"
        assert "3/3" in reason

    def test_majority_needs_work(self):
        results = {
            "claude": self._make("SHIP", "SHIP"),
            "codex": self._make("NEEDS_WORK", "NEEDS_WORK"),
            "gemini": self._make("NEEDS_WORK", "NEEDS_WORK"),
        }
        v, _ = _compute_verdict(results)
        assert v == "NEEDS_WORK"

    def test_position_change_noted(self):
        results = {
            "claude": self._make("SHIP", "NEEDS_WORK"),  # changed!
            "codex": self._make("NEEDS_WORK", "NEEDS_WORK"),
            "gemini": self._make("NEEDS_WORK", "NEEDS_WORK"),
        }
        v, reason = _compute_verdict(results)
        assert v == "NEEDS_WORK"
        assert "changed" in reason.lower()

    def test_no_majority_with_critical(self):
        results = {
            "claude": self._make("SHIP", "SHIP"),
            "codex": self._make("NEEDS_WORK", "UNKNOWN"),
            "gemini": self._make("NEEDS_WORK", "UNKNOWN", [
                {"severity": "critical", "file": "x.py", "description": "vuln"},
            ]),
        }
        v, _ = _compute_verdict(results)
        assert v == "NEEDS_WORK"

    def test_two_engine_majority(self):
        results = {
            "claude": self._make("SHIP", "SHIP"),
            "gemini": self._make("SHIP", "SHIP"),
        }
        v, _ = _compute_verdict(results)
        assert v == "SHIP"
