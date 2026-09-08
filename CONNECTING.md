# How to connect your AI to Binance Agent OS (Claude, ChatGPT, Grok, …)

Everything in this repo runs through **one Binance MCP endpoint**:

```
https://agent.binance.com/mcp/agentic
```

It is an **OAuth-protected, Streamable-HTTP MCP server**. You do NOT paste an
API key. Instead, each time you add it to an AI client, Binance opens a login
page where you approve the connection and choose the permissions (scopes) the
agent gets.

---

## Before you start (do this once in Binance)

1. Log in to Binance and open the **Agent OS** section (binance.com → Agent OS,
   or the Binance app).
2. **Create / select an Agentic sub-account.** Agent OS works on an isolated
   sub-account — this is a safety wall. Whatever the AI does stays inside that
   sub-account; it can trade but **cannot withdraw** to an outside wallet.
3. **Fund that sub-account** with the balance the strategies will actually
   trade. Recommended small start: e.g. 50–100 USDT on spot.
4. Decide the **permissions** to grant. The strategies in this repo need:
   - market data (read tickers / candles / funding),
   - view balances / positions,
   - trade **spot** and **USDT-M futures** (the four strategies split across
     these two venues),
   - move funds between spot and futures **within the account**.
   Grant the minimum. Do NOT grant anything labelled withdrawal / transfer-out.

> If Binance does not expose a standalone "create sub-account" page, the OAuth
> flow in step 2 below will create the agentic sub-account for you when you
> first approve — just make sure to fund it afterward and keep it small.

---

## Step 2 — connect in your AI

Every MCP-capable client has an "add a remote MCP server" flow that takes a
URL. The exact menu changes over time, but the pattern is the same everywhere:

### Claude (Desktop or Claude Code)
- Desktop: **Settings → Connectors (or "MCP") → Add connection → remote /
  Streamable HTTP** → paste the URL → Connect → Binance login opens in your
  browser → approve the scopes.
- Claude Code (CLI): run
  ```
  claude mcp add --transport http binance https://agent.binance.com/mcp/agentic
  ```
  then restart Claude Code. It prompts you to log in and authorize.

### ChatGPT
- **Settings → Connectors → Add connector (remote / Streamable HTTP)** →
  paste the URL → Authorize. ChatGPT opens the Binance OAuth page; sign in and
  approve. After that the Binance tools appear for you to use in chat.

### Grok
- Grok (on X) does not expose arbitrary remote-MCP connectors to end users.
  **Use Grok via an MCP-capable host instead**, or run Grok through a tool that
  can add a remote server. If your Grok build supports custom connectors, add
  the same URL and authorize.

### Hermes (this agent)
- Hermes connects to Binance Agent OS MCP natively (the tools you see in a
  session). Configure the endpoint in your Hermes MCP config as a remote
  Streamable-HTTP server and authorize once.

### Codex / Cursor / VS Code
- Each has an "add MCP server / remote MCP" setting. Paste
  `https://agent.binance.com/mcp/agentic`, transport = **HTTP / Streamable**,
  and complete the OAuth login.

---

## Step 3 — pick a strategy and run it

1. Open the strategy prompt in this repo (the four are embedded in the
   README, files live in `strategies/<name>/prompt.md`).
2. Paste it into the AI that now has the Binance tools.
3. The AI reads the strategy code, checks the live market, and places **MARKET
   orders** only when the strategy's signal is actually present. If nothing is
   in a tradeable state it reports `no signal` and does nothing.

Example — the grid (spot) prompt:
```
Run the grid strategy. Read and follow `strategies/grid/strategy.py` in this repo.
This strategy trades SPOT. Use the Binance Agent OS MCP to fetch data and place
the code's MARKET orders. Act on every live signal. If there is none right now,
place nothing and say "no signal".
```

---

## Which tools the AI uses (the MCP tools Binance exposes)

After authorization the AI holds Binance tools. The relevant ones for these
strategies are:

- Market data: `spot_klines`, `futures_usds_klines`, `spot_ticker24hr`,
  `futures_usds_markPriceKline`, `futures_usds_premiumIndex` (funding),
  `spot_exchangeInfo` / `futures_usds_exchangeInfo` (lot sizes / filters).
- Account / positions: `spot_getAccount`, `spot_getOpenOrders`,
  `wallet_queryUserWalletBalance`, `futures_usds_accountInformationV3`,
  `futures_usds_positionInformationV2`, `futures_usds_currentAllOpenOrders`.
- Trading: `spot_newOrder` (MARKET), `spot_deleteOrder`,
  `futures_usds_newOrder` (MARKET), `futures_usds_changeInitialLeverage`,
  `futures_usds_changeMarginType`, `futures_usds_cancelOrder`.
- Fund moves within the account: `wallet_userUniversalTransfer`
  (spot ↔ futures).

The strategy code is filter-aware: it reads each symbol's real lot size and
rejects an order if it would be refused by the exchange, so the AI does not
waste calls on unplaceable orders.

---

## Safety checklist

- [ ] Trading runs on an **isolated agentic sub-account**, never your main spot.
- [ ] Sub-account is funded with an amount you are comfortable risking.
- [ ] Withdrawal / transfer-out permission is **NOT** granted.
- [ ] Spot orders are $6 each; futures are 5% of the sub-account balance × 3.
- [ ] Max 5 open positions at once (enforced in the strategy code).
- [ ] Re-check scopes whenever Binance asks you to re-authorize.

## Official reference

- Binance MCP Server docs:
  https://developers.binance.com/en/docs/agent-native/mcp-server/agentic
- Agent OS overview: https://www.binance.com/en-IA/agent-os
- MCP (Model Context Protocol) standard: https://modelcontextprotocol.io
