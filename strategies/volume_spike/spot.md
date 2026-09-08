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
