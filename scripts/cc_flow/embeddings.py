"""Embedding-based semantic search for tasks and learnings.

Uses Morph embedding API with local JSON cache to avoid re-embedding
unchanged content. Cache keyed by content hash (SHA-256).
"""

import hashlib
import json
import math

from cc_flow.core import TASKS_DIR, get_morph_client

EMBED_CACHE_FILE = TASKS_DIR / ".embed_cache.json"


def _content_hash(text):
    """SHA-256 hash of text content for cache key."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _load_cache():
    """Load embedding cache from disk."""
    if EMBED_CACHE_FILE.exists():
        try:
            return json.loads(EMBED_CACHE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_cache(cache):
    """Persist embedding cache to disk."""
    EMBED_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    EMBED_CACHE_FILE.write_text(json.dumps(cache) + "\n")


def cosine_similarity(a, b):
    """Cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def embed_texts(texts):
    """Embed a list of texts, using cache for unchanged content.

    Returns list of (text, vector) pairs, or None if Morph unavailable.
    """
    client = get_morph_client()
    if not client:
        return None

    cache = _load_cache()
    results = []
    to_embed = []  # (index, text) pairs that need API call
    indices = []

    for i, text in enumerate(texts):
        h = _content_hash(text)
        if h in cache:
            results.append((text, cache[h]))
        else:
            results.append((text, None))  # placeholder
            to_embed.append(text)
            indices.append(i)

    if to_embed:
        try:
            vectors = client.embed(to_embed)
            for j, vec in enumerate(vectors):
                idx = indices[j]
                results[idx] = (to_embed[j], vec)
                cache[_content_hash(to_embed[j])] = vec
            _save_cache(cache)
        except (RuntimeError, TimeoutError, OSError, json.JSONDecodeError, KeyError, ValueError):
            return None

    # Check all vectors were resolved
    if any(v is None for _, v in results):
        return None
    return results


def semantic_search(query, documents, top_n=5):
    """Search documents by semantic similarity to query.

    Args:
        query: search string
        documents: list of {"id": str, "text": str, ...} dicts
        top_n: max results to return

    Returns:
        List of {"id", "text", "score"} sorted by relevance, or None if unavailable.
    """
    if not documents:
        return []

    all_texts = [query] + [d["text"] for d in documents]
    embedded = embed_texts(all_texts)
    if not embedded:
        return None

    query_vec = embedded[0][1]
    scored = []
    for i, doc in enumerate(documents):
        doc_vec = embedded[i + 1][1]
        score = cosine_similarity(query_vec, doc_vec)
        scored.append({**doc, "score": round(score, 4)})

    scored.sort(key=lambda x: -x["score"])
    return scored[:top_n]
