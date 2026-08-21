#!/usr/bin/env python3
"""
Long-term stock strategy scanner.

Combines a fundamental quality/value screen with a technical trend
confirmation screen to surface candidates suitable for long-term
(buy-and-hold) investing. See README.md for the strategy rationale.
"""

import argparse
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf
from tabulate import tabulate

DEFAULT_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA",
    "COST", "V", "MA", "UNH", "JNJ", "PG",
]

BENCHMARK_TICKER = "SPY"
NIFTY_BENCHMARK_TICKER = "^CRSLDX"  # Nifty 500 Total Return-ish proxy index on NSE

# Yahoo Finance rate-limits aggressively, especially from shared hosting IPs
# (Streamlit Cloud, Render). Keep concurrency low, space requests out, and
# retry with backoff on 429s rather than hammering it with a big thread pool.
MAX_WORKERS = 4
MIN_REQUEST_INTERVAL = 0.5  # seconds between requests, enforced globally across workers
MAX_RETRIES = 4
RETRY_BASE_DELAY = 3.0  # seconds; backs off 3s, 6s, 12s, 24s (+ jitter)

_rate_limit_lock = threading.Lock()
_last_request_time = 0.0


def _throttle():
    """Enforce a minimum gap between outgoing yfinance requests across all threads."""
    global _last_request_time
    with _rate_limit_lock:
        now = time.monotonic()
        wait = MIN_REQUEST_INTERVAL - (now - _last_request_time)
        if wait > 0:
            time.sleep(wait)
        _last_request_time = time.monotonic()


def _is_rate_limit_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "429" in msg or "too many requests" in msg or "rate limit" in msg


@dataclass
class StockMetrics:
    ticker: str
    error: Optional[str] = None

    # Fundamentals
    roe: Optional[float] = None
    operating_margin: Optional[float] = None
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    free_cash_flow: Optional[float] = None
    pe_ratio: Optional[float] = None
    peg_ratio: Optional[float] = None

    # Technicals
    price: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    rsi_14: Optional[float] = None
    pct_off_52w_high: Optional[float] = None
    relative_strength_6m: Optional[float] = None
    volume_trend: Optional[float] = None

    fundamental_score: Optional[float] = None
    technical_score: float = 0.0
    composite_score: Optional[float] = None
    verdict: str = "N/A"


def _safe_get(info: dict, *keys, default=None):
    for key in keys:
        val = info.get(key)
        if val is not None:
            return val
    return default


def compute_rsi(series: pd.Series, period: int = 14) -> float:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1]) if not rsi.empty and not np.isnan(rsi.iloc[-1]) else np.nan


def fetch_metrics(ticker: str, benchmark_hist: pd.DataFrame) -> StockMetrics:
    m = StockMetrics(ticker=ticker)

    for attempt in range(MAX_RETRIES + 1):
        try:
            _throttle()
            tk = yf.Ticker(ticker)
            info = tk.info or {}
            if len(info) < 5:
                # `.info` can silently come back near-empty (no exception) when
                # Yahoo's quoteSummary endpoint gates a request — e.g. from a
                # datacenter/cloud IP. get_info() forces a fresh, uncached
                # fetch and occasionally succeeds where the cached property
                # didn't.
                try:
                    info = tk.get_info() or info
                except Exception:
                    pass
            hist = tk.history(period="1y", auto_adjust=True)
            break
        except Exception as exc:
            if _is_rate_limit_error(exc) and attempt < MAX_RETRIES:
                delay = RETRY_BASE_DELAY * (2 ** attempt) + random.uniform(0, 1.5)
                time.sleep(delay)
                continue
            m.error = "Rate limited by Yahoo Finance — try again shortly or scan fewer tickers" \
                if _is_rate_limit_error(exc) else str(exc)
            return m

    try:
        if hist.empty:
            m.error = "No price history"
            return m

        # ---- Fundamentals ----
        m.roe = _safe_get(info, "returnOnEquity")
        m.operating_margin = _safe_get(info, "operatingMargins")
        m.revenue_growth = _safe_get(info, "revenueGrowth")
        m.earnings_growth = _safe_get(info, "earningsGrowth", "earningsQuarterlyGrowth")
        m.debt_to_equity = _safe_get(info, "debtToEquity")
        if m.debt_to_equity is not None:
            m.debt_to_equity = m.debt_to_equity / 100.0  # yfinance reports as %
        m.current_ratio = _safe_get(info, "currentRatio")
        m.free_cash_flow = _safe_get(info, "freeCashflow")
        m.pe_ratio = _safe_get(info, "trailingPE", "forwardPE")

        peg = _safe_get(info, "pegRatio")
        if peg is None and m.pe_ratio and m.earnings_growth and m.earnings_growth > 0:
            peg = m.pe_ratio / (m.earnings_growth * 100)
        m.peg_ratio = peg

        # ---- Technicals ----
        close = hist["Close"]
        m.price = float(close.iloc[-1])
        m.sma_50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None
        m.sma_200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None
        m.rsi_14 = compute_rsi(close, 14)

        high_52w = float(close.max())
        m.pct_off_52w_high = (m.price - high_52w) / high_52w * 100.0

        if benchmark_hist is not None and not benchmark_hist.empty and len(close) >= 126:
            stock_ret_6m = close.iloc[-1] / close.iloc[-126] - 1
            bench_close = benchmark_hist["Close"]
            if len(bench_close) >= 126:
                bench_ret_6m = bench_close.iloc[-1] / bench_close.iloc[-126] - 1
                m.relative_strength_6m = (stock_ret_6m - bench_ret_6m) * 100.0

        if "Volume" in hist and len(hist) >= 50:
            vol = hist["Volume"]
            recent_avg = vol.tail(20).mean()
            longer_avg = vol.tail(50).mean()
            if longer_avg > 0:
                m.volume_trend = (recent_avg / longer_avg - 1) * 100.0

    except Exception as exc:  # yfinance/network hiccups shouldn't kill the whole scan
        m.error = str(exc)

    return m


def score_fundamentals(m: StockMetrics) -> Optional[float]:
    """Returns a 0-100 score, or None if Yahoo returned no usable fundamental data at all.

    None is distinct from a legitimately bad (near-0) score: it means "we
    can't assess this," not "this fails every metric" — those must not be
    treated the same when classifying a verdict.
    """
    score = 0.0
    weight_total = 0.0

    def add(value, weight, good_fn):
        nonlocal score, weight_total
        # Only count a metric's weight if we actually have data for it —
        # a missing field (common with Yahoo's sparse/rate-limited `.info`)
        # must not be scored as if the company failed that metric.
        if value is not None and not (isinstance(value, float) and np.isnan(value)):
            weight_total += weight
            score += weight * good_fn(value)

    add(m.roe, 20, lambda v: np.clip(v / 0.20, 0, 1))
    add(m.operating_margin, 15, lambda v: np.clip(v / 0.20, 0, 1))
    add(m.revenue_growth, 15, lambda v: np.clip(v / 0.15, 0, 1))
    add(m.earnings_growth, 15, lambda v: np.clip(v / 0.15, 0, 1))
    add(m.debt_to_equity, 10, lambda v: np.clip(1 - (v / 1.5), 0, 1))
    add(m.current_ratio, 5, lambda v: np.clip(v / 1.5, 0, 1))
    add(m.free_cash_flow, 10, lambda v: 1.0 if v > 0 else 0.0)
    add(m.peg_ratio, 10, lambda v: np.clip(1 - ((v - 1) / 2), 0, 1) if v > 0 else 0.3)

    return round((score / weight_total) * 100, 1) if weight_total else None


def score_technicals(m: StockMetrics) -> float:
    score = 0.0
    weight_total = 0.0

    def add(condition_score, weight):
        nonlocal score, weight_total
        weight_total += weight
        if condition_score is not None:
            score += weight * condition_score

    if m.price is not None and m.sma_200 is not None:
        add(1.0 if m.price > m.sma_200 else 0.0, 25)
    if m.sma_50 is not None and m.sma_200 is not None:
        add(1.0 if m.sma_50 > m.sma_200 else 0.0, 20)
    if m.rsi_14 is not None and not np.isnan(m.rsi_14):
        # Best score in the 40-65 "healthy" band, tapering off outside it.
        if 40 <= m.rsi_14 <= 65:
            rsi_score = 1.0
        elif m.rsi_14 < 40:
            rsi_score = np.clip(m.rsi_14 / 40, 0, 1)
        else:
            rsi_score = np.clip(1 - (m.rsi_14 - 65) / 35, 0, 1)
        add(rsi_score, 20)
    if m.pct_off_52w_high is not None:
        # Sweet spot: within 20% of the high (not stretched, not broken down).
        add(np.clip(1 - abs(m.pct_off_52w_high + 10) / 40, 0, 1), 15)
    if m.relative_strength_6m is not None:
        add(np.clip(0.5 + m.relative_strength_6m / 40, 0, 1), 15)
    if m.volume_trend is not None:
        add(np.clip(0.5 + m.volume_trend / 100, 0, 1), 5)

    return round((score / weight_total) * 100, 1) if weight_total else 0.0


def classify(fundamental_score: Optional[float], technical_score: float) -> str:
    if fundamental_score is None:
        # Yahoo gave us no fundamental data to assess at all (common from
        # cloud-hosted IPs) — say so rather than defaulting to AVOID, which
        # would misrepresent "unknown" as "bad".
        return "NO DATA"
    if fundamental_score >= 60 and technical_score >= 55:
        return "BUY"
    if fundamental_score >= 45 and technical_score >= 40:
        return "WATCH"
    return "AVOID"


def _row_for(m: StockMetrics) -> dict:
    if m.error:
        return {
            "Ticker": m.ticker, "Fund.": None, "Tech.": None, "Score": None,
            "Verdict": f"ERROR: {m.error}",
            "P/E": None, "PEG": None, "ROE%": None, "RevGr%": None,
            "D/E": None, "RSI": None, "%OffHigh": None, "RS6m%": None,
        }

    m.fundamental_score = score_fundamentals(m)
    m.technical_score = score_technicals(m)
    m.composite_score = (
        round(m.fundamental_score * 0.65 + m.technical_score * 0.35, 1)
        if m.fundamental_score is not None
        else None  # can't compute a meaningful composite without any fundamentals
    )
    m.verdict = classify(m.fundamental_score, m.technical_score)

    return {
        "Ticker": m.ticker,
        "Fund.": m.fundamental_score,
        "Tech.": m.technical_score,
        "Score": m.composite_score,
        "Verdict": m.verdict,
        "P/E": round(m.pe_ratio, 1) if m.pe_ratio else None,
        "PEG": round(m.peg_ratio, 2) if m.peg_ratio else None,
        "ROE%": round(m.roe * 100, 1) if m.roe else None,
        "RevGr%": round(m.revenue_growth * 100, 1) if m.revenue_growth else None,
        "D/E": round(m.debt_to_equity, 2) if m.debt_to_equity else None,
        "RSI": round(m.rsi_14, 1) if m.rsi_14 and not np.isnan(m.rsi_14) else None,
        "%OffHigh": round(m.pct_off_52w_high, 1) if m.pct_off_52w_high is not None else None,
        "RS6m%": round(m.relative_strength_6m, 1) if m.relative_strength_6m is not None else None,
    }


def scan(tickers: list[str], max_workers: int = MAX_WORKERS) -> pd.DataFrame:
    # Indices outside the US need their own benchmark for relative-strength
    # scoring — an Indian stock's return vs. SPY isn't a meaningful signal.
    is_indian = any(t.upper().endswith((".NS", ".BO")) for t in tickers)
    benchmark_ticker = NIFTY_BENCHMARK_TICKER if is_indian else BENCHMARK_TICKER

    benchmark_hist = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            _throttle()
            benchmark_hist = yf.Ticker(benchmark_ticker).history(period="1y", auto_adjust=True)
            break
        except Exception as exc:
            if _is_rate_limit_error(exc) and attempt < MAX_RETRIES:
                time.sleep(RETRY_BASE_DELAY * (2 ** attempt) + random.uniform(0, 1.5))
                continue
            break  # non-rate-limit error, or retries exhausted — proceed without a benchmark

    rows = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(fetch_metrics, t, benchmark_hist): t for t in tickers}
        for future in as_completed(futures):
            rows.append(_row_for(future.result()))

    df = pd.DataFrame(rows)
    if "Score" in df:
        df = df.sort_values(by="Score", ascending=False, na_position="last")
    return df.reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser(description="Long-term stock strategy scanner")
    parser.add_argument("--tickers", nargs="+", help="Ticker symbols to scan")
    parser.add_argument("--file", help="Path to a file with one ticker per line")
    parser.add_argument(
        "--index", choices=["nifty500"],
        help="Scan a whole index instead of (or in addition to) --tickers/--file",
    )
    parser.add_argument("--limit", type=int, help="Cap the number of tickers scanned (useful with --index)")
    parser.add_argument("--output", help="Path to write results as CSV")
    parser.add_argument("--buy-only", action="store_true", help="Only show BUY verdicts")
    args = parser.parse_args()

    tickers = []
    if args.tickers:
        tickers.extend(args.tickers)
    if args.file:
        with open(args.file) as f:
            tickers.extend(line.strip() for line in f if line.strip())
    if args.index == "nifty500":
        from indices import get_nifty500_tickers
        try:
            tickers.extend(get_nifty500_tickers())
        except Exception as exc:
            print(f"Failed to load Nifty 500 constituents: {exc}", file=sys.stderr)
            return 1
    if not tickers:
        tickers = DEFAULT_TICKERS

    tickers = [t.upper() for t in dict.fromkeys(tickers)]  # de-dupe, preserve order
    if args.limit:
        tickers = tickers[: args.limit]

    print(f"Scanning {len(tickers)} ticker(s): {', '.join(tickers)}\n")
    df = scan(tickers)

    if args.buy_only:
        df = df[df["Verdict"] == "BUY"]

    if df.empty:
        print("No results.")
        return

    print(tabulate(df, headers="keys", tablefmt="github", showindex=False))

    if args.output:
        df.to_csv(args.output, index=False)
        print(f"\nSaved results to {args.output}")


if __name__ == "__main__":
    sys.exit(main())
