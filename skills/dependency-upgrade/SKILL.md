---
name: dependency-upgrade
description: >
  Dependency upgrade workflow — audit, plan, upgrade, test, fix breaking changes.
  TRIGGER: 'upgrade dependencies', 'update packages', 'bump versions',
  'security vulnerability', '升级依赖', '更新包'.
---

# Dependency Upgrade

## Workflow

### 1. Audit Current State

```bash
# Python
pip list --outdated
pip-audit
safety check

# JS/TS
npm outdated
npm audit

# Go
go list -m -u all

# Rust
cargo outdated
cargo audit
```

### 2. Classify Updates

| Type | Risk | Strategy |
|------|------|----------|
| **Patch** (1.2.3 → 1.2.4) | LOW | Batch upgrade, run tests |
| **Minor** (1.2.x → 1.3.0) | MEDIUM | Upgrade one-by-one, check changelog |
| **Major** (1.x → 2.0) | HIGH | Research breaking changes, plan migration |
| **Security** (any) | CRITICAL | Upgrade immediately, regardless of version jump |

### 3. Upgrade Process

**For LOW/MEDIUM risk (batch):**
```bash
# Upgrade
pip install --upgrade <package>  # or npm update, etc.

# Test immediately
run-tests

# If pass → commit: "chore(deps): bump <packages>"
# If fail → investigate, fix, or revert that specific upgrade
```

**For HIGH risk (major version):**
1. Read the migration guide / changelog
2. Create a dedicated branch
3. Upgrade the package
4. Run tests — capture all failures
5. Fix breaking changes one by one
6. Run full test suite
7. Review diff for subtle behavioral changes
8. Commit: `chore(deps): upgrade <package> v1→v2`

### 4. Breaking Change Patterns

| Language | Common Breaks |
|----------|--------------|
| Python | Removed functions, changed signatures, new required params |
| JS/TS | ESM/CJS switch, changed exports, peer dep conflicts |
| Go | Module path changes, removed functions |
| Rust | Trait changes, removed features |

### 5. Post-Upgrade Verification

- [ ] All tests pass
- [ ] Lint clean
- [ ] Type check clean
- [ ] No new security advisories
- [ ] Manual smoke test of critical paths
- [ ] Lock file committed (requirements.txt, package-lock.json, go.sum, Cargo.lock)

## Related Skills

- **security-review** — security audit drives urgency of upgrades
- **readiness-audit** — Pillar 7 checks for vulnerable dependencies
- **autoimmune** — Mode B can auto-fix lint/type issues after upgrades
- **verification** — verify each upgrade step before committing
