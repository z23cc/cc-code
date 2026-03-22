# Changelog

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
