---
description: "QA test & fix — diff-aware page detection, health scoring, auto-fix loop. TRIGGER: 'qa', 'test the site', 'find bugs', 'test and fix', 'QA测试', '测试网站'."
---

Activate the cc-qa skill for systematic QA testing with automatic bug fixing.

## Quick Usage

Full QA on local dev server:
```
/cc-qa test http://localhost:3000
```

QA only pages affected by current branch:
```
/cc-qa test changed pages on http://localhost:3000
```

QA with a target health score:
```
/cc-qa test http://localhost:8080 and fix until health >= 95
```

QA a specific flow:
```
/cc-qa test the checkout flow on http://localhost:3000
```
