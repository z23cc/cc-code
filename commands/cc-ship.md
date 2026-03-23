---
description: >
  Ship current branch: verify, review, version bump, changelog, push, create PR.
  TRIGGER: 'ship', 'release', 'deploy', 'create PR', 'push', '发布', '上线', '推送'.
---

Activate the cc-ship skill. Options:

| Flag | Behavior |
|------|----------|
| (none) | Auto-detect base, auto bump level |
| `--bump=minor` | Force minor version bump |
| `--bump=major` | Force major version bump |
| `--no-review` | Skip review phase |
| `--dry-run` | Show what would happen without executing |

## Steps

1. Detect base branch and merge into current (stop on conflict)
2. Run `cc-flow verify`; auto-fix if possible
3. Review diff vs base using cc-review skill
4. Bump version in pyproject.toml (if exists)
5. Update CHANGELOG.md with grouped commit summaries
6. Commit `chore: release vX.Y.Z`, push, create PR
7. Print PR URL
