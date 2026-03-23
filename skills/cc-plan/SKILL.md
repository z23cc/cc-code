---
name: cc-plan
description: >
  Create comprehensive implementation plans with TDD workflow. Use before touching code.
  TRIGGER: 'plan', 'design', 'how to build', '规划', '写计划'.
  NOT FOR: brainstorming (/brainstorm).
  DEPENDS ON: cc-brainstorm (design before planning).
  FLOWS INTO: cc-tdd (implement the plan), cc-work (execute end-to-end).
---

# Writing Plans

Write comprehensive implementation plans assuming the engineer has zero context. Document everything: which files to touch, code, testing, exact commands. Give the plan as bite-sized tasks. DRY. YAGNI. TDD.

## SPARC Context

This skill covers **P** (Pseudocode) and **R** (Refinement) from SPARC. Use brainstorming first for S+A, then this skill, then TDD for C.

## Optional: Pseudocode-First (for algorithm-heavy tasks)

For complex logic (search algorithms, state machines, data pipelines), write pseudocode before implementation:

```
FUNCTION find_optimal_route(graph, start, end):
    frontier = PriorityQueue()
    frontier.push(start, priority=0)
    costs = {start: 0}

    WHILE frontier is not empty:
        current = frontier.pop()
        IF current == end: RETURN reconstruct_path(current)

        FOR neighbor IN graph.neighbors(current):
            new_cost = costs[current] + graph.cost(current, neighbor)
            IF neighbor NOT IN costs OR new_cost < costs[neighbor]:
                costs[neighbor] = new_cost
                frontier.push(neighbor, priority=new_cost + heuristic(neighbor, end))

    RETURN None  # No path found

COMPLEXITY: O(E log V) time, O(V) space
```

Include pseudocode in the plan when: the task involves non-trivial algorithms, data transformations, or state management. Skip for simple CRUD.

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

## Task Sizing Guide

| Size | Lines | Time | When |
|------|-------|------|------|
| **XS** | < 5 | 1 min | Config change, typo fix |
| **S** | < 20 | 2-5 min | Add type hints, rename, simple test |
| **M** | < 50 | 5-15 min | New function with test, bug fix |
| **L** | < 100 | 15-30 min | New endpoint, service method |
| **XL** | 100+ | 30+ min | **Split this** — too big for one task |

**Red flags** that a task is too big:
- Touches 5+ files → split by file group
- Has "and" in the title → split into two tasks
- Needs 2+ commits → split per commit

## Converting Plan to cc-flow Tasks

```bash
CCFLOW="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"

# Option 1: Auto-import from plan markdown
$CCFLOW epic import --file docs/specs/auth-design.md --sequential

# Option 2: Manual creation with templates
$CCFLOW epic create --title "Add JWT Authentication"
$CCFLOW task create --epic epic-1-add-jwt --title "Define User model" --size S --template feature --tags "auth,domain"
$CCFLOW task create --epic epic-1-add-jwt --title "Implement token service" --size M --template feature --tags "auth,service" --deps "epic-1-add-jwt.1"
$CCFLOW task create --epic epic-1-add-jwt --title "Add login endpoint" --size M --template feature --tags "auth,api" --deps "epic-1-add-jwt.2"

# View the plan
$CCFLOW graph --epic epic-1-add-jwt --format ascii
```

## E2E Example

```
Brainstorming output: "Add rate limiting to /login and /register, 5/min per IP, Redis"

Plan:
# Rate Limiting Implementation Plan

**Goal:** Prevent brute-force attacks on auth endpoints
**Architecture:** Redis sliding window counter as FastAPI middleware
**Tech Stack:** FastAPI, Redis (existing), pytest

### Task 1: Rate Limiter Domain Logic [S]
Files: Create src/domain/rate_limiter.py, tests/test_rate_limiter.py

- [ ] Write test: test_allows_under_limit, test_blocks_over_limit
- [ ] Run: pytest → FAIL
- [ ] Implement RateLimiter dataclass with check() method (pure logic, no Redis)
- [ ] Run: pytest → PASS
- [ ] Commit: "feat(domain): add rate limiter logic"

### Task 2: Redis Adapter [M]
Files: Create src/adapters/redis_rate_store.py, tests/test_redis_rate.py
Depends on: Task 1

- [ ] Write test with fakeredis: test_increment_and_check
- [ ] Implement RedisRateStore (implements RateStore protocol)
- [ ] Run: pytest → PASS
- [ ] Commit: "feat(adapters): add Redis rate limiting store"

### Task 3: Middleware + Routes [M]
Files: Modify src/api/auth_routes.py, Create src/middleware/rate_limit.py
Depends on: Task 2

- [ ] Write test: test_login_rate_limited_returns_429
- [ ] Add rate limit middleware to /login, /register
- [ ] Run: pytest → PASS
- [ ] Commit: "feat(api): add rate limiting to auth endpoints"

→ Convert: cc-flow epic import --file docs/specs/rate-limit-plan.md --sequential
```

## Related Skills

- **cc-brainstorming** — use BEFORE planning to explore intent and design
- **cc-tdd** — every task in the plan should follow Red-Green-Refactor
- **cc-verification** — verify each phase before moving to the next
- **cc-task-tracking** — convert plan to cc-flow tasks for tracking

## Remember
- Exact file paths always
- Complete code in plan (not "add validation")
- Exact commands with expected output
- DRY, YAGNI, TDD, frequent commits
