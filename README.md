# Binance Agent OS — Multi-Strategy Trading Agent

Four strategies on **Binance spot and USDT-M futures**, run through the Binance
Agent OS MCP (`agent.binance.com/mcp/agentic`, OAuth — no API keys).

Public repo: https://github.com/ItzJulkar/binance-os-agent-strategies

**The full logic and rules live in each `strategies/<name>/strategy.py`.** Each
strategy has one short prompt below that just points the AI at that file and
tells it to trade. Connect any AI (GPT / Claude / Grok / Hermes) to the Binance
MCP, paste the prompt, and it executes the strategy via MARKET orders. If there
is no live signal it places nothing.

Spot and futures are both covered across the four strategies (see Venue column).

## How to connect your own AI to Binance Agent OS

The strategies run through **one Binance MCP endpoint**:
`https://agent.binance.com/mcp/agentic`. You connect any MCP-capable AI
(Claude, ChatGPT, Grok, Hermes, Codex, Cursor, VS Code) to that URL with an
OAuth login — no API keys.

Steps:

1. **Create an Agentic sub-account** (or use the one Agent OS makes). Inside
   Binance → *Agent OS*, authorize an agent and fund its sub-account. The agent
   can only trade inside that isolated sub-account — it **cannot withdraw**.
   Start with a small balance you are willing to trade.
2. **Grant scopes.** Approve what the agent may do: market data, view balances,
   trade spot / USDT-M futures, move funds within the account. Only approve
   what a strategy needs.
3. **Add the MCP server in your AI client** with this URL:
   `https://agent.binance.com/mcp/agentic`
   - **Claude / Claude Code**: Settings → Connectors / *Claude MCP* → Add
     remote server → paste the URL → it opens the Binance OAuth window → Approve.
   - **ChatGPT**: Settings → Connectors → add a remote/Streamable-HTTP MCP →
     paste the URL → sign in & approve.
   - **Grok / Hermes / Codex / Cursor / VS Code**: use their "add remote MCP
     server" flow with the same Streamable-HTTP URL.
   The exact button names differ per app, but every one of these accepts a
   remote Streamable-HTTP MCP URL and then runs an OAuth login to Binance.
4. **Fund the sub-account** with the spot/futures balance the strategies will
   trade (the code sizes spot at $6 and futures at 5% of that balance ×3).
5. **Paste a strategy prompt** (below) into the AI and let it run. Watch trades
   in your AI's live output, or in the terminal on this PC.

> **Security:** you are granting an AI limited trade rights on a real account.
> Keep the sub-account funded with only what you are OK losing, do NOT grant
> withdrawal, and re-check the scopes whenever Binance prompts you.

Full walkthrough per client: [`CONNECTING.md`](CONNECTING.md)

## Local tools (run on this PC, no AI needed)
```
pip install -r requirements.txt pytest
python -m pytest tests/ -q                 # unit tests
python scripts/run.py --paper --cycles 1   # paper run over live market data
powershell -ExecutionPolicy Bypass -File terminal\terminal.ps1   # live dashboard
```

---
### 1) Grid  —  SPOT

**Buy-the-dip on calm coins, sell on the recovery.**

Prompt:

```text
# GRID — run

Run the grid strategy. Read and follow `strategies/grid/strategy.py` in this repo — it has the full logic and rules.

This strategy trades SPOT. Use the Binance Agent OS MCP to fetch data and place the code's MARKET orders.

Act on every live signal. If there is none right now, place nothing and say "no signal".
```

---
### 2) Regime Rotation  —  SPOT

**Reads market state - trends up, buys ranges, cash in crashes.**

Prompt:

```text
# REGIME ROTATION — run

Run the regime-rotation strategy. Read and follow `strategies/regime_rotation/strategy.py` in this repo — it has the full logic and rules.

This strategy trades SPOT. Use the Binance Agent OS MCP to fetch data and place the code's MARKET orders.

Act on every live signal. If there is none right now, place nothing and say "no signal".
```

---
### 3) Volume Spike  —  FUTURES

**Only buys a breakout when real volume confirms it.**

Prompt:

```text
# VOLUME-SPIKE BREAKOUT — run

Run the volume-spike strategy. Read and follow `strategies/volume_spike/strategy.py` in this repo — it has the full logic and rules.

This strategy trades USDT-M FUTURES. Use the Binance Agent OS MCP to fetch data and place the code's MARKET orders.

Act on every live signal. If there is none right now, place nothing and say "no signal".
```

---
### 4) Funding Rate  —  FUTURES

**Bets against the crowded side to collect funding.**

Prompt:

```text
# FUNDING RATE — run

Run the funding-rate strategy. Read and follow `strategies/funding_rate/strategy.py` in this repo — it has the full logic and rules.

This strategy trades USDT-M FUTURES. Use the Binance Agent OS MCP to fetch data and place the code's MARKET orders.

Act on every live signal. If there is none right now, place nothing and say "no signal".
```

---
