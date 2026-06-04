"""In-process TTL cache for RAI query results.

Goal: reduce repeat Snowflake queries for the most-frequently-hit endpoints
without adding any new dependencies.

Usage:
    from webapp.backend.cache import ttl_cache, cache_bust

    @ttl_cache(ttl_seconds=300, namespace="geo")
    def observations_for_species(name: str):
        ...

    # After loading new observations from GBIF:
    cache_bust("geo")          # invalidate one namespace
    cache_bust()               # invalidate everything

Notes:
  * In-memory only — entries are lost on uvicorn reload. That's intentional
    for now (single-process dev server, no new deps).
  * Cache stores pandas DataFrames; we return shallow copies (`df.copy()`)
    so callers can mutate freely without poisoning the cache entry.
  * Thread-safe enough for FastAPI's default thread-pool — the dict ops we
    use are atomic in CPython.

DEMONS (see docs/DEMONS.md for the full inventory):

  1. UNBOUNDED CACHE: _STORE grows linearly with distinct (namespace, fn,
     args) tuples. Expired entries are never reclaimed without an explicit
     bust. Per-species or per-cell queries accumulate forever. Add LRU
     eviction or a periodic sweep before production deployment.

  2. THUNDERING HERD: On cache miss, N concurrent callers with the same
     key will all execute the wrapped function (intentional, to avoid
     blocking on slow queries). The trade-off is that N parallel RAI
     queries hit Snowflake. Acceptable for dev; add in-flight key
     coalescing (threading.Event) for production.

  3. df.copy() ON EVERY HIT: ~10-100ms for large frames; can rival the
     original query cost. Document immutability and remove the copy, or
     adopt pandas 2.x copy-on-write.

  4. LAYER INVERSION: This module lives in webapp/backend/ but is imported
     by kg/queries/*.py — inverts the natural dependency direction. The
     CLI usage `python -m kg.queries.co_occurrence` requires PYTHONPATH to
     include the webapp tree. Move to a neutral location (kg/cache.py or
     arq_common/) when convenient.
"""

from __future__ import annotations

import time
import threading
from functools import wraps
from typing import Callable, Any

# (namespace, fn_qualname, args_repr) -> {"value": Any, "expires_at": float}
_STORE: dict[tuple[str, str, str], dict[str, Any]] = {}
_LOCK = threading.RLock()

# Telemetry — read by /api/debug or just from Python for sanity checks.
_STATS = {"hits": 0, "misses": 0, "evictions": 0}


def _key(namespace: str, fn: Callable, args: tuple, kwargs: dict) -> tuple[str, str, str]:
    # Deterministic key. Args must be hashable-ish; repr is safe and stable
    # for the kinds of inputs we pass (str, int, float, lists of those).
    return (namespace, f"{fn.__module__}.{fn.__qualname__}", repr((args, sorted(kwargs.items()))))


def ttl_cache(ttl_seconds: int = 300, namespace: str = "default"):
    """Decorator that memoizes a function's return value for `ttl_seconds`.

    `namespace` groups related entries so they can be invalidated together
    (e.g. all observation-derived queries). Pick a namespace per data
    volatility class:
        "ref"   — reference data (taxonomy, features, keys): 3600s+
        "geo"   — observation/spatial: 300s
        "deriv" — co-occurrence, community, etc.: 300s
    """

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = _key(namespace, fn, args, kwargs)
            now = time.time()
            with _LOCK:
                entry = _STORE.get(key)
                if entry is not None and entry["expires_at"] > now:
                    _STATS["hits"] += 1
                    value = entry["value"]
                    # Return a shallow copy for DataFrames so callers can
                    # rename columns / mutate without polluting the cache.
                    if hasattr(value, "copy") and callable(value.copy):
                        return value.copy()
                    return value
                _STATS["misses"] += 1

            # Compute outside the lock — RAI queries can be slow and we
            # don't want to block other threads.
            # DEMON: No single-flight coalescing here. N concurrent callers
            # with the same key all fall through and each calls fn() in
            # parallel, sending N identical queries to Snowflake. Fine for
            # current single-developer load; revisit before production.
            value = fn(*args, **kwargs)

            with _LOCK:
                _STORE[key] = {"value": value, "expires_at": now + ttl_seconds}
            return value.copy() if hasattr(value, "copy") and callable(value.copy) else value

        wrapper.__wrapped__ = fn  # type: ignore[attr-defined]
        wrapper._cache_namespace = namespace  # type: ignore[attr-defined]
        return wrapper

    return decorator


def cache_bust(namespace: str | None = None) -> int:
    """Invalidate cache entries.

    Pass a namespace (e.g. "geo") to clear just that group, or None to wipe
    everything. Returns the number of entries removed.
    """
    with _LOCK:
        if namespace is None:
            removed = len(_STORE)
            _STORE.clear()
        else:
            to_remove = [k for k in _STORE if k[0] == namespace]
            for k in to_remove:
                del _STORE[k]
            removed = len(to_remove)
        _STATS["evictions"] += removed
    return removed


def cache_stats() -> dict[str, Any]:
    """Return cache telemetry for debugging."""
    with _LOCK:
        return {
            **_STATS,
            "entries": len(_STORE),
            "by_namespace": {
                ns: sum(1 for k in _STORE if k[0] == ns)
                for ns in {k[0] for k in _STORE}
            },
        }
