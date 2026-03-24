---
name: cc-elicit
description: >
  Apply structured reasoning methods to challenge and deepen any design or decision.
  8 methods: pre-mortem, first principles, inversion, red team, Socratic,
  constraint removal, stakeholder mapping, analogical reasoning.
  TRIGGER: 'think deeper', 'challenge this', 'elicit', 'reasoning', 'pre-mortem',
  'first principles', 'what could go wrong', 'red team', '深入思考', '挑战', '预检'.
  NOT FOR: brainstorming from scratch — use cc-brainstorming.
  FLOWS INTO: cc-plan (refined decisions), cc-architecture (validated ADRs).
---

# Advanced Elicitation — Structured Reasoning Methods

Apply structured thinking methods to challenge assumptions, find blind spots, and strengthen decisions. Use on any design doc, ADR, plan, or decision.

## Methods

### 1. Pre-Mortem Analysis
**When:** Before committing to a plan
**How:** "It's 6 months from now and this project failed. Why?"
- List 5+ specific failure modes
- For each: probability (high/medium/low) + mitigation
- Identify the #1 most likely failure

### 2. First Principles Thinking
**When:** Complex problem with many assumptions
**How:** Strip away all assumptions. What are the fundamental truths?
- List all current assumptions
- For each: is this a fact or convention?
- Rebuild the solution from only the facts

### 3. Inversion (Work Backward from Failure)
**When:** Designing safety-critical systems
**How:** "How would I guarantee this system fails?"
- List all ways to break it
- For each: add a guard that prevents it
- The guards become your requirements

### 4. Red Team / Blue Team
**When:** Security, resilience, competitive analysis
**How:** Red team attacks, blue team defends
- Red: find 5 attack vectors / failure modes / competitive threats
- Blue: for each, propose a defense
- Evaluate: are the defenses sufficient?

### 5. Socratic Questioning
**When:** Vague requirements or uncertain decisions
**How:** Chain of "why" and "what if" questions
- Why this approach over alternatives?
- What evidence supports this?
- What would change your mind?
- What's the strongest argument against this?

### 6. Constraint Removal
**When:** Feeling stuck or limited
**How:** "If we had unlimited time/money/people, what would we build?"
- Remove each constraint one at a time
- Note which removals unlock the biggest improvements
- Find creative ways to approximate those improvements within constraints

### 7. Stakeholder Mapping
**When:** Multi-user or multi-team features
**How:** Map every affected party
- Who uses this? Who maintains this? Who pays for this?
- What does each stakeholder need? Fear? Value?
- Where do stakeholder needs conflict?

### 8. Analogical Reasoning
**When:** Novel problem with no precedent
**How:** Find similar problems in other domains
- "What's the [X] of [our domain]?" (e.g., "What's the Uber of package delivery?")
- What worked in the analogy? What failed?
- What transfers and what doesn't?

## Usage

### Auto-Suggest Mode
Based on the input content, suggest the 3 most relevant methods:

| Content Type | Suggested Methods |
|-------------|-------------------|
| New feature design | Pre-mortem, First principles, Stakeholder mapping |
| Architecture decision | Inversion, Red team, Constraint removal |
| Bug root cause | First principles, Inversion, Socratic |
| Security design | Red team, Inversion, Pre-mortem |
| Performance optimization | Constraint removal, Analogical, First principles |
| Team disagreement | Socratic, Stakeholder mapping, Red team |

### Process
1. Read the input (design doc, ADR, plan, or decision)
2. Auto-suggest 3 relevant methods based on content type
3. Ask user which method(s) to apply (or apply all suggested)
4. Execute the chosen method(s)
5. Output refined insights and recommendations

## Output Format

```markdown
## Elicitation: [Method Name]

### Input
[What we're analyzing]

### Findings
1. [Insight]
2. [Insight]
3. [Insight]

### Recommendations
- [Action item]
- [Action item]

### Risk Level Change
Before: [assessment]
After: [assessment]
```

## On Completion

```bash
cc-flow skill ctx save cc-elicit --data '{"methods_used": ["pre-mortem", "inversion"], "findings": 5, "risk_change": "medium→low"}'
cc-flow skill next
```

## Related Skills

- **cc-grill-me** — adversarial questioning (subset of these methods)
- **cc-brainstorming** — generates the designs this skill challenges
- **cc-architecture** — ADRs benefit from pre-mortem and inversion
- **cc-requirement-gate** — requirements benefit from Socratic questioning
