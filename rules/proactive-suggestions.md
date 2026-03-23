---
description: "Proactive skill suggestions — suggest the right skill at the right moment"
alwaysApply: true
---

# Proactive Suggestions

Suggest these skills at contextually appropriate moments:

| When you notice... | Suggest |
|---------------------|---------|
| User describes a new feature idea | `/cc-brainstorm` → then `/cc-plan` |
| User has a plan but hasn't validated it | `/cc-grill-me` (adversarial review) |
| User is debugging and stuck | `/cc-debug` with PUA escalation |
| User says "is this ready?" or "can we ship?" | `/cc-audit` or `/cc-epic-review` |
| It's Friday or user mentions "weekly" | `/cc-retro` (weekly retrospective) |
| User is about to implement without a plan | `/cc-plan` first |
| User asks a quick side question mid-task | `/cc-aside` (preserves context) |
| User has multiple independent tasks | `/cc-parallel-agents` |
| User is about to push/deploy | `/cc-review` first |
| User mentions "worktree" or parallel work | `/cc-worktree` |
| User wants to understand unfamiliar code | `/cc-research` or `cc-flow deep-search` |
| User mentions "production" or "careful" | `cc-flow careful --enable` |

## Rules
- Suggest ONCE per session per skill (don't nag)
- Frame as a question: "Would you like to run /cc-X first?"
- If user says "stop suggesting", respect immediately
- Suggest maximally 2 skills at once
