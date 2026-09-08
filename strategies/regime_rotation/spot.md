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
