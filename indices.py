"""
Index constituent lookups.

NSE (India) does not publish a stable, versioned API for index constituents,
so the Nifty 500 list is fetched live from NSE's own archive CSV and cached
locally for a while, rather than hardcoded — hardcoding 500 tickers would go
stale as the index is periodically reconstituted.
"""

import csv
import io
import time
from pathlib import Path

import requests

NIFTY500_CSV_URL = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
CACHE_PATH = Path(__file__).parent / ".cache" / "nifty500.csv"
CACHE_MAX_AGE_SECONDS = 7 * 24 * 60 * 60  # 1 week

_NSE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/csv,application/csv,*/*",
}


def _fetch_live() -> list[str]:
    # NSE requires a warmed-up session (cookies from the main site) before
    # its archive endpoints will respond to non-browser clients.
    session = requests.Session()
    session.headers.update(_NSE_HEADERS)
    session.get("https://www.nseindia.com", timeout=10)
    resp = session.get(NIFTY500_CSV_URL, timeout=15)
    resp.raise_for_status()

    reader = csv.DictReader(io.StringIO(resp.text))
    symbols = [row["Symbol"].strip() for row in reader if row.get("Symbol")]
    if not symbols:
        raise ValueError("NSE returned no symbols — unexpected CSV format")
    return [f"{s}.NS" for s in symbols]


def _read_cache() -> list[str] | None:
    if not CACHE_PATH.exists():
        return None
    age = time.time() - CACHE_PATH.stat().st_mtime
    if age > CACHE_MAX_AGE_SECONDS:
        return None
    tickers = [line.strip() for line in CACHE_PATH.read_text().splitlines() if line.strip()]
    return tickers or None


def _write_cache(tickers: list[str]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text("\n".join(tickers) + "\n")


def get_nifty500_tickers(force_refresh: bool = False) -> list[str]:
    """Return Nifty 500 constituent tickers as yfinance-compatible symbols (SYMBOL.NS).

    Tries a fresh fetch from NSE first; falls back to a local cache (up to
    CACHE_MAX_AGE_SECONDS old) if the live fetch fails, so a transient NSE
    outage doesn't break the scanner.
    """
    if not force_refresh:
        cached = _read_cache()
        if cached:
            return cached

    try:
        tickers = _fetch_live()
        _write_cache(tickers)
        return tickers
    except Exception as exc:
        cached = _read_cache()
        if cached:
            return cached
        raise RuntimeError(
            f"Could not fetch Nifty 500 list from NSE and no cache is available: {exc}"
        ) from exc
