# Binance Agent OS — Multi-Strategy Trading Agent

An autonomous AI trading agent for **Binance** that runs **four strategies**
on spot + perpetual futures, driven through the **Binance Agent OS MCP server**
(`agent.binance.com/mcp/agentic`, OAuth — no API keys).

The agent is meant to be run by any MCP-capable AI (GPT, Claude, Grok, …).
Each strategy ships a ready-to-paste **execution prompt** (`strategies/*/prompt.md`)
that tells the AI exactly what to do via the Binance MCP tools, plus a
reference Python implementation of the logic (`strategies/*/strategy.py`).

---

## The four strategies

| Strategy | Folder | What it does |
|---|---|---|
| **Grid** | `strategies/grid/` | Range-bound mean-reversion. Places a ladder of resting buy/sell orders around price and banks each oscillation. |
| **Regime rotation** | `strategies/regime_rotation/` | A supervisor that classifies market regime and only trades the sub-strategy that has an edge in it. |
| **Volume-spike breakout** | `strategies/volume_spike/` | Enters only when a breakout is backed by a genuine volume surge. |
| **Funding-rate** | `strategies/funding_rate/` | Trades Binance perp funding — contrarian flips on extreme funding and delta-neutral funding harvest. |

### 1) Grid
Profits from a price that oscillates inside a range. Orders are placed at
fixed percentage-spaced levels **below** (buys) and **above** (sells) the
current price, all post-only. Each time price dips to a buy and then recovers
to the next sell level, the bot banks the spacing as profit. It only deploys on
low-volatility, range-bound symbols and **tears the grid down** if price breaks
out of range — because a grid left running in a one-way trend loses money.

### 2) Regime rotation
Instead of forcing one strategy on every market, a **supervisor** classifies
each symbol's regime from volatility, trend-strength, and volume, then hands
control to the sub-strategy with the edge:

- **Trending** → momentum/breakout entries.
- **Ranging** → mean-reversion entries.
- **High-volatility / news** → stand aside (cash).
- **Crash** → stop out and go to cash.

A regime must persist for several bars before it flips (hysteresis) so a single
candle cannot cause whipsaw churn. This is what gives the agent robustness
across bull, bear, and chop.

### 3) Volume-spike breakout
Waits for a price breakout **confirmed by real volume** — the classic way to
separate a genuine move from a low-volume fakeout. It only acts when a
price-channel breakout happens on a bar whose volume is a large multiple of its
recent average while volatility is compressed (coiling). Enters on the breakout
close or the first light-volume retest, and protects with a volatility-based
stop.

### 4) Funding-rate
Binance perpetuals settle a **funding payment every 8h** between longs and
shorts. This strategy exploits that:
- **Contrarian flip**: extreme funding signals a crowded trade. Very negative
  funding (shorts crowded) → go long to collect funding and ride the squeeze;
  very positive → go short.
- **Cash-and-carry harvest**: steady positive funding → buy spot and short the
  perp of equal notional (delta-neutral) to collect funding with no price risk.

---

## Sizing & risk (fixed)
- **Spot:** `$6` notional per order.
- **Futures:** `5%` of the futures balance as margin at **3× leverage**.
- **Max `5` open trades** across spot + futures combined.
- **Universe:** the **top-20 USDT pairs by 24h volume** (fetched dynamically,
  so the bot always trades the most liquid markets).

These are enforced by the risk layer and repeated in every prompt so no AI agent
can exceed them.

---

## How to run

The AI is the execution engine. For each strategy:

1. Connect an MCP-capable AI to the Binance Agent OS server
   (`agent.binance.com/mcp/agentic`).
2. Paste the strategy's prompt (`strategies/<name>/prompt.md`) into the AI.
3. The AI reads the reference logic in `strategies/<name>/strategy.py`, fetches
   the top-20 pairs, sizes per the rules above, and trades via the MCP tools.

To watch every trade live, open the terminal (PowerShell):

```powershell
powershell -ExecutionPolicy Bypass -File terminal\terminal.ps1
```

It tails the live log and renders a color-coded, two-column dashboard of open
trades and recent orders as the AI places them.

### Local paper backtest / smoke test

Run all four strategies in paper mode against live market data (no real orders):

```bash
pip install -r requirements.txt pytest
python -m pytest tests/ -q        # unit tests (sizing, risk, indicators)
python scripts/smoke.py           # one full paper cycle over the top-20 pairs
```

---

## Repository layout

```
agent_os/        Binance OS MCP client + public market data + indicators + sizing
engine/          supervisor, risk layer (5-trade cap), logging
strategies/
  grid/            strategy.py + prompt.md
  regime_rotation/ strategy.py + prompt.md
  volume_spike/    strategy.py + prompt.md
  funding_rate/    strategy.py + prompt.md
terminal/          live PowerShell terminal
scripts/           CLI + smoke test
tests/             unit tests
config.yaml        public configuration (sizing, caps, universe)
```

> Note: strategy algorithm thresholds live in the strategy code and prompts.
> The README intentionally describes each strategy conceptually only.
