---
description: "Investigate unfamiliar code before making changes. TRIGGER: 'how does X work', 'investigate', 'research this', 'understand the code', '调研', '分析一下', '看看这个怎么工作的'."
---

Activate the cc-research skill. Layered search strategy:

1. **Broad**: File structure overview, class/function listing
2. **Narrow**: Grep for specific symbols, imports, usages
3. **Deep**: Read full files, trace data flow
4. **Cross-reference**: Find all callers, impact analysis

Output a structured findings report:
- Architecture overview
- Data flow diagram
- Dependencies (internal + external)
- Risks (what could break)
- Recommendations
- Gaps (what needs human input)
