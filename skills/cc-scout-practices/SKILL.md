---
name: cc-scout-practices
description: >
  Gather modern best practices and pitfalls BEFORE implementing a change.
  Searches official docs, GitHub repos, and community guidance for current year.
  TRIGGER: 'best practices for', 'how should I implement', 'what are the pitfalls',
  'community guidance', '最佳实践', '有什么坑', '推荐做法'.
  NOT FOR: existing repo patterns — use cc-scout-repo instead.
  FLOWS INTO: cc-brainstorming, cc-plan.
---

# Practice Scout — Best Practices Before Code

## Purpose

Research-only. Find what the community recommends for a specific implementation task BEFORE writing code. Focus on DO/DON'T, not full implementations.

## Search Strategy

### 1. Identify Tech Stack

Auto-detect from project files:
- `pyproject.toml` → Python (check version, frameworks)
- `package.json` → JS/TS (check dependencies)
- `go.mod` → Go
- `Cargo.toml` → Rust

### 2. Search for Current Guidance

```bash
# WebSearch queries (use current year)
"[framework] [feature] best practices 2025"
"[feature] common mistakes [framework]"
"[feature] security considerations [language]"
```

Prefer: official docs > reputable blogs > Stack Overflow

### 3. Find Real-World Examples on GitHub

```bash
# BEST: cc-flow github search (no cloning needed)
cc-flow github-search "[feature] implementation" --repo fastapi/fastapi
cc-flow github-search "[feature] pattern" --repo pallets/flask

# Alternative: gh CLI
gh search code "[pattern]" --language python --json repository,path -L 10

# Quick quality check
gh api repos/{owner}/{repo} --jq '{stars: .stargazers_count, pushed: .pushed_at}'
```

**Quality heuristics:** Stars >= 1000, recent activity, not a fork, production code path.

### 4. Check Anti-Patterns

- What NOT to do
- Deprecated approaches
- Performance pitfalls
- Security considerations (OWASP if relevant)

## Output Format

```markdown
## Best Practices for [Feature]

### Do
- [Practice]: [why, with source link]
- [Practice]: [why]

### Don't
- [Anti-pattern]: [why it's bad]
- [Deprecated approach]: [what to use instead]

### Real-World Examples
- `owner/repo` (stars) - [how they implement it]

### Security
- [Consideration]: [guidance]

### Performance
- [Tip]: [impact]

### Sources
- [Title](url) - [what it covers]
```

## Rules

- Search for 2025/2026 guidance (current year)
- Include source links for verification
- Focus on practical DO/DON'T, not theory
- Be specific to the tech stack — skip generalities
- Focus on non-obvious gotchas
- Keep code snippets < 10 lines (illustrate the point, not full implementation)


## On Completion

When done:
```bash
cc-flow skill ctx save cc-scout-practices --data '{"score": 85, "findings": [...]}'
cc-flow skill next
```

## Related Skills

- **cc-scout-repo** — find existing patterns in THIS codebase
- **cc-scout-docs** — find framework/library documentation
- **cc-research** — deeper codebase investigation
- **cc-brainstorming** — practices inform design decisions
