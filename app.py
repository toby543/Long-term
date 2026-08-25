#!/usr/bin/env python3
"""
Web UI for the long-term stock strategy scanner.

Run with:
    python app.py
Then open http://localhost:5000
"""

from flask import Flask, render_template, request

from scanner import DEFAULT_TICKERS, scan

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    results = None
    tickers_input = ", ".join(DEFAULT_TICKERS)
    buy_only = False
    force_refresh = False
    top_n = None
    error = None

    source = "custom"

    if request.method == "POST":
        source = request.form.get("source", "custom")
        buy_only = bool(request.form.get("buy_only"))
        force_refresh = bool(request.form.get("force_refresh"))
        top_n = request.form.get("top_n", type=int)

        if source == "nifty500":
            try:
                from indices import get_nifty500_tickers
                tickers = get_nifty500_tickers()
            except Exception as exc:
                error = f"Could not load Nifty 500 list: {exc}"
                tickers = []
            limit = request.form.get("limit", type=int)
            if limit:
                tickers = tickers[:limit]
            tickers_input = ", ".join(tickers)
        else:
            tickers_input = request.form.get("tickers", "")
            tickers = [t.strip().upper() for t in tickers_input.replace("\n", ",").split(",") if t.strip()]
            tickers = list(dict.fromkeys(tickers))  # de-dupe, preserve order

        if not error and not tickers:
            error = "Enter at least one ticker symbol."
        elif not error:
            try:
                df = scan(tickers, use_cache=not force_refresh)
                if buy_only:
                    df = df[df["Verdict"] == "BUY"]
                if top_n:
                    df = df.head(top_n)  # already sorted by Score descending
                results = df.to_dict(orient="records")
            except Exception as exc:  # surface scan failures to the user instead of a 500
                error = f"Scan failed: {exc}"

    return render_template(
        "index.html",
        results=results,
        tickers_input=tickers_input,
        buy_only=buy_only,
        force_refresh=force_refresh,
        top_n=top_n,
        source=source,
        error=error,
    )


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug, host="0.0.0.0", port=port)
