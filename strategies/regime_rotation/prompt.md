# REGIME ROTATION — AI PROMPT

Run the **regime rotation** strategy. Read the logic in `strategies/regime_rotation/strategy.py` and follow it exactly.

Rules: only top-20 USDT coins · all MARKET orders (instant fill) · spot $6 per order, futures 5% of wallet at 3x · max 5 open positions · stop new entries if down 3% on the day.

Classify each coin's regime from the code. Buy only where it has an edge (trending→momentum, ranging→dip buy). Do nothing in crash/jumpy. Report one line: market state + what you did + open count (x/5).
