You are verifying epic completion autonomously using cc-code.

EPIC_ID: {{EPIC_ID}}
REVIEW_MODE: {{COMPLETION_REVIEW}}
RECEIPT_PATH: {{RECEIPT_PATH}}

## Steps

1. Read epic spec and all task summaries:
   ```bash
   python3 scripts/cc-flow.py show {{EPIC_ID}}
   python3 scripts/cc-flow.py progress --epic {{EPIC_ID}}
   ```

2. Verify each requirement in the spec is fully implemented:
   - Read the implementation code
   - Read the tests
   - Mark each requirement: DONE / PARTIAL / MISSING

3. If gaps found:
   - Implement missing requirements
   - Run verification: `python3 scripts/cc-flow.py verify`
   - Commit fixes
   - Re-verify

4. Write receipt:
   ```bash
   cat > {{RECEIPT_PATH}} << 'RECEIPT_EOF'
   {"type":"completion_review","id":"{{EPIC_ID}}","mode":"{{COMPLETION_REVIEW}}","verdict":"SHIP","timestamp":"FILL_TIMESTAMP"}
   RECEIPT_EOF
   ```

## Constraints
- Verify ALL requirements from the spec, not just code quality
- Fix any gaps before writing receipt
- Receipt MUST be written only after ALL requirements verified
