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
```

### Web app

A Flask front-end wraps the same scanning logic in a browser UI: enter
tickers, hit Scan, get a ranked, color-coded results table.

```bash
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000 in your browser.

### Deploying to Render

This repo includes a `render.yaml` blueprint so you can deploy the web app
with a public URL (reachable from your phone) in a few clicks:

1. Push this repo to GitHub (already done if you're reading this on GitHub).
2. In the [Render dashboard](https://dashboard.render.com), choose
   **New > Blueprint**, connect this repo, and Render will read
   `render.yaml` and provision the service automatically (free plan, Python
   runtime, `gunicorn app:app` as the start command).
3. Once deployed, Render gives you a public URL like
   `https://long-term-stock-scanner.onrender.com` — open that on any device,
   including your phone.

Notes:
- The free plan spins down after inactivity, so the first request after a
  while can take ~30-50s to wake back up.
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
