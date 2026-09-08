# FUNDING RATE — AI PROMPT

Run the **funding-rate** strategy. Read the logic in `strategies/funding_rate/strategy.py` and follow it exactly.

Rules: only top-20 USDT futures coins · all MARKET orders (instant fill) · each position 5% of wallet at 3x · max 5 open positions.

When a coin's 8h funding is extreme (crowd too long → short it, crowd too short → long it), open at market. Close when funding normalizes / stop / ~3 days. Report one line: what you did or "none — funding normal".
