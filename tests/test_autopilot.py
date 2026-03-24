"""Tests for autopilot.py — 3-engine guided execution."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from cc_flow.autopilot import (
    _consensus_checkpoint,
    _detect_engines,
    _parse_checkpoint_verdict,
)


class TestParseCheckpointVerdict:
    def test_continue(self):
        assert _parse_checkpoint_verdict("All good. Verdict: CONTINUE") == "CONTINUE"

    def test_adjust(self):
        assert _parse_checkpoint_verdict("Need changes. Verdict: ADJUST") == "ADJUST"

    def test_stop(self):
        assert _parse_checkpoint_verdict("Critical issue. Verdict: STOP") == "STOP"

    def test_default_continue(self):
        assert _parse_checkpoint_verdict("no explicit verdict") == "CONTINUE"


class TestConsensusCheckpoint:
    def test_all_continue(self):
        responses = {
            "claude": "## Next Step Guidance\nProceed to phase 2\n## Plan Adjustments\nNone\n## Verdict: CONTINUE",
            "codex": "## Verdict: CONTINUE",
            "gemini": "## Verdict: CONTINUE",
        }
        c = _consensus_checkpoint(responses)
        assert c["verdict"] == "CONTINUE"
        assert len(c["guidance"]) >= 1

    def test_majority_adjust(self):
        responses = {
            "claude": "## Verdict: CONTINUE",
            "codex": "## Verdict: ADJUST",
            "gemini": "## Verdict: ADJUST",
        }
        c = _consensus_checkpoint(responses)
        assert c["verdict"] == "ADJUST"

    def test_extracts_adjustments(self):
        responses = {
            "claude": "## Plan Adjustments\nAdd error handling to the API layer\n## Verdict: ADJUST",
            "gemini": "## Verdict: CONTINUE",
        }
        c = _consensus_checkpoint(responses)
        assert len(c["adjustments"]) >= 1
        assert "error handling" in c["adjustments"][0].lower()

    def test_empty_responses(self):
        c = _consensus_checkpoint({})
        assert c["verdict"] == "CONTINUE"


class TestDetectEngines:
    def test_returns_dict(self):
        engines = _detect_engines()
        assert isinstance(engines, dict)
        # At least some engines should be detected in test env
