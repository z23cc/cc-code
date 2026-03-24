---
description: "One command full automation — describe your goal, everything runs. TRIGGER: 'go', 'just do it', 'automate', 'do everything', '全自动', '一键执行'"
---

Run `cc-flow go` with the user's goal to determine the best execution strategy.

```bash
cc-flow go "<user's goal>" --dry-run
```

Review the output (mode, chain, steps). If the user confirms, execute without --dry-run:

```bash
cc-flow go "<user's goal>"
```

Follow the output instructions — chain mode gives step-by-step skills to execute, ralph mode launches autonomous execution, auto mode runs the improvement loop.
