"""
TTL cache for scan() results, keyed by ticker.

Re-scanning the same tickers within a short window (typical while using the
web UI — retrying a scan, toggling "Show BUY only", tweaking the ticker
list) previously re-fetched everything from Yahoo/Kite every time. This
caches each ticker's computed result row for a while so repeat scans reuse
it instead of re-hitting the network.

The whole cache is a single JSON file, loaded once and saved once per
scan() call (not per ticker) to avoid O(n) file I/O under the thread pool.
"""

import json
import time
from pathlib import Path

CACHE_PATH = Path(__file__).parent / ".cache" / "scan_results.json"
DEFAULT_TTL_SECONDS = 15 * 60  # 15 minutes: long enough to help iterative use,
                                 # short enough that prices don't go stale


def load() -> dict:
    if not CACHE_PATH.exists():
        return {}
    try:
        return json.loads(CACHE_PATH.read_text())
    except Exception:
        return {}


def save(cache: dict) -> None:
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(json.dumps(cache))
    except Exception:
        pass  # caching is a best-effort optimization, never fatal


def get_fresh_rows(tickers: list[str], cache: dict, ttl: int = DEFAULT_TTL_SECONDS) -> dict:
    """Returns {ticker: row} for tickers with a cache entry newer than ttl seconds."""
    now = time.time()
    fresh = {}
    for t in tickers:
        entry = cache.get(t)
        if entry and now - entry.get("ts", 0) <= ttl:
            fresh[t] = entry["row"]
    return fresh


def update(cache: dict, rows_by_ticker: dict) -> None:
    now = time.time()
    for ticker, row in rows_by_ticker.items():
        cache[ticker] = {"ts": now, "row": row}
