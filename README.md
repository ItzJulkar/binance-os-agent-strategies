# Binance Agent OS — Multi-Strategy Trading Agent

Four strategies on Binance spot + USDT-M futures, run through the **Binance
Agent OS MCP** (`agent.binance.com/mcp/agentic`, OAuth — no API keys). Public
repo: https://github.com/ItzJulkar/binance-os-agent-strategies

Connect any AI (GPT / Claude / Grok / Hermes) to the Binance MCP, then paste the
**spot** or **futures** prompt for a strategy. Every prompt is short and
self-contained, all orders are MARKET, and it **never trades unless the signal
is actually present** (otherwise it reports 'no signal'). The matching logic is
also in `strategies/<name>/strategy.py`.

Local tools (run here, no AI needed):
```
pip install -r requirements.txt pytest
python -m pytest tests/ -q                 # unit tests
python scripts/run.py --paper --cycles 1   # paper run over live market data
powershell -ExecutionPolicy Bypass -File terminal\terminal.ps1   # live dashboard
```

---

### 1) Grid  —  Buy the dip in a calm coin's range, sell on the recovery.

Prompts: futures.md / spot.md. Each is self-contained.

**FUTURES:**

```text
# GRID — FUTURES

Repo: https://github.com/ItzJulkar/binance-os-agent-strategies (strategies/grid/strategy.py)

Trade USDT-M futures MARKET. Position = 5% of wallet at 3x leverage.
Scan the top-20 futures coins. For each you don't already hold:
- only calm coins (14-bar swing ~1.5-4.5% of price)
- if the coin is now in the LOWER half of its last-20-bar high/low range -> MARKET LONG 5% x3.
- if you already hold it and it reached the UPPER half or is up ~4% -> MARKET close.

CRITICAL: only trade if the signal is actually present in the live market right now. If the condition is NOT met, place NO order and say 'no signal'. Never invent a trade to 'do something'.
Report one line.
```

**SPOT:**

```text
# GRID — SPOT

Repo: https://github.com/ItzJulkar/binance-os-agent-strategies (strategies/grid/strategy.py)

Trade spot MARKET. Spot order = $6.
Scan the top-20 USDT coins. For each you don't already hold:
- only calm coins (14-bar swing ~1.5-4.5% of price)
- if the coin is now in the LOWER half of its last-20-bar high/low range -> MARKET BUY $6.
- if you already hold it and it reached the UPPER half or is up ~4% -> MARKET SELL to close.

CRITICAL: only trade if the signal is actually present in the live market right now. If the condition is NOT met, place NO order and say 'no signal'. Never invent a trade to 'do something'.
Report one line.
```


---

### 2) Regime rotation  —  Reads the market state — follows trends, buys ranges, sits in cash on crashes.

Prompts: futures.md / spot.md. Each is self-contained.

**FUTURES:**

```text
# REGIME ROTATION — FUTURES

Repo: https://github.com/ItzJulkar/binance-os-agent-strategies (strategies/regime_rotation/strategy.py)

Trade USDT-M futures MARKET. Position = 5% of wallet at 3x.
Scan top-20 futures coins. Classify each (ADX/RSI/volume/trend):
- trending up + fresh break above its recent high -> MARKET LONG 5% x3.
- ranging + oversold at the low of its band -> MARKET LONG 5% x3 (dip).
- crashing or very jumpy -> DO NOTHING (cash).
Only act after the same state 2 checks in a row. Close losers / take profit.

CRITICAL: only trade if the signal is actually present in the live market right now. If the condition is NOT met, place NO order and say 'no signal'. Never invent a trade to 'do something'.
Report one line.
```

**SPOT:**

```text
# REGIME ROTATION — SPOT

Repo: https://github.com/ItzJulkar/binance-os-agent-strategies (strategies/regime_rotation/strategy.py)

Trade spot MARKET. Spot order = $6.
Scan top-20 USDT coins. Classify each (ADX/RSI/volume/trend):
- trending up + fresh break above its recent high -> MARKET BUY $6.
- ranging + oversold (RSI<35) at the low of its band -> MARKET BUY $6 (dip).
- crashing or very jumpy -> DO NOTHING (cash).
Only act after the same state 2 checks in a row. Close losers / take profit ~3-6%.

CRITICAL: only trade if the signal is actually present in the live market right now. If the condition is NOT met, place NO order and say 'no signal'. Never invent a trade to 'do something'.
Report one line.
```


---

### 3) Volume-spike breakout  —  Only buys a breakout when a big volume jump confirms it's real.

Prompts: futures.md / spot.md. Each is self-contained.

**FUTURES:**

```text
# VOLUME-SPIKE BREAKOUT — FUTURES

Repo: https://github.com/ItzJulkar/binance-os-agent-strategies (strategies/volume_spike/strategy.py)

Trade USDT-M futures MARKET. Position = 5% of wallet at 3x.
Scan top-20 futures coins on 1h candles. Trade only when ALL 3 at once:
1. this hour's volume >= 2x the last-20-hour average, AND
2. price closed beyond the prior-20-hour high (long) or low (short), AND
3. the coin was quiet before (ATR below its 20-bar average).
Then MARKET LONG/SHORT 5% x3. Longs skipped if funding very positive.

CRITICAL: only trade if the signal is actually present in the live market right now. If the condition is NOT met, place NO order and say 'no signal'. Never invent a trade to 'do something'.
Report one line or 'no signal'.
```

**SPOT:**

```text
# VOLUME-SPIKE BREAKOUT — SPOT

Repo: https://github.com/ItzJulkar/binance-os-agent-strategies (strategies/volume_spike/strategy.py)

Trade spot MARKET. Spot order = $6.
Scan top-20 USDT coins on 1h candles. Buy only when ALL 3 at once:
1. this hour's volume >= 2x the last-20-hour average, AND
2. price closed above the prior-20-hour high (real breakout), AND
3. the coin was quiet before (ATR below its 20-bar average).
Then MARKET BUY $6. If a coin fails any of the 3, skip it.

CRITICAL: only trade if the signal is actually present in the live market right now. If the condition is NOT met, place NO order and say 'no signal'. Never invent a trade to 'do something'.
Report one line or 'no signal'.
```


---

### 4) Funding rate  —  Bets against the crowded futures side to collect the 8h funding fee.

Prompts: futures.md. Each is self-contained.

**FUTURES:**

```text
# FUNDING RATE — FUTURES

Repo: https://github.com/ItzJulkar/binance-os-agent-strategies (strategies/funding_rate/strategy.py)

USDT-M futures MARKET. Position = 5% of wallet at 3x.
Scan top-20 futures coins' 8h funding rate:
- funding <= -0.05%/8h (crowd very short) for 3 checks -> MARKET LONG 5% x3.
- funding >= +0.05%/8h (crowd very long) for 3 checks -> MARKET SHORT 5% x3.
- otherwise DO NOTHING.
Stop ~3%. Close when funding returns near normal, stop hits, or after ~3 days.

CRITICAL: only trade if the signal is actually present in the live market right now. If the condition is NOT met, place NO order and say 'no signal'. Never invent a trade to 'do something'.
Report one line or 'no signal'.
```


---
