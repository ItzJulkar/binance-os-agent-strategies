# VOLUME-SPIKE BREAKOUT — AI PROMPT

Run the **volume-spike breakout** strategy. Read the logic in `strategies/volume_spike/strategy.py` and follow it exactly.

Rules: only top-20 USDT coins · all MARKET orders (instant fill) · spot $6 per order, futures 5% of wallet at 3x · max 5 open positions.

Scan for a volume spike (≥2x) + a real breakout after quiet trading. Only then enter at market. Manage open ones (stop / take profit). Report one line: what you did or "none — no signal".
