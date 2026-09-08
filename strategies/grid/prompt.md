# GRID — run

Run the grid strategy. Read and follow `strategies/grid/strategy.py` in this repo — it has the full logic and rules.

This strategy trades SPOT. Use the Binance Agent OS MCP to fetch data and place the code's MARKET orders.

Act on every live signal. If there is none right now, place nothing and say "no signal".
