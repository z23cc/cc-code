# Changelog

## [5.1.0] - 2026-03-23
### Added
- Skills marketplace: `cc-flow skills find/add/list` (skills.sh integration)
- "Did you mean?" typo correction in REPL
- REPL tab completion for all 90+ commands
- Interactive REPL mode (`cc-flow` with no args)
- Terminal skin: colored output (✓ ✗ ⚠ ●), tables, progress bars
- Example plugins: notify (desktop notifications) + timer (pomodoro)
### Fixed
- Race-safe task ID allocation (`O_CREAT|O_EXCL`)
- Epic/task ID shorthand (`epic-1.3` → full ID)
- Node.js verify: auto-detect package.json scripts
- Node.js verify: skip missing tools, detect missing node_modules
- Slugify strips `#()!@` from epic IDs
- Chinese route keywords expanded (新增/添加/修复/崩溃 etc.)
- Epic validation on task create (prevents orphan tasks)
- Q-learning rate 0.1→0.25 for faster adaptation

## [5.0.0] - 2026-03-22
### Added
- Interactive REPL with prompt_toolkit
- Terminal skin module (skin.py)
- Dashboard uses skin for colored output

## [4.2.0] - 2026-03-22
### Fixed
- CRITICAL: Atomic file writes (temp + os.replace) prevent data corruption
- CRITICAL: Cross-platform file locking (fcntl on Unix, msvcrt on Windows)
- Missing docstrings on 6 public commands
- Documentation drift (__init__.py, CLAUDE.md now accurate)
- auto.py print/JSON mixing — structured output only

## [4.1.0] - 2026-03-22
### Added
- Deep Morph API integration into OODA loop
- Embedding-based semantic duplication detection in scanner
- Morph Search for pattern discovery + task context
- Morph Rerank for priority refinement in auto deep

## [4.0.0] - 2026-03-22
### Added
- Autoimmune v2: OODA loop architecture (observe/orient/decide/act/learn)
- Smart scanner module: architecture, test coverage, docstrings, duplication, dependencies
- Scan trend tracking (improving/stable/declining)
- Q-learning adaptive priority based on success history

## [3.20.0] - 2026-03-22
### Added
- Q-learning router (qrouter.py) — learns optimal commands from history
- Performance tracking (perf.py) — auto-times every command
- Config profiles — fast/strict/minimal presets

## [3.19.0] - 2026-03-22
### Added
- Plugin system — discover, load, manage user plugins (.tasks/plugins/)
- Plugin lifecycle hooks (on_task_start/done/block)
- Plugin CLI: list/enable/disable/create

## [3.18.1] - 2026-03-22
### Added
- 23 integration tests for v3.10-3.18 features
- CHANGELOG.md with full version history

## [3.18.0] - 2026-03-22
### Added
- Lazy command loading — only imports the module needed for invoked command
- Categorized `--help` output — 10 command groups
- Workflow engine — `workflow list/show/run/create` with 3 built-in workflows

## [3.17.0] - 2026-03-22
### Added
- `time` — duration analysis per task, by size and epic
- `critical-path` — longest dependency chain analysis
- `template list/show/create` — task template management

## [3.16.0] - 2026-03-22
### Added
- `bulk` — batch status changes (done/todo/blocked)
- `burndown` — epic burndown timeline data
- `report` — comprehensive markdown project report

## [3.15.0] - 2026-03-22
### Added
- `index` — pre-build embedding cache for all tasks
- `dedupe` — detect near-duplicate tasks via embeddings
- `suggest` — recommend approach from similar completed tasks

## [3.14.0] - 2026-03-22
### Added
- `find --semantic` — embedding-based task search
- `similar` — find tasks similar to a given task
- `embeddings.py` module with SHA-256 cached Morph embeddings
- 3-tier learning search: rerank -> embedding -> keyword

## [3.13.0] - 2026-03-22
### Added
- `changelog` — auto-generate from completed tasks
- `diff` — git changes since task started
- `priority` — cross-epic priority-sorted task queue

## [3.12.0] - 2026-03-22
### Added
- `standup` — daily standup report
- `dep show` — full dependency chain analysis
- `task comment` — timestamped task notes

## [3.11.0] - 2026-03-22
### Added
- `find` — full-text search across tasks and epics
- `reopen` — reopen done/blocked tasks
- `task update` — modify task attributes post-creation
### Changed
- `stats` now outputs JSON (was markdown)

## [3.10.0] - 2026-03-22
### Added
- `verify` — one-click lint+test with language auto-detection
- `clean` — garbage collect old sessions/archives
- `export` — export epic as markdown report

## [3.9.2] - 2026-03-22
### Fixed
- Replace 6 blind Exception catches with specific types
- Add docstrings to 9 public functions
- 13 new unit tests, enable BLE001 rule

## [3.9.1] - 2026-03-22
### Fixed
- Replace 15 inline error prints with `error()` helper
- 7 new unit tests (graph, config, session, consolidation)
- Enable PLR0915 + TRY300 rules

## [3.9.0] - 2026-03-22
### Changed
- Package cc-flow as installable CLI (`pip install -e .` -> `cc-flow`)
- All C901 complexity violations resolved (12 -> 0)
- 780 ruff violations -> 0, 15 rules enforced
- 114 -> 132 tests
