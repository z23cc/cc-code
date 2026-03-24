"""cc-flow AI router — use an LLM to select the best chain and complexity.

Replaces keyword matching with AI intent analysis for higher accuracy.
Uses the fastest available engine (gemini > claude) for routing decisions.
Results are cached to avoid redundant API calls.
"""

import hashlib
import json
import shutil
import subprocess
import time

from cc_flow.core import TASKS_DIR

# ── Cache ──

CACHE_DIR = TASKS_DIR / "route_cache"


def _cache_key(query):
    """Deterministic cache key from query."""
    normalized = " ".join(query.lower().split())
    return hashlib.md5(normalized.encode(), usedforsecurity=False).hexdigest()[:12]


def _cache_lookup(query):
    """Look up cached routing result. Returns dict or None."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = _cache_key(query)
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        try:
            data = json.loads(cache_file.read_text())
            # Cache valid for 24 hours
            age = time.time() - data.get("cached_at", 0)
            if age < 86400:
                return data.get("result")
        except (json.JSONDecodeError, OSError):
            pass
    return None


def _cache_save(query, result):
    """Save routing result to cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = _cache_key(query)
    cache_file = CACHE_DIR / f"{key}.json"
    try:
        cache_file.write_text(json.dumps({
            "query": query,
            "cached_at": time.time(),
            "result": result,
        }, ensure_ascii=False) + "\n")
    except OSError:
        pass


# ── Chain list builder ──

def _get_chain_summary():
    """Build a concise chain catalog for the AI router."""
    try:
        from cc_flow.skill_chains import SKILL_CHAINS
        lines = []
        for name, chain in SKILL_CHAINS.items():
            desc = chain.get("description", "")
            steps = len(chain.get("skills", []))
            lines.append(f"- {name} ({steps} steps): {desc}")
        return "\n".join(lines)
    except ImportError:
        return ""


def _get_command_summary():
    """Build standalone command catalog (skills not in any chain)."""
    commands = [
        ("review", "Code review — auto 3-engine debate"),
        ("autopilot", "3-engine guided autonomous execution"),
        ("multi-plan", "3-engine collaborative planning"),
        ("prime", "Run all 12 scouts in parallel (project health)"),
        ("audit", "8-pillar readiness assessment"),
        ("interview", "Structured requirements interview"),
        ("scout", "Run specific scout: practices/repo/security/testing/docs/etc"),
        ("research", "Deep codebase investigation"),
        ("retro", "Weekly engineering retrospective"),
        ("verify", "Run lint + tests"),
        ("dashboard", "Project overview"),
        ("doctor", "Health check"),
        ("health", "Health score 0-100"),
    ]
    return "\n".join(f"- {name}: {desc}" for name, desc in commands)


# ── AI Router Prompt ──

ROUTER_PROMPT = """\
You are a routing agent. Given a user's goal, select the best workflow or command.

Available workflow chains (multi-step):
{chain_list}

Standalone commands (single action):
{command_list}

Special modes:
- autopilot: For complex cross-system tasks (redesign, rewrite, migrate). 3-engine guided execution.
- auto: For improvement/scan tasks (lint, quality, auto-fix)
- review: For code review requests. Auto-selects 3-engine debate.
- prime: For project health assessment. Runs all 12 scouts.

User's goal: "{query}"

Respond with ONLY a JSON object (no markdown, no explanation):
{{"chain": "<chain-name or command-name or autopilot or auto or review or prime>", "complexity": "<simple|medium|complex>", "reason": "<one sentence why>"}}"""


# ── Engine Execution ──

def _run_router(query, timeout=30):
    """Run the AI router using the fastest available engine."""
    chain_list = _get_chain_summary()
    command_list = _get_command_summary()
    prompt = ROUTER_PROMPT.format(chain_list=chain_list, command_list=command_list, query=query)

    # Try gemini first (fastest), then claude
    engines = []
    gemini = shutil.which("gemini") or shutil.which("gemini-cli")
    if gemini:
        engines.append(("gemini", [gemini, "-p", prompt]))
    if shutil.which("claude"):
        engines.append(("claude", ["claude", "-p", "--output-format", "text", prompt]))

    for engine_name, cmd in engines:
        try:
            r = subprocess.run(
                cmd, check=False, capture_output=True, text=True, timeout=timeout,
            )
            output = r.stdout.strip()
            # Extract JSON from output (might have noise)
            result = _parse_router_response(output)
            if result:
                result["router_engine"] = engine_name
                return result
        except (subprocess.TimeoutExpired, OSError):
            continue

    return None


def _parse_router_response(text):
    """Parse the AI router's JSON response."""
    # Try direct JSON parse
    try:
        data = json.loads(text)
        if "chain" in data:
            return data
    except json.JSONDecodeError:
        pass

    # Extract JSON from markdown code blocks or mixed text
    import re
    json_match = re.search(r'\{[^{}]*"chain"[^{}]*\}', text)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    return None


# ── Public API ──

def ai_route(query, use_cache=True):
    """Route a query using AI analysis. Returns {chain, complexity, reason} or None.

    Falls back to None if AI routing fails (caller should use keyword fallback).
    """
    # Check cache first
    if use_cache:
        cached = _cache_lookup(query)
        if cached:
            cached["from_cache"] = True
            return cached

    # Run AI router
    result = _run_router(query)

    if result:
        # Validate chain exists
        try:
            from cc_flow.skill_chains import SKILL_CHAINS
            chain = result.get("chain", "")
            if chain not in SKILL_CHAINS and chain not in ("autopilot", "auto"):
                # AI hallucinated a chain name — try fuzzy match
                best_match = None
                best_score = 0
                for name in SKILL_CHAINS:
                    # Simple overlap score
                    score = len(set(chain.split("-")) & set(name.split("-")))
                    if score > best_score:
                        best_score = score
                        best_match = name
                if best_match and best_score > 0:
                    result["chain"] = best_match
                    result["chain_corrected"] = True
        except ImportError:
            pass

        # Save to cache
        if use_cache:
            _cache_save(query, result)

        result["from_cache"] = False
        return result

    return None
