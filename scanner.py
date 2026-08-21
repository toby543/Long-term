#!/usr/bin/env python3
"""
Long-term stock strategy scanner.

Combines a fundamental quality/value screen with a technical trend
confirmation screen to surface candidates suitable for long-term
(buy-and-hold) investing. See README.md for the strategy rationale.
"""

import argparse
import sys
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

    fundamental_score: float = 0.0
    technical_score: float = 0.0
    composite_score: float = 0.0
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
    try:
        tk = yf.Ticker(ticker)
        info = tk.info or {}
        hist = tk.history(period="1y", auto_adjust=True)

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


def score_fundamentals(m: StockMetrics) -> float:
    score = 0.0
    weight_total = 0.0

    def add(value, weight, good_fn):
        nonlocal score, weight_total
        weight_total += weight
        if value is not None and not (isinstance(value, float) and np.isnan(value)):
            score += weight * good_fn(value)

    add(m.roe, 20, lambda v: np.clip(v / 0.20, 0, 1))
    add(m.operating_margin, 15, lambda v: np.clip(v / 0.20, 0, 1))
    add(m.revenue_growth, 15, lambda v: np.clip(v / 0.15, 0, 1))
    add(m.earnings_growth, 15, lambda v: np.clip(v / 0.15, 0, 1))
    add(m.debt_to_equity, 10, lambda v: np.clip(1 - (v / 1.5), 0, 1))
    add(m.current_ratio, 5, lambda v: np.clip(v / 1.5, 0, 1))
    add(m.free_cash_flow, 10, lambda v: 1.0 if v > 0 else 0.0)
    add(m.peg_ratio, 10, lambda v: np.clip(1 - ((v - 1) / 2), 0, 1) if v > 0 else 0.3)

    return round((score / weight_total) * 100, 1) if weight_total else 0.0


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


def classify(fundamental_score: float, technical_score: float) -> str:
    composite = fundamental_score * 0.65 + technical_score * 0.35
    if fundamental_score >= 60 and technical_score >= 55:
        return "BUY"
    if fundamental_score >= 45 and technical_score >= 40:
        return "WATCH"
    return "AVOID"


def scan(tickers: list[str]) -> pd.DataFrame:
    try:
        benchmark_hist = yf.Ticker(BENCHMARK_TICKER).history(period="1y", auto_adjust=True)
    except Exception:
        benchmark_hist = None

    rows = []
    for t in tickers:
        m = fetch_metrics(t, benchmark_hist)
        if m.error:
            rows.append({
                "Ticker": t, "Fund.": None, "Tech.": None, "Score": None,
                "Verdict": f"ERROR: {m.error}",
                "P/E": None, "PEG": None, "ROE%": None, "RevGr%": None,
                "D/E": None, "RSI": None, "%OffHigh": None, "RS6m%": None,
            })
            continue

        m.fundamental_score = score_fundamentals(m)
        m.technical_score = score_technicals(m)
        m.composite_score = round(m.fundamental_score * 0.65 + m.technical_score * 0.35, 1)
        m.verdict = classify(m.fundamental_score, m.technical_score)

        rows.append({
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
        })

    df = pd.DataFrame(rows)
    if "Score" in df:
        df = df.sort_values(by="Score", ascending=False, na_position="last")
    return df.reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser(description="Long-term stock strategy scanner")
    parser.add_argument("--tickers", nargs="+", help="Ticker symbols to scan")
    parser.add_argument("--file", help="Path to a file with one ticker per line")
    parser.add_argument("--output", help="Path to write results as CSV")
    parser.add_argument("--buy-only", action="store_true", help="Only show BUY verdicts")
    args = parser.parse_args()

    tickers = []
    if args.tickers:
        tickers.extend(args.tickers)
    if args.file:
        with open(args.file) as f:
            tickers.extend(line.strip() for line in f if line.strip())
    if not tickers:
        tickers = DEFAULT_TICKERS

    tickers = [t.upper() for t in dict.fromkeys(tickers)]  # de-dupe, preserve order

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
