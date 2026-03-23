---
name: cc-ship
description: >
  Ship current branch: merge base, verify, review, version bump, changelog,
  commit, push, and create PR. One command from working code to pull request.
  TRIGGER: 'ship', 'release', 'deploy', 'create PR', 'push', '发布', '上线', '推送'.
  NOT FOR: drafting changes — finish work first with cc-work.
  DEPENDS ON: cc-review (runs review before shipping).
  FLOWS INTO: (deployment).
---

# Ship — Branch to PR Pipeline

`/cc-ship` takes a working branch and produces a reviewed, versioned pull request.

```
/cc-ship                  # Ship current branch (auto-detect base)
/cc-ship --bump=minor     # Force minor version bump
/cc-ship --no-review      # Skip review step
```

## Pipeline

```bash
CCFLOW="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"
```

### Phase 1: Detect Base & Merge

```bash
BASE=$(git remote show origin | grep 'HEAD branch' | awk '{print $NF}')
CURRENT=$(git branch --show-current)
[[ "$CURRENT" == "$BASE" ]] && error "Already on $BASE. Create a feature branch first."
git fetch origin "$BASE" && git merge "origin/$BASE" --no-edit
```

### Phase 2: Verify

```bash
$CCFLOW verify   # If fails → $CCFLOW verify --fix → if still fails → stop
```

### Phase 3: Review Diff

```bash
git diff "$BASE"...HEAD --stat
# Run cc-review skill; SHIP → continue, NEEDS_WORK → fix, MAJOR_RETHINK → stop
```

### Phase 4: Version Bump (if pyproject.toml exists)

Suggest bump based on changes: breaking → major, features → minor, fixes → patch.
User can override with `--bump=patch|minor|major`. Update version in pyproject.toml.

### Phase 5: Update CHANGELOG.md

Prepend `## vX.Y.Z (YYYY-MM-DD)` with changes grouped by conventional commit type.

### Phase 6: Commit, Push, PR

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "chore: release v$NEW_VERSION"
git push -u origin "$CURRENT"
gh pr create --title "Release v$NEW_VERSION" --body "## Changes..."
```

Print the PR URL when done.

## Related Skills

- **cc-review** — code review (runs in Phase 3)
- **cc-git-workflow** — conventional commits, branch naming
- **cc-work** — task execution (run before shipping)
- **cc-epic-review** — verify epic completion before shipping
