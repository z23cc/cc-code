"""cc-flow CLI entry point — lazy-loaded command dispatch.

Commands are mapped as 'module:function' strings and imported on demand.
This saves ~150ms startup time by avoiding importing all 18 modules upfront.
"""

import sys
from importlib import import_module

from cc_flow.cli import build_parser

# Lazy command registry: command name → "module:function"
# Only the module needed for the invoked command gets imported.
_COMMANDS = {
    # epic_task
    "init": "epic_task:cmd_init",
    # views
    "list": "views:cmd_list", "epics": "views:cmd_epics", "tasks": "views:cmd_tasks",
    "show": "views:cmd_show", "ready": "views:cmd_ready", "next": "views:cmd_next",
    "progress": "views:cmd_progress", "status": "views:cmd_status",
    "dashboard": "views:cmd_dashboard", "export": "views:cmd_export",
    "find": "views:cmd_find", "similar": "views:cmd_similar",
    "priority": "views:cmd_priority", "index": "views:cmd_index",
    "dedupe": "views:cmd_dedupe", "suggest": "views:cmd_suggest",
    # work
    "start": "work:cmd_start", "done": "work:cmd_done", "block": "work:cmd_block",
    "rollback": "work:cmd_rollback", "reopen": "work:cmd_reopen",
    "diff": "work:cmd_diff", "bulk": "work:cmd_bulk",
    # quality
    "validate": "quality:cmd_validate", "scan": "quality:cmd_scan",
    "verify": "quality:cmd_verify",
    # config
    "version": "config:cmd_version", "history": "config:cmd_history",
    "config": "config:cmd_config", "clean": "config:cmd_clean",
    # doctor
    "doctor": "doctor:cmd_doctor",
    # graph
    "graph": "graph:cmd_graph", "critical-path": "graph:cmd_critical_path",
    # log_cmds
    "log": "log_cmds:cmd_log", "summary": "log_cmds:cmd_summary",
    "archive": "log_cmds:cmd_archive", "stats": "log_cmds:cmd_stats",
    "standup": "log_cmds:cmd_standup", "changelog": "log_cmds:cmd_changelog",
    "burndown": "log_cmds:cmd_burndown", "report": "log_cmds:cmd_report",
    "time": "log_cmds:cmd_time",
    # route_learn
    "route": "route_learn:cmd_route", "learn": "learning:cmd_learn",
    "learnings": "learning:cmd_learnings", "consolidate": "learning:cmd_consolidate",
    # morph_cmds
    "apply": "morph_cmds:cmd_apply", "search": "morph_cmds:cmd_search",
    "embed": "morph_cmds:cmd_embed", "compact": "morph_cmds:cmd_compact",
    "github-search": "morph_cmds:cmd_github_search",
    # perf + profile + insights
    "perf": "perf:cmd_perf", "profile": "config:cmd_profile",
    "forecast": "insights:cmd_forecast", "evolve": "insights:cmd_evolve",
    "health": "insights:cmd_health",
    # review setup
    "review-setup": "review_setup:cmd_review_setup",
    # review (unified — auto-selects best mode)
    "review": "unified_review:cmd_unified_review",
    # legacy aliases (still work directly)
    "multi-review": "multi_review:cmd_multi_review",
    "adversarial-review": "adversarial_review:cmd_adversarial_review",
    "multi-plan": "multi_plan:cmd_multi_plan",
    "autopilot": "autopilot:cmd_autopilot",
    "pua": "pua_engine:cmd_pua",
    # skill validation
    "validate-skills": "skill_validate:cmd_validate_skills",
    # bridge (Morph × RP × Supermemory)
    "deep-search": "bridge:cmd_deep_search",
    "smart-chat": "bridge:cmd_smart_chat",
    "embed-structure": "bridge:cmd_embed_structure",
    "recall-review": "bridge:cmd_recall_review",
    "bridge-status": "bridge:cmd_bridge_status",
    # worktree state
    "state-path": "worktree_state:cmd_state_path",
    "migrate-state": "worktree_state:cmd_migrate_state",
    # ralph (legacy — use cc-flow go instead)
    "ralph": "ralph_cmd:cmd_ralph",
    # safety modes
    "careful": "modes:cmd_careful",
    "freeze": "modes:cmd_freeze",
    "guard": "modes:cmd_guard",
    # context budget
    "context-budget": "context_budget:cmd_context_budget",
    # go (unified entry point)
    "go": "go:cmd_go",
    # help (grouped command overview)
    "help": "repl:cmd_help",
}

# Subcommands: parent → (attr, {subcmd: "module:function"})
_SUBCMD_MAP = {
    "epic": ("epic_cmd", {
        "create": "epic_task:cmd_epic_create", "close": "epic_task:cmd_epic_close",
        "import": "epic_task:cmd_epic_import", "reset": "epic_task:cmd_epic_reset",
    }),
    "task": ("task_cmd", {
        "create": "epic_task:cmd_task_create", "reset": "epic_task:cmd_task_reset",
        "set-spec": "epic_task:cmd_task_set_spec", "update": "epic_task:cmd_task_update",
        "comment": "epic_task:cmd_task_comment",
    }),
    "dep": ("dep_cmd", {
        "add": "epic_task:cmd_dep_add", "show": "epic_task:cmd_dep_show",
    }),
    "template": ("template_cmd", {
        "list": "templates:cmd_template_list", "show": "templates:cmd_template_show",
        "create": "templates:cmd_template_create",
    }),
    "workflow": ("workflow_cmd", {
        "list": "workflow:cmd_workflow_list", "show": "workflow:cmd_workflow_show",
        "run": "workflow:cmd_workflow_run", "create": "workflow:cmd_workflow_create",
        "chain": "workflow:cmd_workflow_chain",
    }),
    "pipeline": ("pipeline_cmd", {
        "list": "pipeline:cmd_pipeline_list", "run": "pipeline:cmd_pipeline_run",
        "create": "pipeline:cmd_pipeline_create",
    }),
    "memory": ("memory_cmd", {
        "save": "memory:cmd_memory_save", "search": "memory:cmd_memory_search",
        "sync": "memory:cmd_memory_sync", "forget": "memory:cmd_memory_forget",
        "recall": "memory:cmd_memory_recall",
    }),
    "chain": ("chain_cmd", {
        "list": "skill_chains:cmd_chain_list", "show": "skill_chains:cmd_chain_show",
        "suggest": "skill_chains:cmd_chain_suggest", "run": "skill_chains:cmd_chain_run",
        "advance": "skill_chains:cmd_chain_advance",
        "stats": "skill_flow:cmd_chain_stats",
    }),
    "wisdom": ("wisdom_cmd", {
        "show": "wisdom:cmd_wisdom_show",
        "search": "wisdom:cmd_wisdom_search",
        "add": "wisdom:cmd_wisdom_add",
        "clear": "wisdom:cmd_wisdom_clear",
    }),
    "explore": ("explore_cmd", {
        "cache": "wisdom:cmd_explore_cache",
        "lookup": "wisdom:cmd_explore_lookup",
        "clear": "wisdom:cmd_explore_clear",
    }),
    "wf": ("wf_cmd", {
        "run": "wf_executor:cmd_wf_run",
        "list": "wf_executor:cmd_wf_list",
        "show": "wf_executor:cmd_wf_show",
        "export": "wf_executor:cmd_wf_export",
    }),
    "skill": ("skill_cmd", {
        "next": "skill_flow:cmd_next",
        "graph": "skill_flow:cmd_graph_show",
        "graph-build": "skill_flow:cmd_graph_build",
        "ctx": "skill_flow:cmd_ctx",
        "check-deps": "skill_flow:cmd_check_deps",
    }),
    "worktree": ("wt_cmd", {
        "create": "worktree_cmd:_cmd_create", "list": "worktree_cmd:_cmd_list",
        "switch": "worktree_cmd:_cmd_switch", "remove": "worktree_cmd:_cmd_remove",
        "cleanup": "worktree_cmd:_cmd_cleanup", "status": "worktree_cmd:_cmd_status",
        "info": "worktree_cmd:_cmd_info",
    }),
    "plugin": ("plugin_cmd", {
        "list": "plugins:cmd_plugin_list", "enable": "plugins:cmd_plugin_enable",
        "disable": "plugins:cmd_plugin_disable", "create": "plugins:cmd_plugin_create",
    }),
    "skills": ("skills_cmd", {
        "find": "skill_store:cmd_skills_find", "add": "skill_store:cmd_skills_add",
        "list": "skill_store:cmd_skills_list",
    }),
    "gh": ("gh_cmd", {
        "import": "gh_sync:cmd_gh_import", "export": "gh_sync:cmd_gh_export",
        "status": "gh_sync:cmd_gh_status",
    }),
    "context": ("context_cmd", {
        "save": "context:cmd_context_save", "show": "context:cmd_context_show",
        "brief": "context:cmd_context_brief",
    }),
    "alias": ("alias_cmd", {
        "list": "aliases:cmd_alias_list", "set": "aliases:cmd_alias_set",
        "remove": "aliases:cmd_alias_remove",
    }),
    "checkpoint": ("checkpoint_cmd", {
        "create": "checkpoint:cmd_checkpoint_create",
        "verify": "checkpoint:cmd_checkpoint_verify",
        "compare": "checkpoint:cmd_checkpoint_compare",
        "list": "checkpoint:cmd_checkpoint_list",
    }),
    "eval": ("eval_cmd", {
        "run": "eval_harness:cmd_eval_run", "detail": "eval_harness:cmd_eval_detail",
        "history": "eval_harness:cmd_eval_history",
        "cross": "cross_project_eval:cmd_cross_test",
    }),
}

# Special dispatchers (these modules handle their own subcommand parsing)
_SPECIAL = {
    "auto": "auto:cmd_auto",
    "session": "session:cmd_session",
    "rp": "rp_commands:cmd_rp",
}


def _resolve(ref):
    """Import a 'module:function' reference and return the callable."""
    module_name, func_name = ref.split(":")
    mod = import_module(f"cc_flow.{module_name}")
    return getattr(mod, func_name)


def _run_with_perf(cmd, handler, args):
    """Run a command handler with optional performance tracking."""
    try:
        from cc_flow.perf import PerfTimer
        with PerfTimer(cmd):
            handler(args)
    except ImportError:
        handler(args)


def main():
    """Parse args and dispatch to the appropriate command handler."""
    # No arguments → enter interactive REPL
    if len(sys.argv) <= 1:
        from cc_flow.repl import run_repl
        run_repl()
        return

    parser = build_parser()
    args = parser.parse_args()

    cmd = args.command

    # Special dispatchers (handle own subcommands)
    if cmd in _SPECIAL:
        _run_with_perf(cmd, _resolve(_SPECIAL[cmd]), args)
    # Subcommand groups (epic/task/dep/template)
    elif cmd in _SUBCMD_MAP:
        attr, handlers = _SUBCMD_MAP[cmd]
        sub = getattr(args, attr, None)
        if sub in handlers:
            _run_with_perf(f"{cmd}.{sub}", _resolve(handlers[sub]), args)
        else:
            parser.print_help()
            sys.exit(1)
    # Direct commands
    elif cmd in _COMMANDS:
        _run_with_perf(cmd, _resolve(_COMMANDS[cmd]), args)
    else:
        # Try plugin commands before giving up
        try:
            from cc_flow.plugins import dispatch_plugin_command
            if dispatch_plugin_command(cmd, args):
                return
        except ImportError:
            pass
        parser.print_help()
        sys.exit(1)
