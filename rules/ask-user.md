---
description: "Standardized format when asking user questions — re-ground context, recommend, one decision per question"
alwaysApply: true
---

# Ask User Format

When asking the user a question, follow this format:

## 1. Re-ground Context (assume user hasn't looked in 20 minutes)
- Current branch + what you're working on
- What just happened (1 sentence)

## 2. One Decision Per Question
- NEVER combine multiple decisions into one question
- Each decision gets its own focused question with recommendation

## 3. Recommend with Completeness Score
- Always recommend one option: "RECOMMENDATION: [X] because [reason]"
- Score each option: Completeness X/10 (10=full implementation, 7=happy path only, 3=shortcut)
- If both options are 8+, pick higher. If one is ≤5, flag it.

## 4. Show Dual Effort Estimate
- Human team time vs CC+gstack time
- Example: "A) Full implementation (human: ~2 days / CC: ~15 min)"

## 5. Keep It Simple
- Explain for a "smart 16-year-old" who isn't looking at the code
- If you'd need to read the source to understand your own explanation, simplify
