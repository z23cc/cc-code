---
description: >
  File-based task management with epic/task lifecycle, dependency tracking,
  and progress visualization. Uses cc-flow CLI and .tasks/ directory.
  TRIGGER: 'show tasks', 'task status', 'create task', 'list epics', 'next task', 'progress'.
  NOT FOR: background job queues — use cc-task-queues.
  FLOWS INTO: cc-work.
---

Activate the cc-task-tracking skill.

## Quick Reference

```bash
cc-flow init                                             # Initialize .tasks/
cc-flow epic create --title "Feature name"               # Create epic
cc-flow task create --epic epic-N --title "Task" --deps "epic-N.1"  # Create task

cc-flow list                                             # All epics + tasks
cc-flow ready --epic epic-N                              # What's ready to work on
cc-flow next --epic epic-N                               # Smart next task
cc-flow show epic-N.M                                    # Task detail + spec

cc-flow start epic-N.M                                   # Begin work
cc-flow done epic-N.M --summary "What was done"          # Complete task
cc-flow block epic-N.M --reason "Why"                    # Block task
cc-flow progress                                         # Progress bars
cc-flow epic close epic-N                                # Archive completed epic
cc-flow validate                                         # Check deps, cycles
```
