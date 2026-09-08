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
