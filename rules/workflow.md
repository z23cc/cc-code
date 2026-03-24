---
description: "Development workflow gates and context protocol"
alwaysApply: true
---

# Workflow Rules

## Required Sequences
- **Feature**: brainstorm → plan → tdd → review → commit (skip brainstorm = skip)
- **Bug fix**: debug (root cause) → regression test → fix → commit
- **Hotfix** (≤10 lines): implement → review (1 loop) → commit

## Gates
- **Before commit**: `cc-flow verify` must pass (lint + test)
- **Review verdicts**: SHIP (proceed) / NEEDS_WORK (auto-fix, max 3 loops) / MAJOR_RETHINK (stop, discuss)
- **Before push**: no secrets (.env, credentials, tokens)

## Context Protocol
After each skill: `cc-flow skill ctx save <name> --data '{...}'`
In chains: `cc-flow chain advance --data '{...}'`
Query: `cc-flow skill next` / `cc-flow skill graph`
