# Binance Agent OS — Multi-Strategy Trading Agent

An AI trading agent for **Binance** that runs **four strategies** on spot +
futures through the **Binance Agent OS MCP** (`agent.binance.com/mcp/agentic`,
OAuth — no API keys).

Any MCP-capable AI (GPT, Claude, Grok, Hermes) runs it. Each strategy has one
**short prompt** below — paste it into the AI and it trades. The full logic
lives in `strategies/<name>/strategy.py`; the prompt tells the AI which file to
follow. **Every order is a MARKET order (instant fill).**

---

## Rules (same for every strategy)
- Spot orders **$6**. Futures **5% of wallet at 3x**.
- Max **5** open positions.
- Only **top-20 USDT coins** by volume.
- Quantities rounded to the coin's lot size.

---

## How to run
1. Connect any AI to the Binance Agent OS server (`agent.binance.com/mcp/agentic`).
2. Paste a strategy prompt below into the AI.
3. Watch trades live: `powershell -ExecutionPolicy Bypass -File terminal\terminal.ps1`

---

### 1) Grid

**Buy the dip at the bottom of a coin's recent range, sell it when it recovers. Calm coins only.**

Prompt:

```text
# GRID — AI PROMPT

Run the **grid** strategy. Read the logic in `strategies/grid/strategy.py` and follow it exactly.

Rules: only top-20 USDT coins · all MARKET orders (instant fill) · spot $6 per order, futures 5% of wallet at 3x · max 5 open positions.

Scan the market. If a coin is in the grid buy zone, place the order. Manage open ones (sell on recovery). Report one line: what you did + open count (x/5).
```

---
### 2) Regime rotation

**Reads the market state and picks the right move: follow trends, buy ranges, stay in cash on crashes.**

Prompt:

```text
# REGIME ROTATION — AI PROMPT

Run the **regime rotation** strategy. Read the logic in `strategies/regime_rotation/strategy.py` and follow it exactly.

Rules: only top-20 USDT coins · all MARKET orders (instant fill) · spot $6 per order, futures 5% of wallet at 3x · max 5 open positions · stop new entries if down 3% on the day.

Classify each coin's regime from the code. Buy only where it has an edge (trending→momentum, ranging→dip buy). Do nothing in crash/jumpy. Report one line: market state + what you did + open count (x/5).
```

---
### 3) Volume-spike breakout

**Only buys a breakout when a big volume jump confirms it's real, not a fake move.**

Prompt:

```text
# VOLUME-SPIKE BREAKOUT — AI PROMPT

Run the **volume-spike breakout** strategy. Read the logic in `strategies/volume_spike/strategy.py` and follow it exactly.

Rules: only top-20 USDT coins · all MARKET orders (instant fill) · spot $6 per order, futures 5% of wallet at 3x · max 5 open positions.

Scan for a volume spike (≥2x) + a real breakout after quiet trading. Only then enter at market. Manage open ones (stop / take profit). Report one line: what you did or "none — no signal".
```

---
### 4) Funding rate

**Bets against a crowded futures crowd to collect the 8h funding fee and ride the price snap-back.**

Prompt:

```text
# FUNDING RATE — AI PROMPT

Run the **funding-rate** strategy. Read the logic in `strategies/funding_rate/strategy.py` and follow it exactly.

Rules: only top-20 USDT futures coins · all MARKET orders (instant fill) · each position 5% of wallet at 3x · max 5 open positions.

When a coin's 8h funding is extreme (crowd too long → short it, crowd too short → long it), open at market. Close when funding normalizes / stop / ~3 days. Report one line: what you did or "none — funding normal".
```

---
## Test (paper, no real money)
```
pip install -r requirements.txt pytest
python -m pytest tests/ -q
python scripts/run.py --paper --cycles 1
```

## Layout
```
strategies/<name>/strategy.py   the strategy logic
strategies/<name>/prompt.md     the short AI prompt
agent_os/  market data + Binance MCP client + indicators + sizing
engine/    supervisor + risk (5-trade cap)
terminal/  live dashboard
```
