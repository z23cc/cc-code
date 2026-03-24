---
name: cc-prd-validate
description: >
  Validate a PRD or spec against 10 quality checks: clarity, density, SMART scoring,
  traceability, completeness, measurability, implementation leakage, and more.
  Catches spec issues before investing in planning and implementation.
  TRIGGER: 'validate prd', 'check spec quality', 'is this PRD good', 'review requirements',
  '验证PRD', '检查需求文档', 'PRD质量'.
  NOT FOR: writing the PRD — use cc-prd. NOT FOR: requirement gate — use cc-requirement-gate.
  DEPENDS ON: cc-prd (PRD as input).
  FLOWS INTO: cc-plan (validated PRD ready for planning).
---

# PRD Validation Pipeline

10-step validation pipeline for PRDs and specs. Inspired by BMAD methodology.

## Input

A PRD or spec file — typically from `/cc-prd` output or user-provided.

## Validation Steps

### Step 1: Document Discovery
- Locate the PRD/spec file
- Detect format (single file vs folder/sharded)
- Count sections, word count, requirement count

### Step 2: Format & Structure
- [ ] Has clear sections (Problem, Solution, Requirements, Success Metrics)
- [ ] Consistent heading hierarchy
- [ ] No orphaned content outside sections

### Step 3: Density Check
- [ ] Each requirement is atomic (one thing per requirement)
- [ ] No compound requirements ("X and Y and Z" in one bullet)
- [ ] Requirements are specific, not vague ("fast" → "< 200ms p95")

### Step 4: Clarity Scoring
Rate each requirement:
- **Clear**: An engineer can implement without questions
- **Ambiguous**: Two engineers could interpret differently
- **Vague**: Cannot be implemented as-is

Target: ≥ 80% Clear

### Step 5: SMART Validation
Each requirement scored against:
- **S**pecific — clearly defined scope
- **M**easurable — has success metric
- **A**ttainable — feasible with current stack
- **R**elevant — ties to stated goal
- **T**raceable — links to user story or business goal

Score: 0-5 per requirement, target ≥ 3.5 average

### Step 6: Traceability
- [ ] Each requirement traces to a user story or business goal
- [ ] No orphan requirements (exist but serve no stated goal)
- [ ] Dependencies between requirements are explicit

### Step 7: Completeness
- [ ] Happy path defined
- [ ] Error/edge cases covered
- [ ] Non-functional requirements present (performance, security, accessibility)
- [ ] Out of scope explicitly stated
- [ ] Assumptions listed

### Step 8: Implementation Leakage Check
- [ ] No implementation details in requirements ("use Redis" → "cache with sub-100ms latency")
- [ ] Technology choices are in architecture doc, not PRD
- [ ] Requirements describe WHAT, not HOW

### Step 9: Measurability
- [ ] Success metrics are quantifiable
- [ ] Acceptance criteria are testable
- [ ] No subjective criteria ("should feel fast")

### Step 10: Validation Report

```markdown
## PRD Validation Report

### Summary
- Document: [path]
- Requirements: [count]
- Word count: [N]

### Scores
| Check | Score | Pass? |
|-------|-------|-------|
| Format & Structure | 8/10 | ✅ |
| Density | 7/10 | ✅ |
| Clarity | 85% clear | ✅ |
| SMART Average | 3.8/5 | ✅ |
| Traceability | 90% traced | ✅ |
| Completeness | 7/10 | ⚠️ Missing error cases |
| Implementation Leakage | 0 leaks | ✅ |
| Measurability | 80% measurable | ✅ |

### Issues Found
1. [MEDIUM] Requirement R-003 is compound — split into R-003a and R-003b
2. [HIGH] No error handling defined for payment flow
3. [LOW] Success metric "fast loading" needs quantification

### Decision
- **PASS** — PRD ready for planning (minor fixes recommended)
- **REVISE** — [N] issues must be fixed before planning
```

## On Completion

```bash
cc-flow skill ctx save cc-prd-validate --data '{"decision": "PASS", "clarity_score": 85, "smart_avg": 3.8, "issues": 3}'
cc-flow skill next
```

## Related Skills

- **cc-prd** — produces the PRD this skill validates
- **cc-requirement-gate** — lighter pre-check (5 dimensions vs 10 steps)
- **cc-plan** — consumes the validated PRD
