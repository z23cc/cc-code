---
description: "QA report only — test and document bugs without fixing. TRIGGER: 'qa report', 'just report bugs', 'test but dont fix', 'QA报告', '只报告不修'."
---

Activate the cc-qa-report skill for report-only QA testing (no source code modifications).

## Quick Usage

Generate a QA report:
```
/cc-qa-report test http://localhost:3000
```

Report on changed pages only:
```
/cc-qa-report check pages affected by my branch on http://localhost:3000
```

Report for a specific section:
```
/cc-qa-report test the admin dashboard at http://localhost:3000/admin
```
