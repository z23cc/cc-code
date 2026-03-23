---
name: cc-aside
description: >
  Quick side question without losing task context.
  TRIGGER: 'aside', 'quick question', 'side question', 'by the way', '顺便问一下', '快速问个问题'
  NOT FOR: new features, deep research, multi-step investigations.
  FLOWS INTO: resume original task.
---

# Quick Aside

Answer a side question without derailing the current task. Capture context, respond concisely, then nudge back on track.

## Checklist

1. **Snapshot current task** -- note what the user was working on (from recent messages, open files, last tool calls)
2. **Answer the side question** -- be concise and direct, aim for 1-5 sentences
3. **Remind and resume** -- restate the original task and suggest the next step

## The Process

**Step 1: Capture context (do NOT ask the user)**
- Identify the task in progress from conversation history
- Note the last action taken or file being edited
- Store a one-line summary mentally (do not output a lengthy recap)

**Step 2: Answer the aside**
- Answer directly -- no preamble, no over-explaining
- If the question needs code, show a minimal snippet
- If the question is actually a big topic, say so: "This deserves its own session -- want me to bookmark it?"
- If you genuinely don't know, say so immediately

**Step 3: Resume original task**
- End with a brief reminder:
  > "Back to [original task] -- we were about to [next step]."
- If the aside changes the plan, flag it explicitly before resuming

## Key Principles

- **Speed over depth** -- the user wants a quick answer, not a lecture
- **Zero context loss** -- always bring them back to where they were
- **Know when to escalate** -- if the "aside" is actually complex, recommend a dedicated skill

## E2E Example

```
User (mid-refactoring auth module): "By the way, what's the difference between
HMAC-SHA256 and RS256 for JWTs?"

Step 1: [Internal note: user is refactoring auth module, last edited src/auth/tokens.py]

Step 2: "HMAC-SHA256 (HS256) uses a shared secret -- both sides need the same key.
RS256 uses an RSA key pair -- sign with private, verify with public. Use RS256
when the verifier shouldn't be able to create tokens (e.g., separate auth server)."

Step 3: "Back to the auth refactor -- we were about to extract the token
validation into its own function in src/auth/tokens.py."
```

## Related Skills

- **cc-research** -- use when the "aside" turns out to need deep investigation
- **cc-brainstorming** -- use when the aside sparks a new feature idea
