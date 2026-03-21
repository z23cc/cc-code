"""Tests for cc-flow CLI — covers core task management lifecycle."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

CC_FLOW = [sys.executable, str(Path(__file__).parent.parent / "scripts" / "cc-flow.py")]


def run(args, cwd=None):
    result = subprocess.run(CC_FLOW + args, capture_output=True, text=True, cwd=cwd)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


@pytest.fixture
def workspace(tmp_path):
    """Create a temp workspace with .tasks/ initialized."""
    run(["init"], cwd=tmp_path)
    return tmp_path


class TestInit:
    def test_init_creates_directory(self, tmp_path):
        out, _, code = run(["init"], cwd=tmp_path)
        assert code == 0
        data = json.loads(out)
        assert data["success"] is True
        assert (tmp_path / ".tasks" / "meta.json").exists()

    def test_init_idempotent(self, workspace):
        out, _, code = run(["init"], cwd=workspace)
        assert code == 0


class TestEpic:
    def test_create_epic(self, workspace):
        out, _, code = run(["epic", "create", "--title", "Auth System"], cwd=workspace)
        assert code == 0
        data = json.loads(out)
        assert data["success"] is True
        assert "epic-1-auth-system" in data["id"]

    def test_create_multiple_epics(self, workspace):
        run(["epic", "create", "--title", "First"], cwd=workspace)
        out, _, _ = run(["epic", "create", "--title", "Second"], cwd=workspace)
        data = json.loads(out)
        assert "epic-2" in data["id"]


class TestTask:
    def test_create_task(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        out, _, code = run(["task", "create", "--epic", "epic-1-test", "--title", "Task 1"], cwd=workspace)
        assert code == 0
        data = json.loads(out)
        assert data["id"] == "epic-1-test.1"

    def test_create_task_with_size(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        out, _, _ = run(["task", "create", "--epic", "epic-1-test", "--title", "Small", "--size", "XS"], cwd=workspace)
        data = json.loads(out)
        task_json = json.loads((workspace / ".tasks" / "tasks" / f"{data['id']}.json").read_text())
        assert task_json["size"] == "XS"

    def test_create_task_with_deps(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        out, _, _ = run(["task", "create", "--epic", "epic-1-test", "--title", "T2", "--deps", "epic-1-test.1"], cwd=workspace)
        data = json.loads(out)
        task_json = json.loads((workspace / ".tasks" / "tasks" / f"{data['id']}.json").read_text())
        assert "epic-1-test.1" in task_json["depends_on"]


class TestLifecycle:
    def test_start_done(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        out, _, _ = run(["start", "epic-1-test.1"], cwd=workspace)
        assert json.loads(out)["status"] == "in_progress"
        out, _, _ = run(["done", "epic-1-test.1", "--summary", "done"], cwd=workspace)
        assert json.loads(out)["status"] == "done"

    def test_start_respects_deps(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T2", "--deps", "epic-1-test.1"], cwd=workspace)
        _, _, code = run(["start", "epic-1-test.2"], cwd=workspace)
        assert code == 1  # Should fail — dep not done

    def test_block_and_reset(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        run(["start", "epic-1-test.1"], cwd=workspace)
        out, _, _ = run(["block", "epic-1-test.1", "--reason", "waiting"], cwd=workspace)
        assert json.loads(out)["status"] == "blocked"
        out, _, _ = run(["task", "reset", "epic-1-test.1"], cwd=workspace)
        assert json.loads(out)["status"] == "todo"


class TestViews:
    def test_list(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        out, _, code = run(["list", "--json"], cwd=workspace)
        assert code == 0
        data = json.loads(out)
        assert data["count"] == 1

    def test_status(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        out, _, _ = run(["status"], cwd=workspace)
        data = json.loads(out)
        assert data["tasks"] == 1
        assert data["todo"] == 1

    def test_ready(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        out, _, _ = run(["ready"], cwd=workspace)
        data = json.loads(out)
        assert len(data["ready"]) == 1

    def test_validate(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        out, _, code = run(["validate"], cwd=workspace)
        assert code == 0
        assert json.loads(out)["valid"] is True


class TestRoute:
    def test_route_feature(self, workspace):
        out, _, _ = run(["route", "implement", "new", "feature"], cwd=workspace)
        data = json.loads(out)
        assert data["suggestion"]["command"] == "/brainstorm"

    def test_route_bug(self, workspace):
        out, _, _ = run(["route", "fix", "broken", "login"], cwd=workspace)
        data = json.loads(out)
        assert data["suggestion"]["command"] == "/debug"

    def test_route_empty(self, workspace):
        _, _, code = run(["route"], cwd=workspace)
        assert code == 1


class TestLearn:
    def test_learn_and_search(self, workspace):
        run(["learn", "--task", "fix auth", "--outcome", "success",
             "--approach", "check middleware", "--lesson", "middleware first", "--score", "5"], cwd=workspace)
        out, _, _ = run(["learnings", "--search", "auth"], cwd=workspace)
        data = json.loads(out)
        assert data["count"] >= 1
        assert "middleware" in data["learnings"][0]["lesson"]


class TestVersion:
    def test_version(self):
        out, _, code = run(["version"])
        assert code == 0
        data = json.loads(out)
        assert "version" in data


class TestEpicImport:
    def test_import_creates_tasks(self, workspace):
        plan = workspace / "plan.md"
        plan.write_text("# Plan\n\n### Task 1: Alpha\nDo A\n\n### Task 2: Beta\nDo B\n")
        out, _, code = run(["epic", "import", "--file", str(plan)], cwd=workspace)
        assert code == 0
        lines = [ln for ln in out.split("\n") if ln.strip()]
        data = json.loads(lines[-1])
        assert data["tasks_created"] == 2


class TestEpicClose:
    def test_close_blocks_pending(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        _, _, code = run(["epic", "close", "epic-1-test"], cwd=workspace)
        assert code == 1

    def test_close_archives(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        run(["start", "epic-1-test.1"], cwd=workspace)
        run(["done", "epic-1-test.1", "--summary", "ok"], cwd=workspace)
        _, _, code = run(["epic", "close", "epic-1-test"], cwd=workspace)
        assert code == 0
        assert (workspace / ".tasks" / "completed" / "epic-1-test.md").exists()


class TestEpicReset:
    def test_resets_tasks(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        run(["start", "epic-1-test.1"], cwd=workspace)
        run(["epic", "reset", "epic-1-test"], cwd=workspace)
        t = json.loads((workspace / ".tasks" / "tasks" / "epic-1-test.1.json").read_text())
        assert t["status"] == "todo"


class TestDepAdd:
    def test_add_dep(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T2"], cwd=workspace)
        out, _, _ = run(["dep", "add", "epic-1-test.2", "epic-1-test.1"], cwd=workspace)
        assert "epic-1-test.1" in json.loads(out)["depends_on"]


class TestScan:
    def test_scan_clean(self, workspace):
        out, _, code = run(["scan"], cwd=workspace)
        assert code == 0
        assert json.loads(out)["total"] == 0


class TestArchive:
    def test_archive_empty(self, workspace):
        out, _, _ = run(["archive"], cwd=workspace)
        assert json.loads(out)["count"] == 0


class TestCheckpoint:
    def test_save_list_restore(self, workspace):
        subprocess.run(["git", "init", "-q"], cwd=workspace)
        subprocess.run(["git", "add", "."], cwd=workspace)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=workspace)
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        out, _, _ = run(["checkpoint", "save", "--name", "s1"], cwd=workspace)
        assert json.loads(out)["success"]
        out, _, _ = run(["checkpoint", "list"], cwd=workspace)
        assert len(json.loads(out)["checkpoints"]) == 1
        out, _, _ = run(["checkpoint", "restore", "s1"], cwd=workspace)
        assert "Resume" in out


class TestStats:
    def test_stats_runs(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        out, _, code = run(["stats"], cwd=workspace)
        assert code == 0
        assert "Productivity" in out


class TestVersionFlag:
    def test_version_flag(self):
        out, _, code = run(["--version"])
        assert code == 0
        assert "cc-flow" in out
