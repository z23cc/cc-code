You are reviewing an epic plan autonomously using cc-code.

EPIC_ID: {{EPIC_ID}}
REVIEW_MODE: {{PLAN_REVIEW}}
RECEIPT_PATH: {{RECEIPT_PATH}}

## Steps

1. Read epic spec:
   ```bash
   cc-flow show {{EPIC_ID}}
   ```

2. Review the plan:
   - Check completeness: all requirements covered?
   - Check feasibility: can this be built as described?
   - Check clarity: unambiguous specs?
   - Check architecture: sound design?
   - Check risks: identified and mitigated?
   - Check scope: appropriately bounded?
   - Check testability: verifiable acceptance criteria?

3. If issues found:
   - Fix the spec
   - Re-review until satisfied

4. Write receipt:
   ```bash
   cat > {{RECEIPT_PATH}} << 'RECEIPT_EOF'
   {"type":"plan_review","id":"{{EPIC_ID}}","mode":"{{PLAN_REVIEW}}","verdict":"SHIP","timestamp":"FILL_TIMESTAMP"}
   RECEIPT_EOF
   ```

## Constraints
- Do NOT start implementing — review only
- Fix spec issues in-place
- Receipt MUST be written after review passes
