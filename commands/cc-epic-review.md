---
description: >
  Epic completion review — verify all tasks implement the epic spec requirements.
  TRIGGER: 'epic review', 'completion review', 'verify epic', 'check if done',
  '验收', '完成审查'.
---

Activate the cc-epic-review skill.

## Input

User provides an epic ID: `/cc-epic-review epic-1`

## Steps

```bash
CCFLOW="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"
```

### 1. Verify all tasks done

```bash
$CCFLOW progress --epic $EPIC_ID --json
```

If not 100%, show remaining tasks and ask user if they want to proceed anyway.

### 2. Read epic spec

```bash
$CCFLOW show $EPIC_ID
```

### 3. Extract requirements

Parse the spec for ALL explicit requirements (acceptance criteria, API contracts,
data models, business rules, non-functional).

### 4. Verify each requirement

For each requirement:
- Read the implementation code
- Read the tests
- Mark as DONE / PARTIAL / MISSING / DRIFT

### 5. Verdict

- **SHIP**: All requirements verified → report success
- **NEEDS_WORK**: Gaps found → list gaps with fix suggestions

### 6. Fix loop (if NEEDS_WORK)

For each gap:
- If small (< 20 lines): fix directly, commit
- If larger: create new task via `$CCFLOW task create --epic $EPIC_ID --title "Fix: ..."`
- Re-verify after all fixes
- Repeat until SHIP

### 7. Record

```bash
$CCFLOW task comment $EPIC_ID --text "Epic review: SHIP"
```
