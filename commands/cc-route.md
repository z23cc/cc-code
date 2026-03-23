---
description: "Smart routing: describe your task, get the right command + team. TRIGGER: 'what should I do', 'route this', 'how to approach', '怎么做', '用什么命令'. Uses past learnings."
---

Activate the cc-feedback-loop skill. Steps:

1. Run `cc-flow route "<user's task description>"` to get suggestion
2. If past_learning exists in response, mention it: "Based on past experience: {lesson}"
3. Suggest the command: "I recommend `{command}` — {reason}"
4. If team is suggested: "This is a complex task, consider `/team` ({team} template)"
5. Ask user to confirm, then execute the suggested command

After task completion, prompt: "Want me to record this as a learning? (`cc-flow learn`)"

## Proactive Suggestion Integration

When routing, also consult the proactive suggestion patterns from `rules/proactive-suggestions.md`.
If the user's task description matches a proactive trigger (e.g., "new feature" → `/cc-brainstorm`,
"debug" → `/cc-debug`, "ship" → `/cc-audit`), include that suggestion alongside the route result.
This ensures routing and proactive suggestions stay aligned.
