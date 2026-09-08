# FUNDING RATE — run

Run the funding-rate strategy. Read and follow `strategies/funding_rate/strategy.py` in this repo — it has the full logic and rules.

This strategy trades USDT-M FUTURES. Use the Binance Agent OS MCP to fetch data and place the code's MARKET orders.

Act on every live signal. If there is none right now, place nothing and say "no signal".
