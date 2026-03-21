---
agent: "refactor-cleaner"
description: "Simplify and clean up code. TRIGGER: 'clean up', 'simplify', 'remove dead code', 'refactor', '简化', '清理代码'. NOT for: build errors (/fix), new features (/tdd)."
---

Review recently changed code for simplification opportunities. Dispatch the **refactor-cleaner** agent to:

1. Identify dead code, unused imports, duplicate patterns
2. Simplify complex logic while preserving functionality
3. Apply Pythonic idioms where appropriate
4. Run tests after each change to verify no regressions
5. Report what was simplified and why
