---
name: security-review
description: "Security checklist and patterns for Python applications. Use when adding auth, handling user input, working with secrets, or creating API endpoints."
---

# Security Review Checklist

## When to Trigger

- New API endpoints
- Authentication/authorization code
- User input handling
- Database query changes
- File uploads
- External API integrations
- Dependency updates

## Python Security Checklist

### Input Validation
- [ ] All user input validated (type, length, format)
- [ ] SQL queries use parameterized queries (never f-strings)
- [ ] Shell commands use `subprocess.run([...])` (never `shell=True` with user data)
- [ ] File paths validated (no `..` traversal)
- [ ] XML parsing uses defusedxml
- [ ] YAML uses `safe_load()` only

### Authentication & Authorization
- [ ] Passwords hashed with bcrypt/argon2 (use `passlib` or `bcrypt` library)
- [ ] JWT tokens validated with `python-jose` or `PyJWT` (check signature, expiry, issuer)
- [ ] Session tokens are `secrets.token_urlsafe(32)` (not `random`)
- [ ] Auth checked on every protected route (FastAPI `Depends`, Django `@login_required`)
- [ ] Rate limiting on auth endpoints (`slowapi` for FastAPI, `django-ratelimit`)

### Secrets Management
- [ ] No hardcoded secrets in source code
- [ ] Secrets loaded from environment variables
- [ ] `.env` in `.gitignore`
- [ ] Secrets not logged (passwords, tokens, PII)
- [ ] API keys have minimum necessary permissions

### API Security
- [ ] CORS properly configured (not `*` in production)
- [ ] Rate limiting on public endpoints
- [ ] Input size limits set
- [ ] Error messages don't leak internal details
- [ ] HTTPS enforced in production

### Data Protection
- [ ] PII encrypted at rest
- [ ] Sensitive data not in URL parameters
- [ ] Database connections use TLS
- [ ] Backups encrypted

### Dependencies
- [ ] `pip-audit` clean
- [ ] `safety check` clean
- [ ] No known vulnerable packages
- [ ] Dependencies pinned to specific versions

## Diagnostic Commands

```bash
bandit -r . -f json         # Python security scan
pip-audit                   # Dependency audit
safety check               # Vulnerability check
```

## Common Vulnerability Patterns

| Pattern | Risk | Fix |
|---------|------|-----|
| f-string in SQL | Injection | Parameterized query |
| `subprocess(shell=True)` + user input | Command injection | Use list args |
| `yaml.load()` | Code execution | `yaml.safe_load()` |
| Hardcoded secret | Credential leak | Environment variable |
| Missing rate limit | DoS/brute force | Add rate limiting |
| Debug mode in prod | Info disclosure | Disable debug |
| Bare `except` | Silent failure | Catch specific exceptions |

## Related Skills

- **refinement** — security scan is one dimension of quality hardening
- **readiness-audit** — Pillar 7 uses security-review findings
- **deploy** — security checklist before deployment
- **python-patterns** — secure coding idioms
