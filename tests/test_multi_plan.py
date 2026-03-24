"""Tests for multi_plan.py — 3-engine collaborative planning."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from cc_flow.multi_plan import _parse_verdict


class TestParseVerdict:
    def test_approve(self):
        assert _parse_verdict("Verdict: APPROVE — solid plan") == "APPROVE"

    def test_revise(self):
        assert _parse_verdict("Verdict: REVISE — needs work on error handling") == "REVISE"

    def test_rethink(self):
        assert _parse_verdict("RETHINK the entire approach") == "RETHINK"

    def test_unknown(self):
        assert _parse_verdict("no verdict here") == "UNKNOWN"

    def test_approve_in_text(self):
        assert _parse_verdict("I approve this plan") == "APPROVE"
