"""Tests for multi_review.py — multi-engine consensus review."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from cc_flow.multi_review import (
    SEVERITY_WEIGHTS,
    _consensus_message,
    _parse_engine_result,
    _parse_findings,
    _parse_verdict,
    build_consensus,
)


class TestParseVerdict:
    def test_ship(self):
        assert _parse_verdict("Everything looks good. Verdict: SHIP") == "SHIP"

    def test_needs_work(self):
        assert _parse_verdict("Found issues. NEEDS_WORK") == "NEEDS_WORK"

    def test_major_rethink(self):
        assert _parse_verdict("Fundamental problems. MAJOR_RETHINK required.") == "MAJOR_RETHINK"

    def test_unknown(self):
        assert _parse_verdict("No verdict here") == "UNKNOWN"

    def test_case_insensitive(self):
        assert _parse_verdict("verdict: ship") == "SHIP"
        assert _parse_verdict("NEEDS_work found") == "NEEDS_WORK"

    def test_major_wins_over_ship(self):
        assert _parse_verdict("SHIP for most, but MAJOR_RETHINK for auth") == "MAJOR_RETHINK"


class TestParseFindings:
    def test_severity_markers(self):
        text = (
            "high: Missing input validation in src/auth.py\n"
            "medium: Consider using dataclass instead of dict\n"
            "low: Style prefer f-strings\n"
        )
        findings = _parse_findings(text)
        assert len(findings) >= 2
        assert findings[0]["severity"] == "high"

    def test_no_findings(self):
        assert _parse_findings("All good, no issues.") == []


class TestParseEngineResult:
    def test_failed_engine(self):
        result = _parse_engine_result("codex", {"success": False, "error": "timeout"})
        assert result["status"] == "failed"
        assert result["verdict"] == "SKIPPED"

    def test_agent_structured(self):
        result = _parse_engine_result("agent", {
            "success": True,
            "output": "review done",
            "findings": [{"severity": "high", "file": "x.py", "description": "issue"}],
            "verdict": "NEEDS_WORK",
        })
        assert result["status"] == "completed"
        assert result["verdict"] == "NEEDS_WORK"
        assert len(result["findings"]) == 1

    def test_text_output(self):
        result = _parse_engine_result("codex", {
            "success": True,
            "output": "Found issues. Verdict: NEEDS_WORK",
        })
        assert result["verdict"] == "NEEDS_WORK"


class TestConsensus:
    def test_all_ship(self):
        reviews = [
            {"engine": "agent", "label": "A", "lens": "x", "status": "completed",
             "verdict": "SHIP", "findings": []},
            {"engine": "codex", "label": "B", "lens": "y", "status": "completed",
             "verdict": "SHIP", "findings": []},
        ]
        c = build_consensus(reviews)
        assert c["verdict"] == "SHIP"
        assert c["confidence"] == 100

    def test_worst_verdict_wins(self):
        reviews = [
            {"engine": "agent", "label": "A", "lens": "x", "status": "completed",
             "verdict": "SHIP", "findings": []},
            {"engine": "codex", "label": "B", "lens": "y", "status": "completed",
             "verdict": "NEEDS_WORK", "findings": [
                 {"severity": "high", "file": "a.py", "description": "missing validation"},
             ]},
        ]
        c = build_consensus(reviews)
        assert c["verdict"] == "NEEDS_WORK"
        assert c["confidence"] == 50

    def test_major_rethink_blocks(self):
        reviews = [
            {"engine": "agent", "label": "A", "lens": "x", "status": "completed",
             "verdict": "SHIP", "findings": []},
            {"engine": "rp", "label": "R", "lens": "z", "status": "completed",
             "verdict": "MAJOR_RETHINK", "findings": [
                 {"severity": "critical", "file": "b.py", "description": "security hole"},
             ]},
        ]
        c = build_consensus(reviews)
        assert c["verdict"] == "MAJOR_RETHINK"

    def test_no_completed_engines(self):
        reviews = [
            {"engine": "codex", "label": "B", "lens": "y", "status": "failed",
             "error": "timeout", "verdict": "SKIPPED", "findings": []},
        ]
        c = build_consensus(reviews)
        assert c["verdict"] == "UNKNOWN"
        assert c["confidence"] == 0

    def test_cross_reference_findings(self):
        reviews = [
            {"engine": "agent", "label": "A", "lens": "x", "status": "completed",
             "verdict": "NEEDS_WORK", "findings": [
                 {"severity": "high", "file": "auth.py", "description": "missing validation in login"},
             ]},
            {"engine": "codex", "label": "B", "lens": "y", "status": "completed",
             "verdict": "NEEDS_WORK", "findings": [
                 {"severity": "high", "file": "auth.py", "description": "missing validation in login handler"},
             ]},
        ]
        c = build_consensus(reviews)
        # Same file + similar description = high confidence
        assert c["total_findings"] == 2

    def test_severity_scores(self):
        reviews = [
            {"engine": "agent", "label": "A", "lens": "x", "status": "completed",
             "verdict": "NEEDS_WORK", "findings": [
                 {"severity": "critical", "description": "sql injection"},
                 {"severity": "low", "description": "style"},
             ]},
        ]
        c = build_consensus(reviews)
        assert c["engine_scores"]["agent"] == SEVERITY_WEIGHTS["critical"] + SEVERITY_WEIGHTS["low"]


class TestConsensusMessage:
    def test_all_agree(self):
        msg = _consensus_message("SHIP", 100, {"a": "SHIP", "b": "SHIP"})
        assert "All engines agree" in msg

    def test_blocked(self):
        msg = _consensus_message("MAJOR_RETHINK", 50, {"a": "SHIP", "b": "MAJOR_RETHINK"})
        assert "BLOCKED" in msg
