## cc-code v5.26 — AI-Routed, Multi-Engine, Team-Based

**`cc-flow go "describe your goal"`** — AI selects best workflow automatically.

### Quick Reference

| Goal | Command |
|------|---------|
| **Anything** | `cc-flow go "your goal"` (AI routed) |
| Complex task | `cc-flow autopilot "goal"` (3-engine guided) |
| Code review | `cc-flow review` (auto 3-engine debate) |
| Project health | `/cc-prime` (12 scouts parallel) |

### How It Works

```
cc-flow go "goal"
  → AI Router (gemini/claude) analyzes intent
  → Simple: light chain (2-3 steps)
  → Medium: standard chain + team dispatch + worktree
  → Complex: autopilot (3-engine plan → execute → checkpoint → review)
```

### Key Features

- **AI Router**: LLM selects chain (no keyword matching), cached 24h
- **Team Dispatch**: /cc-review → 3 reviewers parallel, /cc-brainstorm → 3 scouts parallel
- **Worktree**: code-changing chains auto-create isolated branch
- **3-Engine Debate**: Claude × Codex × Gemini adversarial review
- **Bridge**: `deep-search` (Morph→RP), `smart-chat` (SM→RP), `recall-review` (SM)

### Tools

`cc-flow verify` · `cc-flow review` · `cc-flow dashboard` · `cc-flow doctor`
