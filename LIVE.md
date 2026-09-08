# LIVE TRADE — next-session master prompt

Paste this into a NEW Hermes session (this same profile, so Binance Agent OS MCP
is connected). It triggers REAL live trading. Read it fully before pasting —
you are authorizing real money orders.

---

```
You have the Binance Agent OS MCP connected. Run the multi-strategy bot from
this PC's repo ~/binance-agent-os-strategies in LIVE mode (REAL orders).

STRATEGIES (code files are the authority — read each before trading):
- grid:  ~/binance-agent-os-strategies/strategies/grid/strategy.py          (SPOT)
- regime_rotation:  .../strategies/regime_rotation/strategy.py              (SPOT)
- volume_spike:     .../strategies/volume_spike/strategy.py                  (FUTURES)
- funding_rate:     .../strategies/funding_rate/strategy.py                  (FUTURES)

HARD RULES (never break):
1. Only the top-20 USDT coins by 24h volume.
2. ALL orders are MARKET orders (instant fill).
3. Sizing: spot = $6 per order; futures = 5% of the futures wallet balance at 3x
   leverage. If a futures wallet has 0 balance, do NOT open futures trades.
4. Max 5 open positions TOTAL (spot + futures). One coin = one position.
5. Every entry sets an ATR-based stop-loss and take-profit (read the code /
   config.yaml risk block) — respect them and close at market when hit.
6. If a strategy's code produces NO live signal right now, place NOTHING and
   say "no signal". Never invent a trade.
7. Round every quantity to the coin's real lot size and check it clears the
   coin's minNotional before ordering (read exchangeInfo filters first).

DO THIS:
1. Check the live account state first (spot + futures balances, open positions,
   open orders) via the MCP. Report what you see.
2. For each strategy, read its strategy.py, fetch the live market data it needs,
   and determine its current signal(s). Respect the sizing + the 5-position cap
   across all strategies together.
3. Place the MARKET orders for every live signal (start with the GRID/SPOT
   strategy — that account is funded). If the futures wallet is empty, skip
   futures strategies and say why.
4. Set the ATR stop-loss / take-profit per the code.
5. Confirm each fill by reading back the position/order.
6. Report in plain lines: what you bought/sold, on which coins, size, and the
   stop/take-profit set for each. Keep it short.

IMPORTANT: this is REAL money. Do exactly what the strategy code says. Do not
improvise sizing, do not overtrade, do not exceed 5 open positions. If anything
is unclear or an order fails, stop and report the error — do not retry blindly.
```
