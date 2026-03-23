---
name: cc-prompt-engineering
description: >
  LLM prompt design patterns — chain-of-thought, few-shot, structured output,
  cost optimization. Use when building AI features, writing system prompts,
  or optimizing LLM interactions.
  TRIGGER: 'write a prompt', 'optimize prompt', 'LLM integration', 'AI feature',
  'system prompt', 'chain of thought', '写提示词', '优化prompt', '提示工程'.
  NOT FOR: using Claude Code itself — this is for building LLM-powered features.
---

# Prompt Engineering Patterns

## Design Framework

### 1. Define the Task

Before writing a prompt, answer:
- **Input**: What does the LLM receive?
- **Output**: What exact format do you need?
- **Constraints**: Length, tone, language, forbidden content?
- **Evaluation**: How will you measure quality?

### 2. Choose the Pattern

| Pattern | When | Example |
|---------|------|---------|
| **Zero-shot** | Simple, well-defined task | "Translate to French: {text}" |
| **Few-shot** | Need format consistency | 3-5 examples → then task |
| **Chain-of-thought** | Reasoning required | "Think step by step" |
| **Structured output** | Machine-parseable result | JSON schema in prompt |
| **Role-based** | Domain expertise needed | "You are a senior Python developer" |

### 3. Chain-of-Thought (CoT)

```python
prompt = """Analyze this code for security issues.

Think step by step:
1. Identify all user inputs
2. Trace each input through the code
3. Check if inputs are validated before use
4. Check if inputs reach dangerous operations (SQL, shell, file I/O)
5. List each vulnerability found with severity

Code:
{code}
"""
```

### 4. Few-Shot Learning

```python
prompt = """Convert Python functions to docstrings.

Example 1:
Input: def add(a: int, b: int) -> int: return a + b
Output: \"\"\"Add two integers and return the result.\"\"\"

Example 2:
Input: def is_valid_email(email: str) -> bool: return "@" in email and "." in email
Output: \"\"\"Check if an email address contains @ and . characters.\"\"\"

Now convert:
Input: {function_code}
Output:"""
```

### 5. Structured Output

```python
from pydantic import BaseModel

class CodeReview(BaseModel):
    issues: list[Issue]
    summary: str
    verdict: Literal["approve", "request_changes"]

class Issue(BaseModel):
    severity: Literal["critical", "high", "medium", "low"]
    file: str
    line: int
    description: str
    fix: str

# In prompt:
prompt = f"""Review this code and respond in this exact JSON format:
{CodeReview.model_json_schema()}

Code: {code}"""
```

### 6. System Prompt Design

```python
system_prompt = """You are a Python security auditor.

## Rules
- Focus ONLY on security issues, not style
- Rate each issue: CRITICAL / HIGH / MEDIUM / LOW
- Include file path and line number for each issue
- Suggest a specific fix (not just "validate input")
- If no issues found, say "No security issues detected"

## Output Format
Return a JSON array of issues. Each issue has: severity, file, line, description, fix.
"""
```

## Cost Optimization

| Strategy | Savings | Trade-off |
|----------|---------|-----------|
| Use smaller model for simple tasks | 10-50x | Lower quality on complex tasks |
| Cache identical prompts | 50-90% | Stale results |
| Batch similar requests | 20-40% | Latency increase |
| Shorten prompts (remove fluff) | 10-30% | May lose context |
| Use structured output (less parsing) | 5-15% | More rigid |

```python
# Model routing by complexity
def choose_model(task_complexity: float) -> str:
    if task_complexity < 0.3:
        return "haiku"       # Simple: format, classify, extract
    elif task_complexity < 0.7:
        return "sonnet"      # Medium: summarize, translate, review
    else:
        return "opus"        # Complex: reason, plan, architect
```

## Evaluation

```python
# Simple accuracy check
def evaluate_prompt(prompt_template, test_cases, model):
    results = []
    for case in test_cases:
        response = call_llm(model, prompt_template.format(**case["input"]))
        score = case["evaluator"](response, case["expected"])
        results.append(score)
    return sum(results) / len(results)
```

## Anti-Patterns

| Bad | Good |
|-----|------|
| "Be helpful and thorough" | Specific task + format + constraints |
| One giant prompt for everything | Decompose into focused sub-prompts |
| No examples | 2-3 diverse examples |
| "Don't make mistakes" | Define what correct looks like |
| Parsing free-text output | Structured JSON output |

## Pattern Selection Decision Tree

```
What's your task?
├─ Classification/extraction (structured) → Structured output + zero-shot
├─ Format-sensitive output → Few-shot (3-5 examples)
├─ Reasoning/analysis required?
│   ├─ Simple reasoning → Chain-of-thought
│   └─ Complex multi-step → CoT + decomposition into sub-prompts
├─ Domain expertise needed → Role-based + few-shot
└─ Not sure → Start with zero-shot, add complexity only if quality is low
```

## E2E Example: Improving a Prompt

**Before (bad):**
```python
prompt = "Review this code and tell me if there are problems"
# Problems: vague output, no format, no focus area, no severity
```

**After (good):**
```python
system = """You are a Python security auditor. Return JSON only.

Output format: {"issues": [{"severity": "critical|high|medium", "line": N, "description": "...", "fix": "..."}]}

Rules:
- Focus on security issues only (not style)
- Include line numbers
- Suggest specific fixes (not "validate input")
- If clean, return {"issues": []}"""

prompt = f"Review this code:\n```python\n{code}\n```"
# Result: parseable JSON, focused scope, actionable fixes
```

**Evaluation:**
```python
test_cases = [
    {"input": {"code": "subprocess.run(user_input, shell=True)"}, "expected": "critical"},
    {"input": {"code": "x = 1 + 2"}, "expected": "empty"},
    {"input": {"code": "open(path).read()"}, "expected": "medium"},
]
score = evaluate_prompt(system + prompt, test_cases, "sonnet")
# Target: score >= 0.9 (90% of test cases correct)
```

## Related Skills

- **cc-fastapi** — integrating LLM calls into API endpoints
- **cc-error-handling** — handling LLM API failures, retries
- **cc-async-patterns** — concurrent LLM calls
- **cc-performance** — caching and batching strategies
