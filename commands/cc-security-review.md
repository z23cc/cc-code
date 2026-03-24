---
agent: "security-reviewer"
description: >
  Security checklist and patterns for Python applications. Auth, input validation,
  secrets, API endpoints, dependencies.
  TRIGGER: 'security review', 'security check', 'auth review', 'injection', 'vulnerability scan'.
  NOT FOR: general code review — use cc-review. NOT FOR: project health — use cc-readiness-audit.
  FLOWS INTO: cc-review, cc-refinement.
---

Activate the cc-security-review skill.

## Checklist Areas

1. **Input Validation** — SQL injection, shell injection, path traversal, YAML/XML
2. **Auth & Authorization** — password hashing, JWT validation, session tokens, rate limiting
3. **Secrets Management** — no hardcoded secrets, env vars, .gitignore, no PII in logs
4. **API Security** — CORS, rate limiting, input size limits, error message leakage
5. **Data Protection** — PII encryption, TLS, no sensitive data in URLs
6. **Dependencies** — pip-audit, safety check, pinned versions

## Diagnostic Commands

```bash
bandit -r . -f json         # Python security scan
pip-audit                   # Dependency audit
safety check               # Vulnerability check
```
