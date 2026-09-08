# Binance Agent OS — Multi-Strategy Trading Agent

An AI agent that runs **four strategies** on Binance spot + futures through the
**Binance Agent OS MCP** (`agent.binance.com/mcp/agentic`, OAuth — no API keys).

Public repo: https://github.com/ItzJulkar/binance-os-agent-strategies

To trade: connect any AI (GPT / Claude / Grok / Hermes) to the Binance Agent OS
MCP, then paste one of the **short prompts** below. Each prompt tells the AI to
read that strategy's code from the repo and execute it immediately. The full
logic lives in the code — the prompt is only a trigger.

**Every order is a MARKET order.** Rules (all in code): spot $6, futures 5% of
wallet at 3x, max 5 open positions, top-20 USDT coins by volume.

Local tools (run on this PC, no AI needed):
```
pip install -r requirements.txt pytest
python -m pytest tests/ -q                 # unit tests
python scripts/run.py --paper --cycles 1   # paper run over live market data
powershell -ExecutionPolicy Bypass -File terminal\terminal.ps1   # live dashboard
```

---
### 1) Grid

**Buy the dip at the bottom of a coin's range, sell it on the recovery. Calm coins only.**

Prompt:

```text
# GRID — run now

Use the repo https://github.com/ItzJulkar/binance-os-agent-strategies
Read `strategies/grid/strategy.py` there and follow it. It is the whole strategy.

Execute it live on the Binance Agent OS MCP now:
- top-20 USDT coins · all MARKET orders · spot $6, futures 5% of wallet at 3x
- max 5 open positions

Do not explain, do not summarize the code back to me. Just scan and place the
trades, then report what you placed in one or two lines.
```

---
### 2) Regime rotation

**Reads the market state, follows trends, buys ranges, stays in cash on crashes.**

Prompt:

```text
# REGIME ROTATION — run now

Use the repo https://github.com/ItzJulkar/binance-os-agent-strategies
Read `strategies/regime_rotation/strategy.py` there and follow it. It is the whole strategy.

Execute it live on the Binance Agent OS MCP now:
- top-20 USDT coins · all MARKET orders · spot $6, futures 5% of wallet at 3x
- max 5 open positions

Do not explain, do not summarize the code back to me. Just scan, classify each
coin's regime, place the trades the code says, then report in one or two lines.
```

---
### 3) Volume-spike breakout

**Only buys a breakout when a big volume jump confirms it's real.**

Prompt:

```text
# VOLUME-SPIKE — run now

Use the repo https://github.com/ItzJulkar/binance-os-agent-strategies
Read `strategies/volume_spike/strategy.py` there and follow it. It is the whole strategy.

Execute it live on the Binance Agent OS MCP now:
- top-20 USDT coins · all MARKET orders · spot $6, futures 5% of wallet at 3x
- max 5 open positions

Do not explain, do not summarize the code back to me. Just scan, find the
volume-spike breakout the code looks for, place the trade, then report in one line.
```

---
### 4) Funding rate

**Bets against a crowded futures crowd to collect the 8h funding fee.**

Prompt:

```text
# FUNDING RATE — run now

Use the repo https://github.com/ItzJulkar/binance-os-agent-strategies
Read `strategies/funding_rate/strategy.py` there and follow it. It is the whole strategy.

Execute it live on the Binance Agent OS MCP now:
- top-20 USDT futures coins · all MARKET orders · each position 5% of wallet at 3x
- max 5 open positions

Do not explain, do not summarize the code back to me. Just scan funding rates,
open the trades the code says, then report in one line.
```

---
