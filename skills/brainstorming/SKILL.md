---
name: brainstorming
description: "MUST use before any creative work — creating features, building components, adding functionality. Explores intent, requirements and design before implementation."
---

# Brainstorming Ideas Into Designs

Turn ideas into fully formed designs through collaborative dialogue. Understand context, ask questions one at a time, present the design, get approval.

<HARD-GATE>
Do NOT write any code, scaffold any project, or take any implementation action until you have presented a design and the user has approved it. This applies to EVERY project regardless of perceived simplicity.
</HARD-GATE>

## Checklist

1. **Explore project context** — check files, docs, recent commits
2. **Ask clarifying questions** — one at a time, understand purpose/constraints/success criteria
3. **Propose 2-3 approaches** — with trade-offs and your recommendation
4. **Present design** — in sections scaled to complexity, get approval after each section
5. **Write design doc** — save to `docs/specs/YYYY-MM-DD-<topic>-design.md`
6. **User reviews spec** — ask user to review before proceeding
7. **Transition to implementation** — invoke plan skill

## The Process

**Understanding the idea:**
- Check current project state first (files, docs, recent commits)
- If the request describes multiple independent subsystems, flag this immediately — decompose first
- Ask questions one at a time, prefer multiple choice when possible
- Focus on: purpose, constraints, success criteria

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
