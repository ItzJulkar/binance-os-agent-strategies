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
