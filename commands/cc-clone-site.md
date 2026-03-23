---
name: cc-clone-site
description: "Replicate a reference website — screenshot, analyze, implement, QA compare."
---

Clone a reference site. Pass the target URL as argument.

```bash
TARGET_URL="${1:?Provide target URL}"

echo "Cloning: $TARGET_URL"
echo "Phase 1: Capturing reference screenshots..."
echo "Phase 2: Analyzing design tokens and structure..."
echo "Phase 3: Creating implementation plan..."
echo "Phase 4: Implementing components..."
echo "Phase 5: QA comparing against reference..."
```

Activate the cc-clone-site skill for the full workflow.

## Usage

- `/cc-clone-site https://example.com` — full clone workflow
- `/cc-clone-site https://example.com/pricing` — clone a specific page
