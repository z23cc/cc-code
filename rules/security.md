---
description: "Security rules — enforced across all code changes"
alwaysApply: true
---

# Security Rules

- No hardcoded secrets in source code (use env vars)
- Use parameterized queries for all SQL (never f-strings)
- Use `subprocess.run([...])` not `shell=True` with user input
- Use `yaml.safe_load()` not `yaml.load()`
- Validate and sanitize all external input
- Hash passwords with bcrypt or argon2
- No debug mode in production
- Don't log sensitive data (passwords, tokens, PII)
- Pin dependency versions
- Run `bandit` and `pip-audit` before release
