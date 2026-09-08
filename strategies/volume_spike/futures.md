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
