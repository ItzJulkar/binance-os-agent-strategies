# GRID — SPOT

Repo: https://github.com/ItzJulkar/binance-os-agent-strategies (strategies/grid/strategy.py)

Trade spot MARKET. Spot order = $6.
Scan the top-20 USDT coins. For each you don't already hold:
- only calm coins (14-bar swing ~1.5-4.5% of price)
- if the coin is now in the LOWER half of its last-20-bar high/low range -> MARKET BUY $6.
- if you already hold it and it reached the UPPER half or is up ~4% -> MARKET SELL to close.

CRITICAL: only trade if the signal is actually present in the live market right now. If the condition is NOT met, place NO order and say 'no signal'. Never invent a trade to 'do something'.
Report one line.
