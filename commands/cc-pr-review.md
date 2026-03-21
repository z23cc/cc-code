---
agent: "code-reviewer"
description: "Review a GitHub PR with multi-agent dispatch. TRIGGER: 'review PR', 'review pull request', 'check this PR', '审查PR', 'PR #123'. Pass PR number or URL as argument."
---

Review a GitHub Pull Request by dispatching specialized agents based on diff content.

## Process

1. Fetch PR info: `gh pr view <number> --json title,body,files,additions,deletions`
2. Get full diff: `gh pr diff <number>`
3. Classify changed files and dispatch agents:

| Files Changed | Agent | Focus |
|---------------|-------|-------|
| `*.py` | **python-reviewer** | PEP 8, type hints, Pythonic patterns |
| Auth/API/input handling | **security-reviewer** | OWASP, injection, secrets |
| All files | **code-reviewer** | Quality, dead code, complexity |

4. For large PRs (>500 lines):
   - Split review by file groups
   - Use parallel agents (one per file group)

5. Consolidate findings into a single comment:
   ```bash
   gh pr review <number> --comment --body "## Code Review\n\n..."
   ```

6. Verdict: APPROVE / REQUEST_CHANGES / COMMENT

## Size Heuristics

| PR Size | Lines | Strategy |
|---------|-------|----------|
| Small | < 100 | Single code-reviewer pass |
| Medium | 100-500 | python-reviewer + security-reviewer |
| Large | > 500 | Parallel agents per file group |
