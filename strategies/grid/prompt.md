# GRID — AI PROMPT

Run the **grid** strategy. Read the logic in `strategies/grid/strategy.py` and follow it exactly.

Rules: only top-20 USDT coins · all MARKET orders (instant fill) · spot $6 per order, futures 5% of wallet at 3x · max 5 open positions.

Scan the market. If a coin is in the grid buy zone, place the order. Manage open ones (sell on recovery). Report one line: what you did + open count (x/5).
