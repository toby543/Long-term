# Long-Term Stock Strategy Scanner

A screener for finding stocks worth buying and holding for the long term (years,
not weeks). It blends **fundamental quality/value analysis** with **technical
trend confirmation**, on the idea that:

- Fundamentals tell you whether a business is worth owning.
- Technicals tell you whether *now* is a sane time to be buying it (i.e. the
  market isn't actively rejecting the stock, and you're not catching a falling
  knife or paying into a blow-off top).

## The Strategy

### 1. Fundamental screen — "is this a good business at a fair price?"

| Factor | Metric | Why it matters | Rule of thumb |
|---|---|---|---|
| Profitability | Return on Equity (ROE) | Efficient use of shareholder capital | ROE ≥ 15% |
| Profitability | Operating margin | Pricing power / cost discipline | Positive & stable |
| Growth | Revenue growth (YoY) | Business is expanding, not stagnant | ≥ 5–8% |
| Growth | Earnings growth (YoY) | Growth is translating to the bottom line | Positive |
| Financial health | Debt/Equity | Survives downturns, not over-levered | ≤ 1.0–1.5 (sector-dependent) |
| Financial health | Current ratio | Can cover near-term obligations | ≥ 1.0 |
| Cash generation | Free cash flow | Real cash, not just accounting earnings | Positive FCF |
| Valuation | P/E vs historical / peers | Not wildly overpaying | Reasonable, sector-relative |
| Valuation | PEG ratio (P/E ÷ growth) | Growth-adjusted valuation (Peter Lynch) | ≤ 1.5–2.0 |
| Shareholder return | Dividend / buyback trend (optional) | Capital discipline | Non-dilutive, growing payout is a plus |

This is a classic **quality + reasonable price (GARP)** approach — closer to
Buffett/Munger/Lynch than deep value or pure momentum. The goal isn't the
cheapest stock, it's the best business you can buy without overpaying.

### 2. Technical screen — "is the trend/market agreeing with me?"

Long-term investing doesn't mean ignoring price action — it means using it as
a *confirmation and timing filter*, not the primary decision driver.

| Signal | What it checks | Why |
|---|---|---|
| Price > 200-day SMA | Long-term uptrend | Don't buy into a structural downtrend |
| 50-day SMA > 200-day SMA | "Golden cross" regime | Medium-term trend confirms long-term trend |
| RSI(14) between 35–70 | Not extremely overbought/oversold | Avoid chasing blow-off tops; avoid falling knives |
| Off 52-week high | Distance from high | Flags stretched entries (very extended = wait for a pullback) |
| Relative strength vs benchmark (e.g. SPY) | Outperformance over 6–12 months | Buy relative leaders, not laggards |
| Volume trend | Above-average volume on up moves | Confirms institutional participation |

### 3. Composite score

Each stock gets a **Fundamental Score (0–100)** and a **Technical Score
(0–100)**. A stock is flagged as a **BUY candidate** when it clears minimum
thresholds on *both* — good business, reasonable price, healthy trend. This
avoids two classic traps:
- Buying a "great story" stock whose chart is in freefall.
- Buying a strong chart on a mediocre/overpriced business (pure momentum).

Weighting emphasizes fundamentals (65%) over technicals (35%), since this is
a long-term strategy — technicals here are a filter/timing aid, not the
primary thesis.

## Usage

```bash
pip install -r requirements.txt

# Scan a default watchlist
python scanner.py

# Scan your own tickers
python scanner.py --tickers AAPL MSFT GOOGL NVDA COST

# Scan tickers from a file (one per line)
python scanner.py --file watchlist.txt

# Export results to CSV
python scanner.py --tickers AAPL MSFT --output results.csv

# Only show BUY candidates
python scanner.py --tickers AAPL MSFT NVDA TSLA --buy-only

# Scan the Nifty 500 (India) — fetched live from NSE, cached locally for a week
python scanner.py --index nifty500 --limit 50   # try a subset first, it's 500 tickers
python scanner.py --index nifty500 --buy-only --output nifty500_buys.csv
```

Note on the Nifty 500: the constituent list is fetched live from NSE
(`indices.py`) rather than hardcoded, since index membership changes
periodically. Scanning all 500 tickers hits `yfinance` 500+ times, so it can
take several minutes — use `--limit` to try a smaller slice first.
Relative-strength scoring automatically benchmarks `.NS`/`.BO` tickers
against the Nifty 500 index (`^CRSLDX`) instead of SPY.

**On rate limiting:** Yahoo Finance aggressively rate-limits `yfinance`
requests, especially from shared hosting IPs (Streamlit Cloud, Render free
tier). `scanner.py` handles this by keeping concurrency low (4 workers),
spacing requests out (min ~0.5s apart, enforced globally across threads),
and retrying 429s with exponential backoff (up to 4 retries). If you still
hit `ERROR: Rate limited by Yahoo Finance` on individual tickers, wait a
minute and re-scan, or scan a smaller batch (`--limit`) at a time — this is
Yahoo throttling the shared IP the app runs on, not a bug in the scanner.

**On "everything shows AVOID":** the fundamental score only counts a metric
(ROE, margins, growth, etc.) toward the score if Yahoo actually returned
data for it — a missing field is excluded from scoring, not treated as a
failing grade. If you're still seeing every ticker as AVOID, check the raw
`P/E`/`ROE%`/`RevGr%` columns in the output: if they're mostly blank across
the board, Yahoo's `.info` endpoint is returning sparse data for your
session (common under rate limiting), not a real fundamental problem with
those companies — wait and re-scan rather than trusting the verdict.

### Web app

Two front-ends wrap the same `scan()` logic — pick whichever you prefer.

**Streamlit** (recommended — simplest to deploy):

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Then open http://localhost:8501 in your browser.

**Flask**:

```bash
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000 in your browser.

### Deploying

**Option A — Streamlit Community Cloud (easiest, free, zero config):**

1. Push this repo to GitHub (already done if you're reading this on GitHub).
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with
   GitHub, click **New app**.
3. Select this repo/branch and set the main file path to
   `streamlit_app.py`. Streamlit Cloud installs `requirements.txt`
   automatically.
4. Deploy — you get a public URL like
   `https://long-term-stock-scanner.streamlit.app`, reachable from any
   device including your phone.

**Option B — Render:**

This repo includes a `render.yaml` blueprint (currently configured to run
`streamlit_app.py`) so you can deploy with a public URL in a few clicks:

1. In the [Render dashboard](https://dashboard.render.com), choose
   **New > Blueprint**, connect this repo, and Render will read
   `render.yaml` and provision the service automatically (free plan, Python
   runtime, Streamlit as the start command).
2. Once deployed, Render gives you a public URL like
   `https://long-term-stock-scanner.onrender.com`.

To deploy the Flask app on Render instead, change `render.yaml`'s
`startCommand` to `gunicorn app:app --bind 0.0.0.0:$PORT` (and update the
`Procfile` the same way).

Notes:
- Render's free plan spins down after inactivity, so the first request
  after a while can take ~30-50s to wake back up. Streamlit Community Cloud
  apps also sleep after inactivity and wake on the next visit.
- A `Procfile` is also included for platforms that use that convention
  instead of `render.yaml` (e.g. Heroku-style buildpacks).

## Output

The scanner prints a ranked table with fundamental score, technical score,
composite score, and a verdict (`BUY`, `WATCH`, `AVOID`), plus the key raw
metrics behind each score so you can sanity-check the call yourself.

## Disclaimer

This is a screening tool for research and education, not financial advice.
Data comes from Yahoo Finance via `yfinance` and can be delayed, incomplete,
or wrong. Always verify fundamentals from primary sources (10-K/10-Q filings)
before investing real money.
