"""Tests for morph_client.py — Morph API Python client.

Tests are split into:
- Unit tests (no API key needed, test logic only)
- Integration tests (need MORPH_API_KEY, marked with @pytest.mark.morph)
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from morph_client import MorphClient

# ── Unit Tests (no API needed) ──

class TestMorphClientInit:
    def test_init_with_key(self):
        client = MorphClient(api_key="test-key")
        assert client.api_key == "test-key"

    def test_init_from_env(self):
        with patch.dict(os.environ, {"MORPH_API_KEY": "env-key"}):
            client = MorphClient()
            assert client.api_key == "env-key"

    def test_init_no_key_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("MORPH_API_KEY", None)
            with pytest.raises(ValueError, match="MORPH_API_KEY"):
                MorphClient()


class TestToolExecution:
    def test_execute_grep(self, tmp_path):
        (tmp_path / "test.py").write_text("def hello():\n    pass\n")
        client = MorphClient(api_key="fake")
        result = client._execute_tool("grep_search", {"pattern": "hello", "path": str(tmp_path)}, tmp_path)
        assert "hello" in result

    def test_execute_read(self, tmp_path):
        (tmp_path / "test.py").write_text("line1\nline2\nline3\n")
        client = MorphClient(api_key="fake")
        result = client._execute_tool(
            "read",
            {"path": str(tmp_path / "test.py"), "start_line": 2, "end_line": 3},
            tmp_path,
        )
        assert "line2" in result

    def test_execute_list_directory(self, tmp_path):
        (tmp_path / "a.py").write_text("")
        (tmp_path / "b.py").write_text("")
        client = MorphClient(api_key="fake")
        result = client._execute_tool("list_directory", {"path": str(tmp_path)}, tmp_path)
        assert "a.py" in result
        assert "b.py" in result

    def test_execute_read_nonexistent(self, tmp_path):
        client = MorphClient(api_key="fake")
        result = client._execute_tool("read", {"path": str(tmp_path / "nope.py")}, tmp_path)
        assert "not found" in result.lower()

    def test_execute_finish(self, tmp_path):
        client = MorphClient(api_key="fake")
        result = client._execute_tool("finish", {"result": "done"}, tmp_path)
        assert result == "done"


# ── Integration Tests (need MORPH_API_KEY) ──

morph = pytest.mark.skipif(
    not os.environ.get("MORPH_API_KEY"),
    reason="MORPH_API_KEY not set",
)


@morph
class TestMorphApply:
    def test_apply_simple(self):
        client = MorphClient()
        result = client.apply("change x to 42", "x = 1\ny = 2", "x = 42")
        assert "42" in result
        assert "y = 2" in result

    def test_apply_file(self, tmp_path):
        f = tmp_path / "test.py"
        f.write_text("x = 1\n")
        client = MorphClient()
        _ = client.apply_file(str(f), "change to 99", "x = 99")
        assert "99" in f.read_text()


@morph
class TestMorphEmbed:
    def test_embed_single(self):
        client = MorphClient()
        try:
            vecs = client.embed("def hello(): pass")
        except RuntimeError as e:
            if "404" in str(e):
                pytest.skip("Morph embed endpoint not available")
            raise
        assert len(vecs) == 1
        assert len(vecs[0]) == 1536

    def test_embed_batch(self):
        client = MorphClient()
        try:
            vecs = client.embed(["code1", "code2", "code3"])
        except RuntimeError as e:
            if "404" in str(e):
                pytest.skip("Morph embed endpoint not available")
            raise
        assert len(vecs) == 3


@morph
class TestMorphRerank:
    def test_rerank_basic(self):
        client = MorphClient()
        try:
            results = client.rerank(
                "authentication",
                ["login handler", "CSS styles", "auth middleware"],
                top_n=2,
            )
        except RuntimeError as e:
            if "404" in str(e):
                pytest.skip("Morph rerank endpoint not available")
            raise
        assert len(results) == 2
        assert "relevance_score" in results[0]
        # Auth-related docs should rank higher
        assert results[0]["document"] in ("login handler", "auth middleware")


@morph
class TestMorphCompact:
    def test_compact_text(self):
        client = MorphClient()
        text = "This is a detailed explanation. " * 30
        result = client.compact(text, 0.3)
        # Result should be shorter than original
        assert len(result) < len(text)


@morph
class TestMorphSearch:
    def test_search_local(self, tmp_path):
        (tmp_path / "app.py").write_text("def authenticate_user(token):\n    return validate(token)\n")
        client = MorphClient()
        # WarpGrep search — may or may not work depending on API state
        # Just verify it doesn't crash
        try:
            result = client.search("authentication", str(tmp_path), max_turns=2)
            assert isinstance(result, str)
        except RuntimeError:
            pytest.skip("WarpGrep API unavailable")
