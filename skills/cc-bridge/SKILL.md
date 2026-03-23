---
name: cc-bridge
description: >
  Morph × RepoPrompt × Supermemory collaboration bridge — 6 feedback loops for deep search,
  memory-enhanced chat, review knowledge, and cross-project pattern reuse.
  TRIGGER: 'bridge', 'deep search', 'smart chat', 'morph rp', 'system status',
  '桥接', '深度搜索', '智能对话', '三系统', '联动'.
  NOT FOR: individual tool usage — use cc-rp, cc-search-strategy, or memory commands directly.
---

# Bridge — Morph × RepoPrompt × Supermemory

Three systems, six feedback loops. Each loop chains two systems so knowledge flows automatically.

## Architecture

```
          ┌──────────┐
     ┌───>│  Morph   │───┐
     │    │ (search, │   │  1. deep-search: Morph search → RP select → RP builder
     │    │  embed)  │<──┤  5. embed-structure: RP structure → Morph embed
     │    └──────────┘   │
     │                   v
┌────┴─────┐      ┌──────────┐
│Supermem- │<─────│  Repo-   │  2. review-to-memory: RP review → SM save
│  ory     │─────>│  Prompt  │  3. smart-chat: SM recall → RP chat
│(memory)  │      │ (reason) │  4. scan-to-memory: OODA findings → SM save
└──────────┘      └──────────┘  6. recall-review: SM recall → RP review context
```

## CLI Commands

```bash
# Check all three systems
cc-flow bridge-status

# Loop 1 — Deep search (Morph speed + RP depth)
cc-flow deep-search "how does auth work"
cc-flow deep-search "payment flow" --type plan

# Loop 3 — Memory-enhanced chat (recall past experience → RP)
cc-flow smart-chat "design a retry mechanism" --mode chat
cc-flow smart-chat "refactor auth" --mode plan --new

# Loop 5 — Embed code structure for similarity search
cc-flow embed-structure src/auth/ src/api/

# Loop 6 — Recall past review findings for a task
cc-flow recall-review "implement rate limiting"
```

## Auto-Triggered Loops

These loops fire automatically — no CLI needed:

| Loop | Trigger | What happens |
|------|---------|--------------|
| **review-to-memory** | `cc-flow done` with review verdict | Saves NEEDS_WORK/MAJOR_RETHINK findings to SM. Routine SHIPs are skipped to avoid clutter. |
| **scan-to-memory** | OODA deep scan completes | Saves P1/P2 findings (max 10 per scan) to SM. Lower severity skipped. |

Saved memories are tagged by category (`review`, `scan`, severity) and recalled automatically
when similar code is reviewed or scanned in the future.

## Prerequisites

| System | Required env var | Install |
|--------|-----------------|---------|
| Morph | `MORPH_API_KEY` | `pip install morph-python` |
| RepoPrompt | RepoPrompt app running | rp-cli or MCP transport |
| Supermemory | `SUPERMEMORY_API_KEY` | `pip install supermemory` |

Loops degrade gracefully — if a system is unavailable, the bridge skips that step and
continues with what is reachable. `deep-search` falls back to grep if Morph is down.

## bridge-status Output

```bash
cc-flow bridge-status
```

Returns JSON with three sections:

- **`morph`** / **`repoprompt`** / **`supermemory`** — each has `available: bool`. RP also reports `transport` (cli/mcp) and `version`.
- **`bridge_loops`** — all 6 loops with name, chain direction, and triggering command.
- **`all_systems_connected`** — `true` only when all three systems are reachable. Partial connectivity still works for loops that only need two systems.

## Related Skills

- **cc-rp** — RepoPrompt operations (select, builder, chat, git)
- **cc-search-strategy** — when to use which search tool
- **cc-review-backend** — review routing (agent/rp/codex/export)
