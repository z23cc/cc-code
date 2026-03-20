---
name: research
description: >
  Structured codebase research methodology — layered search, cross-reference
  tracing, dependency analysis, findings synthesis. Use BEFORE making changes
  to unfamiliar code.
  TRIGGER: 'investigate', 'how does X work', 'understand this', 'research',
  '调研', '分析一下'.
---

# Research Methodology

Understand before you change. This skill provides a systematic approach to investigating unfamiliar code.

## Layered Search Strategy

```
Layer 1: BROAD — What exists?
  → Glob for file patterns, tree overview
  → Semantic search for concepts

Layer 2: NARROW — Where specifically?
  → Grep for exact symbols, imports, usages
  → Symbol search for definitions

Layer 3: DEEP — How does it work?
  → Read full files, trace data flow
  → Dependency graph analysis

Layer 4: CROSS-REFERENCE — What depends on it?
  → Grep for callers, importers
  → Impact analysis for changes
```

## Research Workflow

### Phase 1: Scope

Define the research question clearly:
- "How does authentication work in this project?"
- "What would break if I change the User model?"
- "Where is the payment flow and what external services does it call?"

### Phase 2: Discovery

```bash
# Layer 1: Broad structure
find src/ -name "*.py" | head -30          # File layout
grep -r "class.*:" src/ --include="*.py"   # All classes
grep -r "def " src/auth/ --include="*.py"  # Functions in area

# Layer 2: Specific symbols
grep -rn "UserService" src/                # All usages
grep -rn "from.*import.*UserService" src/  # All importers

# Layer 3: Deep read
# Read the file, understand the logic

# Layer 4: Cross-reference
grep -rn "user_service\." src/             # Method calls
grep -rn "UserService" tests/              # Test coverage
```

### Phase 3: Dependency Mapping

```
Component A
  ├── depends on: B, C
  ├── depended on by: D, E
  ├── external calls: Stripe API, Redis
  └── config: DATABASE_URL, STRIPE_KEY
```

Build this map for each component you'll touch.

### Phase 4: Findings Synthesis

Structure your findings:

```markdown
## Research: [Topic]

### Architecture
- [How it's structured, key components]

### Data Flow
- [Input → Processing → Output path]

### Dependencies
- Internal: [modules that depend on this]
- External: [APIs, databases, services]

### Risks
- [What could break if we change this]

### Recommendations
- [How to proceed with changes]

### Gaps
- [What I couldn't determine — needs human input]
```

## When to Research vs. Just Start

| Signal | Action |
|--------|--------|
| You've never seen this code | Research first |
| Change touches 3+ files | Research first |
| Change affects public API | Research first |
| Simple rename/format | Just do it |
| Adding new isolated feature | Minimal research |
| Bug with clear stack trace | Follow the trace, minimal research |

## Related Skills

- **search-strategy** — which tools to use for each search layer
- **brainstorming** — research feeds into the brainstorming phase
- **plan** — research findings inform the implementation plan
- **debugging** — Phase 1 (Root Cause Investigation) uses research patterns
