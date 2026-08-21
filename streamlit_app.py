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

with st.form("scan_form"):
    tickers_input = st.text_area(
        "Tickers (comma or newline separated)",
        value=", ".join(DEFAULT_TICKERS),
        height=100,
    )
    col1, col2 = st.columns([1, 4])
    with col1:
        buy_only = st.checkbox("Show BUY only")
    submitted = st.form_submit_button("Scan", type="primary")

if submitted:
    tickers = [
        t.strip().upper()
        for t in tickers_input.replace("\n", ",").split(",")
        if t.strip()
    ]
    tickers = list(dict.fromkeys(tickers))  # de-dupe, preserve order

    if not tickers:
        st.error("Enter at least one ticker symbol.")
    else:
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
                    colors = {"BUY": "#1f9d55", "WATCH": "#c99a2e", "AVOID": "#b3403a"}
                    color = colors.get(row.get("Verdict"), None)
                    if color:
                        return [f"color: {color}; font-weight: 700" if col == "Verdict" else "" for col in row.index]
                    return ["" for _ in row.index]

                styled = df.style.apply(highlight_verdict, axis=1)
                st.dataframe(styled, use_container_width=True, hide_index=True)

                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("Download CSV", csv, "scan_results.csv", "text/csv")

st.markdown("---")
st.caption(
    "Data via Yahoo Finance / yfinance. For research and education only — not financial advice."
)
