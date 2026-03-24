---
description: >
  Unified RepoPrompt interface — auto-routes between rp-cli and MCP.
  File selection, context builder, code review, chat, search, codemaps, git, workspace management.
  TRIGGER: 'repoprompt', 'rp', 'builder', 'codemap', 'rp review', 'context builder'.
  NOT FOR: simple grep searches, single-file reads.
---

Activate the cc-rp skill.

## Transports

| Transport | Best for |
|-----------|----------|
| **MCP** | Interactive Claude Code sessions (preferred) |
| **CLI** (`rp-cli`) | Scripts, Ralph, chaining, piping |

## Quick Reference (CLI)

```bash
cc-flow rp check                                        # What's available
cc-flow rp builder "question" -w 1 --type question      # Deep AI analysis
cc-flow rp builder "plan feature" -w 1 --type plan      # Architecture plan
cc-flow rp builder "review changes" -w 1 --type review  # Code review
cc-flow rp chat "How does X work?" -w 1                 # Continue chat
cc-flow rp search "pattern" -w 1                        # Code search
cc-flow rp structure src/ -w 1                          # Function signatures
cc-flow rp git status -w 1                              # Git via RP
```

## Quick Reference (MCP — preferred in Claude Code)

```
mcp__RepoPrompt__file_search(pattern="auth")
mcp__RepoPrompt__context_builder(instructions="...", response_type="question")
mcp__RepoPrompt__chat_send(message="...", new_chat=true)
mcp__RepoPrompt__get_code_structure(paths=["src/"])
mcp__RepoPrompt__apply_edits(path="f.py", search="old", replace="new")
```
