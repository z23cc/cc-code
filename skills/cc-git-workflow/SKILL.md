---
name: cc-git-workflow
description: >
  Git branching, conventional commits, PR workflow, and collaboration patterns.
  TRIGGER: 'git', 'branch', 'commit', 'PR', 'merge', 'rebase', 'Git工作流', '分支策略'
  NOT FOR: code review content, deployment, CI/CD pipelines
  FLOWS INTO: cc-commit, cc-ship.
---

# Git Workflow

## Conventional Commits

All commits follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | When |
|------|------|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test` | Adding or updating tests |
| `docs` | Documentation only |
| `style` | Formatting, missing semicolons (no code change) |
| `perf` | Performance improvement |
| `ci` | CI/CD configuration |
| `chore` | Maintenance tasks |
| `build` | Build system or dependency changes |

### Examples

```bash
feat(auth): add JWT token refresh endpoint
fix(api): handle empty request body in user creation
refactor(models): extract validation logic to separate module
test(auth): add integration tests for login flow
perf(queries): add database index for user email lookup
```

### Breaking Changes

```bash
feat(api)!: change authentication from session to JWT

BREAKING CHANGE: All API endpoints now require Bearer token instead of session cookie.
Migration guide: docs/migration-v2.md
```

## Branching Strategy

```
main ─────────────────────────────────────────────
  │                                    ▲
  └── feature/add-auth ────────────────┘ (squash merge)
  │                         ▲
  └── fix/empty-body-crash ─┘ (squash merge)
```

### Branch Naming

```
feature/<short-description>    # New features
fix/<short-description>        # Bug fixes
refactor/<short-description>   # Refactoring
test/<short-description>       # Test improvements
```

## Pre-Commit Checklist

Before every commit:
- [ ] `ruff check .` — no lint errors
- [ ] `mypy .` — no type errors
- [ ] `pytest` — all tests pass
- [ ] `git diff --staged` — review what you're committing
- [ ] No secrets, no `.env` files, no debug prints

## PR Workflow

### Creating a PR

```bash
# Push and create PR
git push -u origin feature/my-feature
gh pr create --title "feat: add feature" --body "## Summary\n- What changed\n\n## Test plan\n- How to verify"
```

### PR Description Template

```markdown
## Summary
- [What changed and why]

## Test Plan
- [ ] Unit tests added/updated
- [ ] Manual testing steps
- [ ] Edge cases verified

## Breaking Changes
- None / [Description]
```

## Useful Git Commands

```bash
git log --oneline -10                      # Recent history
git diff --stat HEAD~3                     # What changed in last 3 commits
git stash && git stash pop                 # Temp save/restore
git rebase -i HEAD~3                       # Clean up last 3 commits
git cherry-pick <sha>                      # Pick specific commit
git bisect start && git bisect bad         # Find regression
```

## Pre-PR Checklist

Before creating a PR, verify:

- [ ] `git diff main..HEAD --stat` — reasonable diff size (< 500 lines)
- [ ] All commits follow conventional format
- [ ] No `WIP`, `fixup`, `tmp` commits (squash or rebase)
- [ ] Tests pass: `pytest` / `npm test` / `go test`
- [ ] Lint clean: `ruff check .` / `eslint`
- [ ] No secrets in diff: `git diff main..HEAD | grep -i "password\|secret\|key=\|token="`
- [ ] PR description has Summary + Test Plan
- [ ] Related issue/task referenced

## Commit Size Guidelines

| Commits in PR | Assessment | Action |
|---------------|-----------|--------|
| 1 | Good for small fixes | Ship it |
| 2-5 | Good for features | Each commit should be atomic |
| 6-10 | Consider splitting PR | Group by concern |
| 10+ | **Too big** | Split into multiple PRs |

**Each commit should:** compile, pass tests, and be revertable independently.

## Rebase vs Merge Decision

| Situation | Use | Why |
|-----------|-----|-----|
| Feature branch behind main | `git rebase main` | Clean linear history |
| Shared branch (2+ people) | `git merge main` | Don't rewrite shared history |
| PR with messy commits | `git rebase -i` to squash | Clean before merge |
| Conflict-heavy rebase | `git merge` instead | Less painful |


## On Completion

When done:
```bash
cc-flow skill ctx save cc-git-workflow --data '{"completed_tasks": [...], "epic_status": "done"}'
cc-flow skill next
```

## Related Skills

- **cc-verification** — run lint+test before every commit
- **cc-autoimmune** — commit format follows conventional commits
- **cc-task-tracking** — commit task state changes alongside code
- **cc-docs** — update docs in same PR as code changes
