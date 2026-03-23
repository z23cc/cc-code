"""Unit tests for bridge module — Morph × RP × Supermemory collaboration."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from cc_flow.bridge import (
    _recall_memories,
    _save_memory,
    deep_search,
    memory_enhanced_chat,
    recall_for_review,
    review_to_memory,
    scan_to_memory,
    structure_to_embed,
)


class TestReviewToMemory:
    """P0-2: RP Review → Supermemory."""

    def test_ship_without_findings_skipped(self):
        """Routine SHIP verdicts without findings should not clutter memory."""
        result = review_to_memory("SHIP", "epic-1.1")
        assert result is False

    def test_ship_with_findings_saved(self):
        """SHIP with notable findings should be saved."""
        with patch("cc_flow.bridge._save_memory", return_value=True) as mock:
            result = review_to_memory("SHIP", "epic-1.1", findings="Good patterns noted")
            assert result is True
            assert mock.called
            content = mock.call_args[0][0]
            assert "SHIP" in content
            assert "epic-1.1" in content

    def test_needs_work_always_saved(self):
        """NEEDS_WORK verdicts should always be saved."""
        with patch("cc_flow.bridge._save_memory", return_value=True) as mock:
            result = review_to_memory("NEEDS_WORK", "epic-2.3", findings="SQL injection risk")
            assert result is True
            content = mock.call_args[0][0]
            assert "NEEDS_WORK" in content
            assert "SQL injection" in content

    def test_findings_truncated(self):
        """Long findings should be truncated to 500 chars."""
        with patch("cc_flow.bridge._save_memory", return_value=True) as mock:
            long_findings = "x" * 1000
            review_to_memory("NEEDS_WORK", "epic-1.1", findings=long_findings)
            content = mock.call_args[0][0]
            # Content should include truncated findings
            assert len(content) < 600  # verdict header + 500 chars

    def test_tags_include_verdict(self):
        """Tags should include the verdict level."""
        with patch("cc_flow.bridge._save_memory", return_value=True) as mock:
            review_to_memory("MAJOR_RETHINK", "epic-3.1", findings="Arch issue")
            tags = mock.call_args[0][1]
            assert "review" in tags
            assert "major_rethink" in tags


class TestScanToMemory:
    """P1-2: OODA findings → Supermemory."""

    def test_low_severity_skipped(self):
        """P3/P4 findings should not be saved."""
        findings = [
            {"severity": "P3", "message": "minor style issue"},
            {"severity": "P4", "message": "cosmetic"},
        ]
        result = scan_to_memory(findings)
        assert result["saved"] == 0
        assert result["skipped"] == 2

    def test_high_severity_saved(self):
        """P1/P2 findings should be saved."""
        findings = [
            {"severity": "P1", "category": "security", "message": "SQL injection"},
            {"severity": "P2", "category": "test", "message": "No tests for auth"},
            {"severity": "P4", "message": "cosmetic"},
        ]
        with patch("cc_flow.bridge._save_memory", return_value=True):
            result = scan_to_memory(findings, scan_type="deep")
            assert result["saved"] == 2

    def test_capped_at_10(self):
        """Should not save more than 10 findings per scan."""
        findings = [
            {"severity": "P1", "category": "test", "message": f"issue {i}"}
            for i in range(20)
        ]
        with patch("cc_flow.bridge._save_memory", return_value=True):
            result = scan_to_memory(findings)
            assert result["saved"] == 10


class TestRecallForReview:
    """P2-2: Supermemory → RP Review context."""

    def test_no_memories_returns_none(self):
        """Should return None when no memories found."""
        with patch("cc_flow.bridge._recall_memories", return_value=[]):
            result = recall_for_review("auth module")
            assert result is None

    def test_memories_formatted(self):
        """Should format recalled memories as bullet list."""
        with patch("cc_flow.bridge._recall_memories", return_value=[
            "Found SQL injection in auth.py last month",
            "Rate limiting was missing in API endpoints",
        ]):
            result = recall_for_review("auth module")
            assert "Past review findings" in result
            assert "SQL injection" in result
            assert "Rate limiting" in result


class TestRecallMemories:
    """Helper: _recall_memories."""

    def test_no_client_returns_empty(self):
        """Should return empty list when Supermemory unavailable."""
        with patch("cc_flow.bridge._get_supermemory", return_value=None):
            result = _recall_memories("query")
            assert result == []

    def test_api_error_returns_empty(self):
        """Should gracefully handle API errors."""
        mock_client = MagicMock()
        mock_client.search.execute.side_effect = RuntimeError("timeout")
        with patch("cc_flow.bridge._get_supermemory", return_value=mock_client):
            result = _recall_memories("query")
            assert result == []


class TestDeepSearch:
    """P0-1: Morph Search → RP Selection → RP Builder."""

    def test_no_morph_returns_steps(self):
        """Should record morph_search step even when unavailable."""
        with patch("cc_flow.core.get_morph_client", return_value=None), \
             patch("subprocess.run", side_effect=FileNotFoundError("no grep")):
            result = deep_search("test query")
            assert "steps" in result
            assert "query" in result
            assert result["query"] == "test query"

    def test_result_structure(self):
        """Result should have query, steps keys."""
        mock_morph = MagicMock()
        mock_morph.search.return_value = "src/auth.py:10: def login():\nsrc/auth.py:20: def logout():"
        with patch("cc_flow.core.get_morph_client", return_value=mock_morph), \
             patch("cc_flow.rp.is_available", return_value=False):
            result = deep_search("auth")
            assert result["query"] == "auth"
            assert len(result["steps"]) >= 1
            assert result["steps"][0]["tool"] == "morph_search"
            assert result["steps"][0]["files_found"] == 1  # src/auth.py deduped


class TestSaveMemory:
    """Helper: _save_memory."""

    def test_no_client_returns_false(self):
        """Should return False when Supermemory unavailable."""
        with patch("cc_flow.bridge._get_supermemory", return_value=None):
            result = _save_memory("content", ["tag"])
            assert result is False
