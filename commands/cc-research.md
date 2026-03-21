---
team: "research"
agent: "researcher"
description: "Investigate unfamiliar code before making changes. TRIGGER: 'how does X work', 'investigate', 'research this', 'understand the code', '调研', '分析一下', '看看这个怎么工作的'."
---

Activate the cc-research skill with **Research team** dispatch.

## Default Team: researcher → architect (if needed)

### Step 1: Dispatch researcher
Layered search strategy:
1. **Broad**: File structure overview, class/function listing
2. **Narrow**: Grep for specific symbols, imports, usages
3. **Deep**: Read full files, trace data flow
4. **Cross-reference**: Find all callers, impact analysis

Write findings to `/tmp/cc-team-research.md`.

### Step 2: Dispatch architect (for complex systems)
If research reveals complex architecture:
- Review findings
- Draw component boundaries
- Identify risks and dependencies
- Write architecture notes to `/tmp/cc-team-design.md`

### Output
Structured findings report:
- Architecture overview
- Data flow diagram
- Dependencies (internal + external)
- Risks (what could break)
- Recommendations
- Gaps (what needs human input)
