#!/usr/bin/env python3
"""
Streamlit UI for the long-term stock strategy scanner.

Run with:
    streamlit run streamlit_app.py
"""

import math

import numpy as np
import pandas as pd
import streamlit as st

from scanner import DEFAULT_TICKERS, scan

st.set_page_config(page_title="Long-Term Stock Strategy Scanner", page_icon="📈", layout="wide")

VERDICT_COLORS = {"BUY": "#1f9d55", "WATCH": "#c99a2e", "AVOID": "#b3403a", "NO DATA": "#9aa0ab"}
VERDICT_ICONS = {"BUY": "🟢", "WATCH": "🟡", "AVOID": "🔴", "NO DATA": "⚪"}

st.markdown(
    """
    <style>
      .block-container { padding-top: 2rem; max-width: 1200px; }
      .hero {
        background: linear-gradient(135deg, #1a3a5c 0%, #0f1f33 100%);
        border-radius: 14px;
        padding: 1.75rem 2rem;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255,255,255,0.08);
      }
      .hero h1 { margin: 0 0 0.35rem 0; font-size: 1.7rem; }
      .hero p { margin: 0; opacity: 0.85; font-size: 0.95rem; }
      div[data-testid="stForm"] {
        background: rgba(127,127,127,0.05);
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        border: 1px solid rgba(127,127,127,0.15);
      }
      div[data-testid="stMetric"] {
        background: rgba(127,127,127,0.06);
        border-radius: 10px;
        padding: 0.75rem 1rem;
        border: 1px solid rgba(127,127,127,0.12);
      }
      .footnote { opacity: 0.6; font-size: 0.82rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>📈 Long-Term Stock Strategy Scanner</h1>
      <p>Fundamental quality/GARP screen (ROE, margins, growth, debt, FCF, PEG) +
      technical trend confirmation (SMA trend/slope, RSI, 52-week high, multi-timeframe
      relative strength) for long-term buy-and-hold candidates.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

source = st.radio(
    "Ticker source",
    ["Custom list", "Nifty 500 (India)"],
    horizontal=True,
)

with st.form("scan_form"):
    if source == "Custom list":
        tickers_input = st.text_area(
            "Tickers (comma or newline separated)",
            value=", ".join(DEFAULT_TICKERS),
            height=100,
        )
        limit = None
    else:
        st.caption(
            "Fetches the current Nifty 500 constituent list live from NSE "
            "(cached locally for a week). Scanning all 500 can take a few "
            "minutes — use the limit below to try a subset first."
        )
        tickers_input = None
        limit = st.slider("Limit (0 = all 500)", 0, 500, 50, step=10)

    col1, col2, col3 = st.columns(3)
    with col1:
        buy_only = st.checkbox("Show BUY only")
    with col2:
        force_refresh = st.checkbox("Force refresh", help="Bypass the 15-minute result cache and re-fetch everything")
    with col3:
        top_n = st.number_input("Top N (0 = all)", min_value=0, value=0, step=5)

    invest_amount = st.number_input(
        "Amount to invest per pick (optional — for the Qty column)",
        min_value=0.0, value=0.0, step=100.0,
        help="Same currency as the Price column (USD for US tickers, INR for .NS/.BO). "
             "Leave at 0 to skip the quantity calculation.",
    )

    submitted = st.form_submit_button("Scan", type="primary", use_container_width=True)

if submitted:
    if source == "Custom list":
        tickers = [
            t.strip().upper()
            for t in tickers_input.replace("\n", ",").split(",")
            if t.strip()
        ]
        tickers = list(dict.fromkeys(tickers))  # de-dupe, preserve order
    else:
        with st.spinner("Fetching Nifty 500 constituent list from NSE..."):
            try:
                from indices import get_nifty500_tickers
                tickers = get_nifty500_tickers()
            except Exception as exc:
                st.error(f"Could not load Nifty 500 list: {exc}")
                tickers = []
        if limit:
            tickers = tickers[:limit]

    if not tickers and source == "Custom list":
        st.error("Enter at least one ticker symbol.")
    elif tickers:
        with st.spinner(f"Scanning {len(tickers)} ticker(s)..."):
            try:
                df = scan(tickers, use_cache=not force_refresh)
            except Exception as exc:
                st.error(f"Scan failed: {exc}")
                df = None

        if df is not None:
            verdict_counts = df["Verdict"].value_counts()
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🟢 BUY", int(verdict_counts.get("BUY", 0)))
            m2.metric("🟡 WATCH", int(verdict_counts.get("WATCH", 0)))
            m3.metric("🔴 AVOID", int(verdict_counts.get("AVOID", 0)))
            m4.metric("Scanned", len(df))

            if buy_only:
                df = df[df["Verdict"] == "BUY"]

            if top_n:
                df = df.head(int(top_n))  # already sorted by Score descending

            if df.empty:
                st.info("No results to show.")
            else:
                if invest_amount > 0 and "EntryPrice" in df.columns:
                    df = df.copy()
                    df["Qty"] = df["EntryPrice"].apply(
                        lambda p: math.floor(invest_amount / p) if p and p > 0 else np.nan
                    )

                display_df = df.rename(columns={"EntryPrice": "Entry Price"})
                if "Verdict" in display_df.columns:
                    display_df["Verdict"] = display_df["Verdict"].apply(
                        lambda v: f"{VERDICT_ICONS.get(v, '')} {v}".strip()
                    )

                def highlight_verdict(row):
                    color = None
                    for label, c in VERDICT_COLORS.items():
                        if str(row.get("Verdict", "")).endswith(label):
                            color = c
                            break
                    if color:
                        return [f"color: {color}; font-weight: 700" if col == "Verdict" else "" for col in row.index]
                    return ["" for _ in row.index]

                # Display formatting only — underlying values are unrounded floats;
                # without this, Streamlit renders them at full float precision
                # (e.g. "97.400000" instead of "97.4").
                one_decimal = ["Fund.", "FundCov%", "Tech.", "Score", "P/E", "ROE%", "RevGr%", "RSI", "%OffHigh", "RS6m%"]
                two_decimal = ["Price", "Entry Price", "PEG", "D/E"]
                fmt = {col: "{:.1f}" for col in one_decimal if col in display_df.columns}
                fmt.update({col: "{:.2f}" for col in two_decimal if col in display_df.columns})
                if "Qty" in display_df.columns:
                    fmt["Qty"] = "{:.0f}"

                styled = display_df.style.apply(highlight_verdict, axis=1).format(fmt, na_rep="—")
                st.dataframe(styled, use_container_width=True, hide_index=True)

                if invest_amount <= 0:
                    st.caption(
                        "💡 Set an investment amount above to see a suggested share quantity per pick."
                    )

                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("Download CSV", csv, "scan_results.csv", "text/csv")

st.markdown("---")
st.markdown(
    """
    <p class="footnote">
    Entry Price is a simple technical suggestion, not a guarantee: if RSI is
    overbought (&gt;65) and the 50-day average sits below the current price,
    that average is offered as a pullback target; otherwise the current
    price is used. Qty = investment amount ÷ Entry Price, rounded down.
    Data via Yahoo Finance / yfinance (and Kite Connect if configured).
    For research and education only — not financial advice.
    </p>
    """,
    unsafe_allow_html=True,
)
