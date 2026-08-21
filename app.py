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
    error = None

    if request.method == "POST":
        tickers_input = request.form.get("tickers", "")
        buy_only = bool(request.form.get("buy_only"))

        tickers = [t.strip().upper() for t in tickers_input.replace("\n", ",").split(",") if t.strip()]
        tickers = list(dict.fromkeys(tickers))  # de-dupe, preserve order

        if not tickers:
            error = "Enter at least one ticker symbol."
        else:
            try:
                df = scan(tickers)
                if buy_only:
                    df = df[df["Verdict"] == "BUY"]
                results = df.to_dict(orient="records")
            except Exception as exc:  # surface scan failures to the user instead of a 500
                error = f"Scan failed: {exc}"

    return render_template(
        "index.html",
        results=results,
        tickers_input=tickers_input,
        buy_only=buy_only,
        error=error,
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
