"""Tests for adversarial_review.py — Ship Advocate vs Quality Gate."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from cc_flow.adversarial_review import (
    _final_verdict,
    _parse_issues_from_table,
    _parse_verdict,
)


class TestParseVerdict:
    def test_ship(self):
        assert _parse_verdict("## Verdict: SHIP") == "SHIP"

    def test_needs_work(self):
        assert _parse_verdict("## Verdict: NEEDS_WORK") == "NEEDS_WORK"

    def test_fallback_ship(self):
        assert _parse_verdict("I think this should SHIP") == "SHIP"

    def test_unknown(self):
        assert _parse_verdict("no verdict here") == "UNKNOWN"


class TestParseIssues:
    def test_markdown_table(self):
        text = (
            "| Severity | File | Issue |\n"
            "|----------|------|-------|\n"
            "| **high** | `auth.py` | Missing input validation |\n"
            "| **low** | `util.py` | Unused import |\n"
        )
        issues = _parse_issues_from_table(text)
        assert len(issues) == 2
        assert issues[0]["severity"] == "high"
        assert "auth.py" in issues[0]["file"]

    def test_no_table(self):
        assert _parse_issues_from_table("No issues found") == []


class TestFinalVerdict:
    def test_advocate_concedes(self):
        """If advocate changes to NEEDS_WORK in R2, gate wins."""
        v, reason, _ = _final_verdict(
            "Verdict: SHIP",      # advocate R1
            "Verdict: NEEDS_WORK",  # gate R1
            "Verdict: NEEDS_WORK",  # advocate R2 (conceded!)
            "Verdict: NEEDS_WORK",  # gate R2
        )
        assert v == "NEEDS_WORK"
        assert "conceded" in reason.lower()

    def test_gate_concedes(self):
        """If gate changes to SHIP in R2, advocate wins."""
        v, reason, _ = _final_verdict(
            "Verdict: SHIP",
            "Verdict: NEEDS_WORK",
            "Verdict: SHIP",
            "Verdict: SHIP",  # gate conceded!
        )
        assert v == "SHIP"
        assert "conceded" in reason.lower()

    def test_both_hold_no_critical(self):
        """Both hold but gate has only low issues → lean SHIP."""
        v, _, _ = _final_verdict(
            "Verdict: SHIP",
            "Verdict: NEEDS_WORK\n| low | x.py | minor style |",
            "Verdict: SHIP",
            "Verdict: NEEDS_WORK",
        )
        assert v == "SHIP"

    def test_both_hold_with_critical(self):
        """Both hold and gate has critical issue → NEEDS_WORK."""
        gate_r1 = (
            "| Severity | File | Issue |\n"
            "| critical | auth.py | SQL injection vulnerability |\n"
            "Verdict: NEEDS_WORK"
        )
        v, _, _ = _final_verdict(
            "Verdict: SHIP",
            gate_r1,
            "Verdict: SHIP",
            "Verdict: NEEDS_WORK",
        )
        assert v == "NEEDS_WORK"

    def test_all_verdicts_tracked(self):
        """All 4 round verdicts are returned."""
        _, _, verdicts = _final_verdict(
            "Verdict: SHIP", "Verdict: NEEDS_WORK",
            "Verdict: SHIP", "Verdict: NEEDS_WORK",
        )
        assert "advocate_r1" in verdicts
        assert "gate_r2" in verdicts
        assert verdicts["advocate_r1"] == "SHIP"
        assert verdicts["gate_r1"] == "NEEDS_WORK"
