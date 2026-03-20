---
name: git-workflow
description: "Git branching, conventional commits, PR workflow, and collaboration patterns for Python projects."
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

## Related Skills

- **verification** — run lint+test before every commit
- **autoimmune** — commit format follows conventional commits
- **task-tracking** — commit task state changes alongside code
