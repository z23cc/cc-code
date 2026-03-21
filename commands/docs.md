---
description: "Update project documentation. TRIGGER: 'update docs', 'write README', 'changelog', 'sync docs', '更新文档', '写文档'. Keeps docs in sync with code."
---

Activate the docs skill. Determine what needs updating:

1. `git log --oneline` — what changed recently?
2. Check each doc for staleness:
   - README.md — does Quick Start still work? Usage examples current?
   - CHANGELOG.md — are recent changes logged?
   - CLAUDE.md — do commands/conventions match reality?
3. Update stale docs
4. Verify code examples in docs still work
5. Commit: `docs: update documentation`
