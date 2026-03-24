---
description: >
  Multi-tool search strategy — RP MCP first, then cc-flow CLI, then built-in.
  Choose the right search tool for each task.
  TRIGGER: 'search strategy', 'how to search', 'find code', 'exploring code', 'code search'.
  NOT FOR: known file paths — just use Read directly.
  FLOWS INTO: cc-research.
---

Activate the cc-search-strategy skill.

## Priority Chain

```
Search:    RP file_search       -> cc-flow search  -> Grep
Edit:      RP apply_edits       -> cc-flow apply   -> Edit
Deep:      RP context_builder   -> cc-flow rp builder -> Read + Grep
Structure: RP get_code_structure -> cc-flow rp structure -> Grep def/class
```

## Decision Framework

- **Exact text/pattern** -> Grep (fastest)
- **Code pattern** -> RP file_search
- **Meaning/concept** -> cc-flow search (Morph semantic)
- **Function/class defs** -> RP get_code_structure
- **Cross-file understanding** -> RP context_builder
- **Relevance ranking** -> cc-flow search --rerank
