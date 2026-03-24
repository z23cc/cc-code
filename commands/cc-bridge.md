---
description: >
  Morph x RepoPrompt x Supermemory collaboration bridge — 6 feedback loops for deep search,
  memory-enhanced chat, review knowledge, and cross-project pattern reuse.
  TRIGGER: 'bridge', 'deep search', 'smart chat', 'morph rp', 'system status',
  'bridge status', 'three systems'.
---

Activate the cc-bridge skill.

## Quick Commands

```bash
cc-flow bridge-status                          # check all 3 systems
cc-flow deep-search "query" --type plan        # Morph find -> RP analyze
cc-flow smart-chat "question" --mode chat      # memory-enhanced RP chat
cc-flow embed-structure src/                   # code structure -> vectors
cc-flow recall-review "topic"                  # past review findings
```

## 6 Loops

1. **deep-search** — Morph search -> RP select -> RP builder
2. **review-to-memory** — RP review -> SM save (auto on `cc-flow done`)
3. **smart-chat** — SM recall -> RP chat
4. **scan-to-memory** — OODA findings -> SM save (auto)
5. **embed-structure** — RP structure -> Morph embed
6. **recall-review** — SM recall -> RP review context

Systems degrade gracefully — if one is unavailable, the bridge skips that step.
