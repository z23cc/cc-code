---
name: plan
description: "Create comprehensive implementation plans with TDD workflow. Use when you have a spec or requirements for a multi-step task, before touching code."
---

# Writing Plans

Write comprehensive implementation plans assuming the engineer has zero context. Document everything: which files to touch, code, testing, exact commands. Give the plan as bite-sized tasks. DRY. YAGNI. TDD.

## File Structure

Before defining tasks, map out which files will be created or modified:
- Design units with clear boundaries and well-defined interfaces
- Prefer smaller, focused files over large ones
- Follow existing codebase patterns

## Bite-Sized Task Granularity

Each step is one action (2-5 minutes):
- "Write the failing test" → step
- "Run it to verify it fails" → step
- "Implement minimal code to pass" → step
- "Run tests to verify they pass" → step
- "Commit" → step

## Plan Document Header

```markdown
# [Feature Name] Implementation Plan

**Goal:** [One sentence]
**Architecture:** [2-3 sentences]
**Tech Stack:** [Key technologies]
```

## Task Structure

```markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

- [ ] **Step 1: Write failing test**
  ```python
  def test_specific_behavior():
      result = function(input)
      assert result == expected
  ```

- [ ] **Step 2: Run test to verify it fails**
  Run: `pytest tests/path/test.py::test_name -v`
  Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

- [ ] **Step 4: Run tests to verify they pass**
  Run: `pytest tests/path/test.py -v`
  Expected: PASS

- [ ] **Step 5: Commit**
```

## Sizing and Phasing

Break large features into independently deliverable phases:
- **Phase 1**: Minimum viable — smallest slice with value
- **Phase 2**: Core experience — complete happy path
- **Phase 3**: Edge cases — error handling, polish
- **Phase 4**: Optimization — performance, monitoring

Each phase should be mergeable independently.

## Related Skills

- **brainstorming** — use BEFORE planning to explore intent and design
- **tdd** — every task in the plan should follow Red-Green-Refactor
- **verification** — verify each phase before moving to the next

## Remember
- Exact file paths always
- Complete code in plan (not "add validation")
- Exact commands with expected output
- DRY, YAGNI, TDD, frequent commits
