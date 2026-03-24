---
description: >
  Run verification commands and confirm output before any completion claims.
  Evidence before assertions — no completion claims without fresh verification.
  TRIGGER: 'verify', 'check', 'is it done', 'run tests', 'confirm complete'.
  FLOWS INTO: cc-refinement, cc-commit.
---

Activate the cc-verification skill.

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

## The Gate Function

1. **IDENTIFY** — what command proves this claim?
2. **RUN** — execute the full command (fresh, complete)
3. **READ** — full output, check exit code, count failures
4. **VERIFY** — does output confirm the claim?
5. **ONLY THEN** — make the claim with evidence

## Verification Commands by Language

| Language | Lint | Types | Tests | Build |
|----------|------|-------|-------|-------|
| Python | `ruff check .` | `mypy .` | `pytest -v` | `python -m py_compile` |
| JS/TS | `eslint .` | `tsc --noEmit` | `npm test` | `npm run build` |
| Go | `golangci-lint run` | built-in | `go test ./...` | `go build ./...` |
| Rust | `cargo clippy` | built-in | `cargo test` | `cargo build` |

Full verification = ALL four pass. Partial is not sufficient.
