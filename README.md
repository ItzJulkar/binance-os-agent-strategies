# Binance Agent OS — Multi-Strategy Trading Agent

Four strategies on **Binance spot and USDT-M futures**, run through the Binance
Agent OS MCP (`agent.binance.com/mcp/agentic`, OAuth — no API keys).

Public repo: https://github.com/ItzJulkar/binance-os-agent-strategies

**The full logic and rules live in each `strategies/<name>/strategy.py`.** Each
strategy has one short prompt below that just points the AI at that file and
tells it to trade. Connect any AI (GPT / Claude / Grok / Hermes) to the Binance
MCP, paste the prompt, and it executes the strategy via MARKET orders. If there
is no live signal it places nothing.

Spot and futures are both covered across the four strategies (see Venue column).

## Local tools (run on this PC, no AI needed)
```
pip install -r requirements.txt pytest
python -m pytest tests/ -q                 # unit tests
python scripts/run.py --paper --cycles 1   # paper run over live market data
powershell -ExecutionPolicy Bypass -File terminal\terminal.ps1   # live dashboard
```

---
### 1) Grid  —  SPOT

**Buy-the-dip on calm coins, sell on the recovery.**

Prompt:

```text
# GRID — run

Run the grid strategy. Read and follow `strategies/grid/strategy.py` in this repo — it has the full logic and rules.

This strategy trades SPOT. Use the Binance Agent OS MCP to fetch data and place the code's MARKET orders.

Act on every live signal. If there is none right now, place nothing and say "no signal".
```

---
### 2) Regime Rotation  —  SPOT

**Reads market state - trends up, buys ranges, cash in crashes.**

Prompt:

```text
# REGIME ROTATION — run

Run the regime-rotation strategy. Read and follow `strategies/regime_rotation/strategy.py` in this repo — it has the full logic and rules.

This strategy trades SPOT. Use the Binance Agent OS MCP to fetch data and place the code's MARKET orders.

Act on every live signal. If there is none right now, place nothing and say "no signal".
```

---
### 3) Volume Spike  —  FUTURES

**Only buys a breakout when real volume confirms it.**

Prompt:

```text
# VOLUME-SPIKE BREAKOUT — run

Run the volume-spike strategy. Read and follow `strategies/volume_spike/strategy.py` in this repo — it has the full logic and rules.

This strategy trades USDT-M FUTURES. Use the Binance Agent OS MCP to fetch data and place the code's MARKET orders.

Act on every live signal. If there is none right now, place nothing and say "no signal".
```

---
### 4) Funding Rate  —  FUTURES

**Bets against the crowded side to collect funding.**

Prompt:

```text
# FUNDING RATE — run

Run the funding-rate strategy. Read and follow `strategies/funding_rate/strategy.py` in this repo — it has the full logic and rules.

This strategy trades USDT-M FUTURES. Use the Binance Agent OS MCP to fetch data and place the code's MARKET orders.

Act on every live signal. If there is none right now, place nothing and say "no signal".
```

---
