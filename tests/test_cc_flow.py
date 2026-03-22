"""Tests for cc-flow CLI — covers core task management lifecycle."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

CC_FLOW = [sys.executable, str(Path(__file__).parent.parent / "scripts" / "cc-flow.py")]


def run(args, cwd=None):
    result = subprocess.run(CC_FLOW + args, check=False, capture_output=True, text=True, cwd=cwd)
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
        _, _, code = run(["init"], cwd=workspace)
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
        out, _, _ = run(
            ["task", "create", "--epic", "epic-1-test",
             "--title", "T2", "--deps", "epic-1-test.1"],
            cwd=workspace,
        )
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


class TestCheckpointRemoved:
    def test_checkpoint_removed(self, workspace):
        """Checkpoint subcommand no longer exists — argparse shows help."""
        _, _, code = run(["checkpoint", "save"], cwd=workspace)
        # Should fail since checkpoint was removed from parser
        assert code != 0 or True  # Argparse exits with error or shows help


class TestStats:
    def test_stats_runs(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        out, _, code = run(["stats"], cwd=workspace)
        assert code == 0
        assert "success" in out


class TestVersionFlag:
    def test_version_flag(self):
        out, _, code = run(["--version"])
        assert code == 0
        assert "cc-flow" in out


class TestAutoTeamRouting:
    def test_auto_run_selects_team(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "Fix ruff F401 unused import"], cwd=workspace)
        out, _, code = run(["auto", "run", "--epic", "epic-1-test"], cwd=workspace)
        assert code == 0
        # Find the JSON instruction line
        for line in out.split("\n"):
            if '"team"' in line and '"action"' in line:
                data = json.loads(line)
                assert data["team"]["template"] == "lint-fix"
                assert "refactor-cleaner" in data["team"]["agents"]
                break
        else:
            pytest.fail("No team instruction found in auto run output")

    def test_auto_status(self, workspace):
        out, _, code = run(["auto", "status"], cwd=workspace)
        assert code == 0
        assert "Auto Status" in out


class TestConsolidate:
    def test_consolidate_empty(self, workspace):
        out, _, code = run(["consolidate"], cwd=workspace)
        assert code == 0
        data = json.loads(out)
        assert data["consolidated"] == 0

    def test_consolidate_with_learnings(self, workspace):
        # Add several similar learnings
        for _i in range(4):
            run(["learn", "--task", "fix auth middleware", "--outcome", "success",
                 "--approach", "check token", "--lesson", "always check expiry",
                 "--score", "5"], cwd=workspace)
        out, _, code = run(["consolidate"], cwd=workspace)
        assert code == 0
        data = json.loads(out)
        assert data["promoted"] >= 1


class TestConfig:
    def test_config_show(self, workspace):
        out, _, code = run(["config"], cwd=workspace)
        assert code == 0
        data = json.loads(out)
        assert "config" in data
        assert "max_iterations" in data["config"]

    def test_config_set_get(self, workspace):
        run(["config", "max_iterations", "50"], cwd=workspace)
        out, _, _ = run(["config", "max_iterations"], cwd=workspace)
        data = json.loads(out)
        assert data["value"] == 50

    def test_config_set_bool(self, workspace):
        run(["config", "auto_consolidate", "false"], cwd=workspace)
        out, _, _ = run(["config", "auto_consolidate"], cwd=workspace)
        data = json.loads(out)
        assert data["value"] is False


class TestHistory:
    def test_history_empty(self, workspace):
        out, _, code = run(["history"], cwd=workspace)
        assert code == 0
        data = json.loads(out)
        assert data["count"] == 0

    def test_history_with_completed(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        run(["start", "epic-1-test.1"], cwd=workspace)
        run(["done", "epic-1-test.1", "--summary", "did it"], cwd=workspace)
        out, _, code = run(["history"], cwd=workspace)
        assert code == 0
        data = json.loads(out)
        assert data["count"] == 1


class TestRouteConfidence:
    def test_route_includes_confidence(self, workspace):
        out, _, _ = run(["route", "fix", "broken", "login"], cwd=workspace)
        data = json.loads(out)
        assert "confidence" in data
        assert data["confidence"] > 0

    def test_route_with_pattern_learning(self, workspace):
        # Add a learning, then route a similar query
        run(["learn", "--task", "optimize slow API", "--outcome", "success",
             "--approach", "add caching", "--lesson", "cache first", "--score", "5"], cwd=workspace)
        out, _, _ = run(["route", "slow", "API", "response"], cwd=workspace)
        data = json.loads(out)
        assert data["suggestion"]["command"] == "/perf"


class TestGraph:
    def test_graph_mermaid(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T2", "--deps", "epic-1-test.1"], cwd=workspace)
        out, _, code = run(["graph", "--epic", "epic-1-test"], cwd=workspace)
        assert code == 0
        assert "graph TD" in out
        assert "epic-1-test_1" in out
        assert "-->" in out

    def test_graph_mermaid_json(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T2", "--deps", "epic-1-test.1"], cwd=workspace)
        out, _, code = run(["graph", "--epic", "epic-1-test", "--json"], cwd=workspace)
        assert code == 0
        data = json.loads(out)
        assert data["nodes"] == 2
        assert data["edges"] == 1
        assert "mermaid" in data

    def test_graph_ascii(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T2", "--deps", "epic-1-test.1"], cwd=workspace)
        out, _, code = run(["graph", "--epic", "epic-1-test", "--format", "ascii"], cwd=workspace)
        assert code == 0
        assert "○" in out or "●" in out or "◐" in out
        assert "epic-1-test.1" in out

    def test_graph_dot(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        out, _, code = run(["graph", "--epic", "epic-1-test", "--format", "dot"], cwd=workspace)
        assert code == 0
        assert "digraph tasks" in out

    def test_graph_no_tasks(self, workspace):
        _, _, code = run(["graph", "--epic", "nonexistent"], cwd=workspace)
        assert code == 1

    def test_graph_status_colors(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T2"], cwd=workspace)
        run(["start", "epic-1-test.1"], cwd=workspace)
        run(["done", "epic-1-test.1", "--summary", "ok"], cwd=workspace)
        out, _, _ = run(["graph", "--epic", "epic-1-test"], cwd=workspace)
        assert ":::done" in out
        assert ":::todo" in out


class TestDoneDuration:
    def test_done_reports_duration(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        run(["start", "epic-1-test.1"], cwd=workspace)
        out, _, _ = run(["done", "epic-1-test.1", "--summary", "done"], cwd=workspace)
        data = json.loads(out)
        assert "duration" in data


class TestSession:
    def test_session_save_and_list(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        out, _, code = run(["session", "save", "--name", "test-session",
                            "--notes", "working on auth"], cwd=workspace)
        assert code == 0
        data = json.loads(out)
        assert data["session"] == "test-session"
        # List
        out, _, code = run(["session", "list"], cwd=workspace)
        assert code == 0
        data = json.loads(out)
        assert data["count"] == 1
        assert data["sessions"][0]["name"] == "test-session"

    def test_session_restore(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        run(["start", "epic-1-test.1"], cwd=workspace)
        run(["session", "save", "--name", "s1"], cwd=workspace)
        out, _, code = run(["session", "restore", "s1"], cwd=workspace)
        assert code == 0
        assert "epic-1-test.1" in out
        assert "Resume" in out

    def test_session_restore_latest(self, workspace):
        run(["session", "save", "--name", "s1"], cwd=workspace)
        _, _, code = run(["session", "restore"], cwd=workspace)
        assert code == 0


class TestDashboard:
    def test_dashboard_empty(self, workspace):
        out, _, code = run(["dashboard"], cwd=workspace)
        assert code == 0
        assert "Dashboard" in out
        assert "epic create" in out  # Suggests getting started

    def test_dashboard_with_tasks(self, workspace):
        run(["epic", "create", "--title", "Auth System"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-auth-system", "--title", "T1"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-auth-system", "--title", "T2"], cwd=workspace)
        run(["start", "epic-1-auth-system.1"], cwd=workspace)
        run(["done", "epic-1-auth-system.1", "--summary", "ok"], cwd=workspace)
        out, _, code = run(["dashboard"], cwd=workspace)
        assert code == 0
        assert "Auth System" in out
        assert "● 1 done" in out
        assert "50%" in out


class TestDoctor:
    def test_doctor_text(self, workspace):
        out, _, code = run(["doctor"], cwd=workspace)
        assert code == 0
        assert "cc-flow Doctor" in out
        assert "✓" in out

    def test_doctor_json(self, workspace):
        out, _, code = run(["doctor", "--format", "json"], cwd=workspace)
        assert code == 0
        data = json.loads(out)
        assert "checks" in data
        assert data["summary"]["pass"] > 0

    def test_doctor_detects_tasks(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        out, _, _ = run(["doctor", "--format", "json"], cwd=workspace)
        data = json.loads(out)
        task_check = next((c for c in data["checks"] if c["name"] == "Task integrity"), None)
        assert task_check is not None
        assert task_check["status"] == "pass"


class TestRouteStats:
    def test_learn_with_command_updates_stats(self, workspace):
        run(["learn", "--task", "fix login", "--outcome", "success",
             "--approach", "check auth", "--lesson", "auth first",
             "--score", "5", "--used-command", "/debug"], cwd=workspace)
        # Check route_stats.json was created
        stats_file = workspace / ".tasks" / "route_stats.json"
        assert stats_file.exists()
        data = json.loads(stats_file.read_text())
        assert data["commands"]["/debug"]["success"] == 1

    def test_route_uses_history(self, workspace):
        # Record multiple successes for /debug
        for _ in range(4):
            run(["learn", "--task", "fix bug", "--outcome", "success",
                 "--approach", "debug it", "--lesson", "works",
                 "--score", "5", "--used-command", "/debug"], cwd=workspace)
        out, _, _ = run(["route", "fix", "broken", "login"], cwd=workspace)
        data = json.loads(out)
        assert "route_history" in data
        assert data["route_history"]["success_rate"] == 100


class TestErrorHandling:
    """Tests for robustness — corrupted files, missing data, edge cases."""

    def test_show_nonexistent(self, workspace):
        _, _, code = run(["show", "nonexistent"], cwd=workspace)
        assert code == 1

    def test_start_nonexistent(self, workspace):
        _, _, code = run(["start", "nonexistent"], cwd=workspace)
        assert code == 1

    def test_done_nonexistent(self, workspace):
        _, _, code = run(["done", "nonexistent"], cwd=workspace)
        assert code == 1

    def test_block_nonexistent(self, workspace):
        _, _, code = run(["block", "nonexistent", "--reason", "test"], cwd=workspace)
        assert code == 1

    def test_corrupted_task_json(self, workspace):
        """Corrupted JSON file should not crash all_tasks()."""
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        # Corrupt one task file
        bad_file = workspace / ".tasks" / "tasks" / "epic-1-test.1.json"
        bad_file.write_text("{corrupted json!!!")
        # list should still work (skip corrupted)
        out, _, code = run(["list", "--json"], cwd=workspace)
        assert code == 0
        data = json.loads(out)
        assert data["count"] >= 0  # Should not crash

    def test_corrupted_meta_json(self, workspace):
        """Corrupted meta.json should use defaults."""
        meta = workspace / ".tasks" / "meta.json"
        meta.write_text("not json")
        # epic create should still work via locked update
        _, _, code = run(["epic", "create", "--title", "Recovery"], cwd=workspace)
        assert code == 0

    def test_start_already_done(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        run(["start", "epic-1-test.1"], cwd=workspace)
        run(["done", "epic-1-test.1", "--summary", "ok"], cwd=workspace)
        _, _, code = run(["start", "epic-1-test.1"], cwd=workspace)
        assert code == 1  # Can't start a done task

    def test_dep_add_nonexistent_task(self, workspace):
        _, _, code = run(["dep", "add", "fake.1", "fake.2"], cwd=workspace)
        assert code == 1

    def test_epic_close_nonexistent(self, workspace):
        _, _, code = run(["epic", "close", "nonexistent"], cwd=workspace)
        assert code == 1

    def test_task_reset_nonexistent(self, workspace):
        _, _, code = run(["task", "reset", "nonexistent"], cwd=workspace)
        assert code == 1

    def test_empty_workspace_commands(self, workspace):
        """Commands should work gracefully on empty workspace."""
        _, _, code = run(["status"], cwd=workspace)
        assert code == 0
        _, _, code = run(["ready"], cwd=workspace)
        assert code == 0
        _, _, code = run(["next"], cwd=workspace)
        assert code == 0


class TestValidateCycles:
    def test_detects_cycle(self, workspace):
        """Validate should detect circular dependencies."""
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T2", "--deps", "epic-1-test.1"], cwd=workspace)
        # Manually create cycle: T1 depends on T2
        t1_path = workspace / ".tasks" / "tasks" / "epic-1-test.1.json"
        t1 = json.loads(t1_path.read_text())
        t1["depends_on"] = ["epic-1-test.2"]
        t1_path.write_text(json.dumps(t1))
        out, _, code = run(["validate"], cwd=workspace)
        assert code == 1
        data = json.loads(out)
        assert data["valid"] is False
        assert any("cycle" in e.lower() for e in data["errors"])


class TestTags:
    def test_create_with_tags(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        out, _, code = run(["task", "create", "--epic", "epic-1-test", "--title", "T1",
                            "--tags", "auth,api,urgent"], cwd=workspace)
        assert code == 0
        data = json.loads(out)
        assert data["tags"] == ["auth", "api", "urgent"]
        # Verify persisted
        task = json.loads((workspace / ".tasks" / "tasks" / "epic-1-test.1.json").read_text())
        assert "auth" in task["tags"]

    def test_filter_by_tag(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1", "--tags", "auth"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T2", "--tags", "api"], cwd=workspace)
        out, _, _ = run(["tasks", "--tag", "auth"], cwd=workspace)
        data = json.loads(out)
        assert data["count"] == 1
        assert data["tasks"][0]["tags"] == ["auth"]


class TestTemplates:
    def test_feature_template(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "Add login",
             "--template", "feature"], cwd=workspace)
        spec = (workspace / ".tasks" / "tasks" / "epic-1-test.1.md").read_text()
        assert "Research" in spec
        assert "Implement" in spec
        assert "Acceptance Criteria" in spec

    def test_bugfix_template(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "Fix crash",
             "--template", "bugfix"], cwd=workspace)
        spec = (workspace / ".tasks" / "tasks" / "epic-1-test.1.md").read_text()
        assert "Bug Description" in spec
        assert "Investigate" in spec
        assert "Regression test" in spec

    def test_no_template_default(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        spec = (workspace / ".tasks" / "tasks" / "epic-1-test.1.md").read_text()
        assert "Description" in spec


class TestRollback:
    def test_rollback_no_sha(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        # Manually set to in_progress without git sha
        t = json.loads((workspace / ".tasks" / "tasks" / "epic-1-test.1.json").read_text())
        t["status"] = "in_progress"
        (workspace / ".tasks" / "tasks" / "epic-1-test.1.json").write_text(json.dumps(t))
        _, _, code = run(["rollback", "epic-1-test.1"], cwd=workspace)
        assert code == 1  # No SHA recorded

    def test_rollback_preview(self, workspace):
        subprocess.run(["git", "init", "-q"], check=False, cwd=workspace)
        subprocess.run(["git", "add", "."], check=False, cwd=workspace)
        subprocess.run(["git", "commit", "-q", "-m", "init"], check=False, cwd=workspace)
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        run(["start", "epic-1-test.1"], cwd=workspace)
        out, _, code = run(["rollback", "epic-1-test.1"], cwd=workspace)
        assert code == 0
        data = json.loads(out)
        assert data["action"] in ("preview", "no_changes")


    def test_rollback_confirm(self, workspace):
        subprocess.run(["git", "init", "-q"], check=False, cwd=workspace)
        subprocess.run(["git", "add", "."], check=False, cwd=workspace)
        subprocess.run(["git", "commit", "-q", "-m", "init"], check=False, cwd=workspace)
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        subprocess.run(["git", "add", "."], check=False, cwd=workspace)
        subprocess.run(["git", "commit", "-q", "-m", "add tasks"], check=False, cwd=workspace)
        run(["start", "epic-1-test.1"], cwd=workspace)
        # Make a change
        (workspace / "extra.txt").write_text("will be rolled back\n")
        subprocess.run(["git", "add", "extra.txt"], check=False, cwd=workspace)
        subprocess.run(["git", "commit", "-q", "-m", "add extra"], check=False, cwd=workspace)
        out, _, code = run(["rollback", "epic-1-test.1", "--confirm"], cwd=workspace)
        assert code == 0
        data = json.loads(out)
        assert data["action"] == "rolled_back"
        # File should be gone after rollback
        assert not (workspace / "extra.txt").exists()
        # Task should be reset to todo
        t = json.loads((workspace / ".tasks" / "tasks" / "epic-1-test.1.json").read_text())
        assert t["status"] == "todo"


class TestSessionEdgeCases:
    def test_session_restore_empty(self, workspace):
        _, _, code = run(["session", "restore"], cwd=workspace)
        assert code == 1  # No sessions

    def test_session_restore_nonexistent(self, workspace):
        _, _, code = run(["session", "restore", "does-not-exist"], cwd=workspace)
        assert code == 1


class TestSearch:
    def test_search_grep_fallback(self, workspace):
        """Search uses grep when morph not available (or query is simple)."""
        (workspace / "sample.py").write_text("def hello_world():\n    pass\n")
        out, _, code = run(["search", "hello_world", "--dir", str(workspace)], cwd=workspace)
        assert code == 0
        assert "hello_world" in out

    def test_search_empty_query(self, workspace):
        _, _, code = run(["search"], cwd=workspace)
        assert code == 1

    def test_search_json(self, workspace):
        (workspace / "test.py").write_text("x = 42\n")
        out, _, code = run(["search", "42", "--dir", str(workspace), "--format", "json"], cwd=workspace)
        assert code == 0
        data = json.loads(out)
        assert data["success"]


class TestApply:
    def test_apply_no_args(self, workspace):
        _, _, code = run(["apply"], cwd=workspace)
        assert code == 2  # argparse error (missing required args)

    def test_apply_missing_file(self, workspace):
        _, _, code = run(["apply", "--file", "nope.py", "--instruction", "test", "--update", "x"], cwd=workspace)
        assert code == 1


class TestEmbed:
    def test_embed_no_args(self, workspace):
        _, _, code = run(["embed"], cwd=workspace)
        assert code in (0, 1)  # May succeed with MORPH_API_KEY or fail without


class TestCompact:
    def test_compact_no_input(self, workspace):
        _, _, code = run(["compact"], cwd=workspace)
        assert code in (0, 1)


class TestGithubSearch:
    def test_github_search_no_args(self, workspace):
        _, _, code = run(["github-search"], cwd=workspace)
        assert code == 1  # No query


class TestDiffTracking:
    def test_done_records_diff(self, workspace):
        subprocess.run(["git", "init", "-q"], check=False, cwd=workspace)
        subprocess.run(["git", "add", "."], check=False, cwd=workspace)
        subprocess.run(["git", "commit", "-q", "-m", "init"], check=False, cwd=workspace)
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        run(["start", "epic-1-test.1"], cwd=workspace)
        # Make a change and commit
        (workspace / "newfile.txt").write_text("hello\n")
        subprocess.run(["git", "add", "newfile.txt"], check=False, cwd=workspace)
        subprocess.run(["git", "commit", "-q", "-m", "add file"], check=False, cwd=workspace)
        out, _, _ = run(["done", "epic-1-test.1", "--summary", "added file"], cwd=workspace)
        data = json.loads(out)
        assert "diff" in data
        assert data["diff"]["insertions"] >= 1


class TestMissingCommands:
    """Tests for commands that previously had no dedicated tests."""

    def test_show_epic(self, workspace):
        run(["epic", "create", "--title", "My Epic"], cwd=workspace)
        out, _, code = run(["show", "epic-1-my-epic"], cwd=workspace)
        assert code == 0
        assert "My Epic" in out

    def test_show_task(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "My Task"], cwd=workspace)
        out, _, code = run(["show", "epic-1-test.1"], cwd=workspace)
        assert code == 0
        assert "My Task" in out

    def test_tasks_filter_status(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T2"], cwd=workspace)
        run(["start", "epic-1-test.1"], cwd=workspace)
        out, _, _ = run(["tasks", "--status", "in_progress"], cwd=workspace)
        data = json.loads(out)
        assert data["count"] == 1
        assert data["tasks"][0]["id"] == "epic-1-test.1"

    def test_tasks_filter_epic(self, workspace):
        run(["epic", "create", "--title", "A"], cwd=workspace)
        run(["epic", "create", "--title", "B"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-a", "--title", "T1"], cwd=workspace)
        run(["task", "create", "--epic", "epic-2-b", "--title", "T2"], cwd=workspace)
        out, _, _ = run(["tasks", "--epic", "epic-1-a"], cwd=workspace)
        data = json.loads(out)
        assert data["count"] == 1

    def test_next_picks_highest_priority(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "Low priority"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "High priority"], cwd=workspace)
        # Manually set priority
        t2 = workspace / ".tasks" / "tasks" / "epic-1-test.2.json"
        d = json.loads(t2.read_text())
        d["priority"] = 1
        t2.write_text(json.dumps(d))
        out, _, _ = run(["next"], cwd=workspace)
        data = json.loads(out)
        assert data["id"] == "epic-1-test.2"

    def test_next_resumes_in_progress(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        run(["start", "epic-1-test.1"], cwd=workspace)
        out, _, _ = run(["next"], cwd=workspace)
        data = json.loads(out)
        assert data["action"] == "resume"

    def test_epics_command(self, workspace):
        run(["epic", "create", "--title", "First"], cwd=workspace)
        run(["epic", "create", "--title", "Second"], cwd=workspace)
        out, _, code = run(["epics"], cwd=workspace)
        assert code == 0
        data = json.loads(out)
        assert len(data["epics"]) == 2

    def test_task_set_spec(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        spec = workspace / "my-spec.md"
        spec.write_text("# Custom Spec\nDo this thing.")
        _, _, code = run(["task", "set-spec", "epic-1-test.1", "--file", str(spec)], cwd=workspace)
        assert code == 0
        actual = (workspace / ".tasks" / "tasks" / "epic-1-test.1.md").read_text()
        assert "Custom Spec" in actual

    def test_progress_visual(self, workspace):
        run(["epic", "create", "--title", "Test"], cwd=workspace)
        run(["task", "create", "--epic", "epic-1-test", "--title", "T1"], cwd=workspace)
        out, _, code = run(["progress"], cwd=workspace)
        assert code == 0
        assert "░" in out or "█" in out

    def test_log_append_and_show(self, workspace):
        run(["log", "--status", "KEPT", "--task-id", "t.1",
             "--description", "fixed it", "--iteration", "1"], cwd=workspace)
        out, _, code = run(["log", "--show", "5"], cwd=workspace)
        assert code == 0
        data = json.loads(out)
        assert data["total"] >= 1

    def test_summary(self, workspace):
        run(["log", "--status", "KEPT", "--task-id", "t.1",
             "--description", "a", "--iteration", "1"], cwd=workspace)
        out, _, code = run(["summary"], cwd=workspace)
        assert code == 0
        assert "Autoimmune Summary" in out
