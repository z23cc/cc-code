---
description: >
  Multi-backend code review routing. Supports agent, RepoPrompt, Codex CLI, and context export.
  Configurable per review type (plan/impl/completion).
  TRIGGER: 'review backend', 'use rp for review', 'codex review', 'review config', 'switch reviewer'.
  NOT FOR: doing a review — use cc-review. This configures HOW reviews run.
---

Activate the cc-review-backend skill.

## Backends

| Backend | ID | Best for |
|---------|-----|----------|
| **Agent** | `agent` | Default, fast, no setup |
| **RepoPrompt** | `rp` | Deep review, visual, full file context |
| **Codex CLI** | `codex` | Multi-model, unattended |
| **Export** | `export` | Manual review via external LLM |
| **None** | `none` | Skip review |

## Configuration

```bash
cc-flow config set review.backend agent        # Set default
cc-flow config set review.plan rp              # Plan review via RP
cc-flow config set review.impl agent           # Impl review via agents
cc-flow config set review.completion codex     # Epic review via Codex
```

Override priority: CLI arg > env var > per-type config > default config > `agent`.
