"""Tests for pua_engine.py — 3-model mutual PUA."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from cc_flow.pua_engine import _count_challenges, _parse_verdict


class TestParseVerdict:
    def test_passed(self):
        assert _parse_verdict("Everything looks clean. Verdict: PASSED") == "PASSED"

    def test_no_issues(self):
        assert _parse_verdict("NO_ISSUES_FOUND") == "PASSED"

    def test_challenged(self):
        assert _parse_verdict("Found 3 issues. Verdict: CHALLENGED") == "CHALLENGED"

    def test_default_challenged(self):
        assert _parse_verdict("Here are the problems...") == "CHALLENGED"


class TestCountChallenges:
    def test_severity_format(self):
        text = """
1. [SEVERITY: high] Missing validation
2. [SEVERITY: medium] Unused import
3. [SEVERITY: low] Style issue
"""
        assert _count_challenges(text) == 3

    def test_no_challenges(self):
        assert _count_challenges("Everything looks good") == 0

    def test_mixed_format(self):
        text = """
1. [critical] SQL injection in auth.py
2. [high] Missing error handling
"""
        assert _count_challenges(text) == 2
