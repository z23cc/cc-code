---
description: "Fix build/type/test errors minimally. TRIGGER: 'build broken', 'type errors', 'tests failing', 'lint errors', '构建失败', '修复报错'. NOT for: new features (/tdd), refactoring (/simplify)."
---

Dispatch the **build-fixer** agent to resolve build errors with minimal changes.

1. Auto-detect project language:
   - Python: `ruff check . && mypy . && pytest --tb=short`
   - JS/TS: `npx tsc --noEmit && npm test`
   - Go: `go build ./... && go test ./...`
   - Rust: `cargo check && cargo test`
2. Categorize errors by type and severity
3. Fix each error with the smallest possible change
4. Verify the fix doesn't break other code
5. Report what was fixed

Rules: No refactoring, no architecture changes, no feature additions. Just get the build green.
