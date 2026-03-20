---
name: brainstorming
description: "MUST use before any creative work — creating features, building components, adding functionality. Explores intent, requirements and design before implementation."
---

# Brainstorming Ideas Into Designs

Turn ideas into fully formed designs through collaborative dialogue. Understand context, ask questions one at a time, present the design, get approval.

<HARD-GATE>
Do NOT write any code, scaffold any project, or take any implementation action until you have presented a design and the user has approved it. This applies to EVERY project regardless of perceived simplicity.
</HARD-GATE>

## SPARC Phases (Specification → Pseudocode → Architecture → Refinement → Completion)

This skill covers **S** (Specification) and **A** (Architecture). The plan skill covers **P** and **R**. TDD covers **C**.

## Checklist

1. **[S] Explore project context** — check files, docs, recent commits
2. **[S] Ask clarifying questions** — one at a time, understand purpose/constraints/success criteria
3. **[S] Define acceptance criteria** — measurable, testable outcomes (not vague "should work")
4. **[A] Propose 2-3 approaches** — with trade-offs and your recommendation
5. **[A] Present design** — in sections scaled to complexity, get approval after each section
6. **Write design doc** — save to `docs/specs/YYYY-MM-DD-<topic>-design.md`
7. **User reviews spec** — ask user to review before proceeding
8. **Transition to implementation** — invoke plan skill

## The Process

**Understanding the idea (Interview Protocol):**
- Check current project state first (files, docs, recent commits)
- If the request describes multiple independent subsystems, flag this immediately — decompose first
- Ask questions one at a time, prefer multiple choice when possible
- Cover these dimensions systematically:
  1. **Who** — target users, personas, access levels
  2. **What** — core features, acceptance criteria, out-of-scope
  3. **Why** — business goal, success metrics, what happens if we don't build this
  4. **How** — technical constraints, existing integrations, performance requirements
  5. **Edge cases** — error scenarios, concurrent access, empty states, limits
  6. **Non-functional** — security, scalability, accessibility, i18n
- Stop interviewing when answers start repeating or user says "enough"

**Exploring approaches:**
- Propose 2-3 different approaches with trade-offs
- Lead with your recommended option and explain why

**Presenting the design:**
- Scale each section to its complexity
- Ask after each section whether it looks right
- Cover: architecture, components, data flow, error handling, testing

**Design for isolation:**
- Break into smaller units with one clear purpose each
- Well-defined interfaces, independently testable
- Smaller units are easier for agents to reason about

**Working in existing codebases:**
- Explore current structure before proposing changes
- Follow existing patterns
- Only include targeted improvements where they serve the current goal

## After the Design

- Write spec to `docs/specs/YYYY-MM-DD-<topic>-design.md`
- Commit the design document
- Ask user to review before proceeding
- Invoke the plan skill to create implementation plan

## Key Principles

- **One question at a time** — don't overwhelm
- **Multiple choice preferred** — easier to answer
- **YAGNI ruthlessly** — remove unnecessary features
- **Explore alternatives** — always propose 2-3 approaches
- **Incremental validation** — present design, get approval, move on
