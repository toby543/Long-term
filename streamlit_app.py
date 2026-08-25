#!/usr/bin/env python3
"""
Streamlit UI for the long-term stock strategy scanner.

Run with:
    streamlit run streamlit_app.py
"""

import pandas as pd
import streamlit as st

from scanner import DEFAULT_TICKERS, scan

st.set_page_config(page_title="Long-Term Stock Strategy Scanner", page_icon="📈", layout="wide")

st.title("📈 Long-Term Stock Strategy Scanner")
st.caption(
    "Fundamental quality/GARP screen (ROE, margins, growth, debt, FCF, PEG) "
    "+ technical trend confirmation (SMA trend, RSI, 52-week high, relative "
    "strength vs. SPY) for long-term buy-and-hold candidates."
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

    col1, col2 = st.columns([1, 4])
    with col1:
        buy_only = st.checkbox("Show BUY only")
    submitted = st.form_submit_button("Scan", type="primary")

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
                df = scan(tickers)
            except Exception as exc:
                st.error(f"Scan failed: {exc}")
                df = None

        if df is not None:
            if buy_only:
                df = df[df["Verdict"] == "BUY"]

            if df.empty:
                st.info("No results to show.")
            else:
                def highlight_verdict(row):
                    colors = {"BUY": "#1f9d55", "WATCH": "#c99a2e", "AVOID": "#b3403a", "NO DATA": "#9aa0ab"}
                    color = colors.get(row.get("Verdict"), None)
                    if color:
                        return [f"color: {color}; font-weight: 700" if col == "Verdict" else "" for col in row.index]
                    return ["" for _ in row.index]

                # Display formatting only — underlying values are unrounded floats;
                # without this, Streamlit renders them at full float precision
                # (e.g. "97.400000" instead of "97.4").
                one_decimal = ["Fund.", "Tech.", "Score", "P/E", "ROE%", "RevGr%", "RSI", "%OffHigh", "RS6m%"]
                two_decimal = ["Price", "PEG", "D/E"]
                fmt = {col: "{:.1f}" for col in one_decimal if col in df.columns}
                fmt.update({col: "{:.2f}" for col in two_decimal if col in df.columns})

                styled = df.style.apply(highlight_verdict, axis=1).format(fmt, na_rep="—")
                st.dataframe(styled, use_container_width=True, hide_index=True)

                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("Download CSV", csv, "scan_results.csv", "text/csv")

st.markdown("---")
st.caption(
    "Data via Yahoo Finance / yfinance. For research and education only — not financial advice."
)
