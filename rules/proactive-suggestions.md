---
description: "AI-first skill routing — analyze intent + context, then suggest optimal skill combination"
alwaysApply: true
---

# AI-First Skill Routing

## Protocol: Analyze Before Suggesting

When the user describes a task, DO NOT just keyword-match. Instead:

1. **Analyze intent**: What is the user actually trying to achieve?
2. **Check project context**: What files exist? What's the git state? Active tasks?
3. **Consider complexity**: Simple fix vs multi-step feature vs architectural change?
4. **Select skill combination**: Pick 1-3 skills that work together, not just the closest keyword match

## Decision Framework

```
User says something
    ↓
Step 1: Classify the intent
    ├── BUILD (new feature, new project, new endpoint)
    ├── FIX (bug, error, crash, broken)
    ├── IMPROVE (refactor, optimize, clean up, performance)
    ├── VERIFY (test, review, audit, check)
    ├── SHIP (deploy, release, push, PR)
    ├── UNDERSTAND (research, how does, explain, investigate)
    └── PLAN (design, architecture, spec, requirements)
    ↓
Step 2: Check if multi-skill combination is better
    Examples:
    - "optimize database queries" → cc-performance (profile) + cc-database (patterns) + cc-review
    - "add auth to API" → cc-architecture (ADR) + cc-fastapi (patterns) + cc-security-review + cc-tdd
    - "this page is slow" → cc-browser-qa (measure) + cc-optimize (fix) + cc-review
    - "not sure if this feature is worth building" → cc-product-lens + cc-requirement-gate + cc-elicit
    ↓
Step 3: Run cc-flow go or suggest specific skills
    - Simple task → cc-flow go "description" (auto-routes to chain)
    - Multi-domain task → suggest skill combination explicitly
    - Unknown/complex → cc-flow go "description" --dry-run first
```

## Skill Catalog by Domain

### Development
| Domain | Primary Skill | Supporting Skills |
|--------|--------------|-------------------|
| New feature | `/cc-brainstorm` | + requirement-gate + plan + architecture + tdd |
| Bug fix | `/cc-debug` | + tdd + review |
| Refactor | `/cc-simplify` | + research + review |
| Performance | `/cc-performance` | + browser-qa + optimize |
| Testing | `/cc-python-testing` | + tdd + verification |
| Error handling | `/cc-error-handling` | + tdd + review |
| Async/concurrent | `/cc-async-patterns` | + tdd + review |
| Database | `/cc-database` | + tdd + security-review |
| API | `/cc-fastapi` | + architecture + security-review + tdd |
| Logging | `/cc-logging` | + tdd + deploy |

### Quality & Review
| Domain | Primary Skill | Supporting Skills |
|--------|--------------|-------------------|
| Code review | `/cc-review` | severity-weighted, agent lens |
| Security | `/cc-security-review` | + scout-security |
| Visual QA | `/cc-browser-qa` | + qa + optimize |
| Accessibility | `/cc-browser-qa` | (WCAG checks built-in) |
| Full audit | `/cc-audit` | + readiness-audit + qa-report |

### Planning & Product
| Domain | Primary Skill | Supporting Skills |
|--------|--------------|-------------------|
| Idea validation | `/cc-office-hours` | + product-lens |
| Product thinking | `/cc-product-lens` | + requirement-gate + elicit |
| Requirements | `/cc-prd` | + prd-validate + requirement-gate |
| Architecture | `/cc-architecture` | + elicit (pre-mortem) |
| Challenge plan | `/cc-grill-me` | + elicit (red team) |
| Dependencies | `/cc-deps` | + work |

### Execution
| Domain | Primary Skill | Supporting Skills |
|--------|--------------|-------------------|
| Execute tasks | `/cc-work` | + worktree |
| Autonomous | `/cc-ralph` | + autonomous-loops |
| Team dispatch | `/cc-team-builder` | + teams + parallel-agents |
| Ship | `/cc-ship` | + review + verification |
| Deploy | `/cc-deploy` | + readiness-audit |

## Multi-Skill Combination Patterns

When the task touches multiple domains, combine skills:

```
"Build a payment API with Stripe"
→ cc-brainstorm (design) → cc-architecture (ADR: Stripe integration)
  → cc-fastapi (API patterns) → cc-security-review (payment safety)
  → cc-tdd (implement) → cc-review → cc-commit

"Our dashboard is slow and has accessibility issues"
→ cc-browser-qa (measure LCP + WCAG) → cc-performance (profile)
  → cc-optimize (fix) → cc-browser-qa (verify) → cc-commit

"We need to refactor the auth module, it's getting complex"
→ cc-research (map dependencies) → cc-elicit (first principles)
  → cc-architecture (ADR) → cc-simplify (refactor) → cc-review
```

## Contextual Triggers (Auto-Detect)

| When you notice... | Suggest |
|---------------------|---------|
| User describes a new feature | `cc-flow go "description"` (auto-routes to feature chain) |
| User has a plan but hasn't validated | `/cc-grill-me` or `/cc-elicit` |
| User debugging and stuck after 2 attempts | `/cc-debug` with PUA escalation |
| User says "is this ready?" | `/cc-readiness-audit` + `/cc-browser-qa` |
| User about to implement without design | `/cc-brainstorm` → `/cc-architecture` first |
| User mentions performance concern | `/cc-browser-qa` (measure first) → then `/cc-optimize` |
| Multiple independent tasks | `/cc-team-builder` → `/cc-parallel-agents` |
| User about to push/deploy | `/cc-review` → `/cc-verification` first |
| User mentions "production" or "careful" | `cc-flow careful --enable` |
| Task involves auth/secrets/payments | Auto-add `/cc-security-review` to the chain |
| Task touches database schema | Auto-add `/cc-database` patterns |
| User wants to understand code | `/cc-research` → `/cc-scout-repo` |
| User unsure what to do | `cc-flow go "describe task"` — let routing decide |

## Rules
- Analyze BEFORE suggesting — don't just keyword match
- Frame as specific combination: "I'd suggest `/cc-performance` to measure first, then `/cc-optimize` to fix"
- Suggest ONCE per session per skill (don't nag)
- Max 3 skills in one suggestion
- If user says "stop suggesting", respect immediately
- When in doubt: `cc-flow go "description" --dry-run` to preview the best route
