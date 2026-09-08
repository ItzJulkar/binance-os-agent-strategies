# GRID — FUTURES

Repo: https://github.com/ItzJulkar/binance-os-agent-strategies (strategies/grid/strategy.py)

Trade USDT-M futures MARKET. Position = 5% of wallet at 3x leverage.
Scan the top-20 futures coins. For each you don't already hold:
- only calm coins (14-bar swing ~1.5-4.5% of price)
- if the coin is now in the LOWER half of its last-20-bar high/low range -> MARKET LONG 5% x3.
- if you already hold it and it reached the UPPER half or is up ~4% -> MARKET close.

CRITICAL: only trade if the signal is actually present in the live market right now. If the condition is NOT met, place NO order and say 'no signal'. Never invent a trade to 'do something'.
Report one line.
