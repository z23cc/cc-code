You are executing a task autonomously using cc-code.

TASK_ID: {{TASK_ID}}
EPIC_ID: {{EPIC_ID}}
REVIEW_MODE: {{WORK_REVIEW}}
RECEIPT_PATH: {{RECEIPT_PATH}}

## Steps

1. Read task spec:
   ```bash
   cc-flow show {{TASK_ID}}
   ```

2. Start task:
   ```bash
   cc-flow start {{TASK_ID}}
   ```

3. Implement using TDD:
   - Write failing test
   - Write minimal code to pass
   - Refactor
   - Run verification: `cc-flow verify`

4. Commit:
   ```bash
   git add -A && git commit -m "feat(scope): implement task {{TASK_ID}}"
   ```

5. Mark done:
   ```bash
   cc-flow done {{TASK_ID}} --summary "Brief description of what was done"
   ```

6. Write receipt:
   ```bash
   cat > {{RECEIPT_PATH}} << 'RECEIPT_EOF'
   {"type":"impl_review","id":"{{TASK_ID}}","mode":"{{WORK_REVIEW}}","verdict":"SHIP","timestamp":"FILL_TIMESTAMP"}
   RECEIPT_EOF
   ```
   Replace FILL_TIMESTAMP with current UTC time.

## Constraints
- Do NOT modify files outside the task scope
- Run verification before committing
- Receipt MUST be written after successful completion
