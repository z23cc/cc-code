---
description: "Scout unified entry — run any scout by type. Usage: /cc-scout [type]. Types: practices, repo, docs, docs-gap, security, testing, tooling, build, env, observability, gaps, context. TRIGGER: 'scout', 'scan for', '侦察', '检查'."
---

Unified entry point for all 12 cc-scout-* skills.

## Usage

`/cc-scout [type] [optional context]`

| Type | Skill | What it does |
|------|-------|-------------|
| `practices` | cc-scout-practices | Best practices for a feature (external) |
| `repo` | cc-scout-repo | Existing patterns in this codebase |
| `docs` | cc-scout-docs | Framework/library documentation |
| `docs-gap` | cc-scout-docs-gap | Which docs need updating |
| `security` | cc-scout-security | Security configuration audit |
| `testing` | cc-scout-testing | Test infrastructure audit |
| `tooling` | cc-scout-tooling | Lint/format/type check setup |
| `build` | cc-scout-build | Build system and CI/CD |
| `env` | cc-scout-env | Environment setup audit |
| `observability` | cc-scout-observability | Logging/tracing/metrics |
| `gaps` | cc-scout-gaps | Missing requirements/edge cases |
| `context` | cc-scout-context | Token-efficient exploration |

## Examples

```
/cc-scout practices add rate limiting to FastAPI
/cc-scout repo authentication patterns
/cc-scout security
/cc-scout gaps add password reset feature
/cc-scout docs FastAPI middleware
```

## If no type specified

Run the 3 most common scouts:
1. `cc-scout-repo` — existing patterns
2. `cc-scout-gaps` — missing requirements
3. `cc-scout-practices` — best practices

For a full assessment, use `/cc-prime` instead.
