"""
Optional Zerodha Kite Connect integration for Indian stock price history.

Kite Connect gives more reliable OHLCV data for NSE-listed stocks than
Yahoo Finance (which frequently rate-limits or blocks cloud-hosted IPs), but
it does NOT provide fundamentals (ROE, margins, growth, etc.) — those still
come from `yfinance`. This module is entirely optional: if Kite credentials
aren't configured, `scanner.py` falls back to Yahoo for price history too,
exactly as before.

Setup (see README.md for the full walkthrough):
  1. Subscribe to Kite Connect at https://developers.kite.trade (paid, ~Rs
     2000/month) and create an app to get an api_key + api_secret.
  2. Each trading day, generate a fresh access_token by running
     `python kite_login.py` — it opens/prints a login URL, you log in in
     your browser (Zerodha requires this manual step, it cannot be
     automated), and paste back the request_token it redirects you with.
  3. Set environment variables KITE_API_KEY and KITE_ACCESS_TOKEN (kite_login.py
     prints them for you to export, or writes them to a .env-style file).
"""

import os
import time
from pathlib import Path

import pandas as pd

INSTRUMENTS_CACHE_PATH = Path(__file__).parent / ".cache" / "kite_nse_instruments.csv"
INSTRUMENTS_CACHE_MAX_AGE_SECONDS = 24 * 60 * 60  # instrument tokens are stable; refresh daily

_client = None
_instrument_token_by_symbol = None


def is_configured() -> bool:
    return bool(os.environ.get("KITE_API_KEY") and os.environ.get("KITE_ACCESS_TOKEN"))


def get_client():
    """Returns a connected KiteConnect client, or None if not configured/available."""
    global _client
    if _client is not None:
        return _client
    if not is_configured():
        return None
    try:
        from kiteconnect import KiteConnect
    except ImportError:
        return None

    kite = KiteConnect(api_key=os.environ["KITE_API_KEY"])
    kite.set_access_token(os.environ["KITE_ACCESS_TOKEN"])
    _client = kite
    return _client


def _load_instrument_map(kite) -> dict:
    global _instrument_token_by_symbol
    if _instrument_token_by_symbol is not None:
        return _instrument_token_by_symbol

    if INSTRUMENTS_CACHE_PATH.exists():
        age = time.time() - INSTRUMENTS_CACHE_PATH.stat().st_mtime
        if age < INSTRUMENTS_CACHE_MAX_AGE_SECONDS:
            df = pd.read_csv(INSTRUMENTS_CACHE_PATH)
            _instrument_token_by_symbol = dict(zip(df["tradingsymbol"], df["instrument_token"]))
            return _instrument_token_by_symbol

    instruments = kite.instruments("NSE")
    df = pd.DataFrame(instruments)[["tradingsymbol", "instrument_token"]]
    INSTRUMENTS_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(INSTRUMENTS_CACHE_PATH, index=False)
    _instrument_token_by_symbol = dict(zip(df["tradingsymbol"], df["instrument_token"]))
    return _instrument_token_by_symbol


def fetch_history(ticker: str, days: int = 400) -> pd.DataFrame:
    """Fetch daily OHLCV history for a `SYMBOL.NS` ticker via Kite Connect.

    Returns a DataFrame shaped like yfinance's `Ticker.history()` output
    (Close/Open/High/Low/Volume columns, DatetimeIndex) so it's a drop-in
    replacement in scanner.py, or an empty DataFrame if unavailable.
    """
    kite = get_client()
    if kite is None:
        return pd.DataFrame()

    symbol = ticker.upper().removesuffix(".NS").removesuffix(".BO")

    try:
        token_map = _load_instrument_map(kite)
        token = token_map.get(symbol)
        if token is None:
            return pd.DataFrame()

        to_date = pd.Timestamp.now().date()
        from_date = to_date - pd.Timedelta(days=days)
        candles = kite.historical_data(token, from_date, to_date, interval="day")
        if not candles:
            return pd.DataFrame()

        df = pd.DataFrame(candles)
        df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
        df = df.set_index("date").rename(columns={
            "open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume",
        })
        return df[["Open", "High", "Low", "Close", "Volume"]]
    except Exception:
        return pd.DataFrame()
