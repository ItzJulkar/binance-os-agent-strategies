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

## ▶ Live trading (this is the real thing)

This repo is built to **trade live on real money** through the Binance Agent
OS MCP. There is no testnet and no demo gate — when you authorize a trade, it
executes on Binance. Start small and only with money you can afford to lose.

**Run all four strategies live in one go** — paste the master prompt in
[`LIVE.md`](LIVE.md) into any AI that has the Binance Agent OS MCP connected
(Hermes / Claude / ChatGPT / Grok). The prompt makes the AI:

1. Check your real spot + futures balances and open positions first,
2. run each of the four strategies' code against the live market,
3. place MARKET orders for every real signal it finds,
4. set an ATR-based stop-loss / take-profit on each entry,
5. confirm fills and report back — and it **never invents a trade** if there is
   no signal (it says `no signal` and does nothing).

Rules it enforces (also in `config.yaml`): top-20 USDT coins, all MARKET orders,
spot $6 / futures 5% of wallet ×3, max 5 open positions total, one coin = one
position. If the futures wallet is empty it skips the futures strategies and
tells you why.

> Paper / no-risk runs still exist for testing — see the Local tools block
> below — but the default, headline use of this repo is **live Agent OS
> trading**.

## Auto stop-loss & take-profit (market-adaptive)

Every entry gets its own **stop-loss and take-profit that are not hardcoded** —
they are set from that coin's current volatility, so they adjust to the market:

- Each strategy reads the coin's recent **average true range (ATR)** and sets
  the stop at roughly **1.5× that ATR** and the take-profit at roughly **3× it**.
- A calm coin (small ATR) gets a **tight** stop and target; a volatile coin
  (large ATR) gets a **wider** one — so positions aren't stopped out by normal
  noise on a choppy coin, and targets aren't set unrealistically far on a calm one.
- Results are clamped to sane bounds (stop never below ~1% or above ~8%, target
  capped ~20%) so extreme volatility can't produce absurd orders.
- Once price hits a stop it **closes at market** (loss cut); when it hits the
  take-profit it **closes at market** (gain locked). Closing frees a slot so the
  bot can keep trading — it doesn't freeze at the 5-position cap.
- These are configured in `config.yaml` (`risk.stop_atr_multiplier`,
  `take_profit_atr_multiplier`, and the clamp bounds).

The one exception is the **Grid** strategy: its natural "take-profit" is the
range recovery (it sells when price bounces back to the top of its range), which
is also market-based. The ATR stop still protects the downside.

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

**How it works.** A coin normally moves inside an invisible band (its recent high and low). This strategy waits for the price to drift down near the bottom of that band, then buys — expecting the price to bounce back up. Once it rises back toward the top of the band, it sells and locks in the small gain. It only plays coins that are moving sideways (calm); it stays away from coins trending hard up or down, where "buying the dip" can just keep falling.

Why it can win / lose: it makes money when the coin keeps bouncing in its band. It can lose if the coin breaks out and keeps falling instead of bouncing — so it only ever risks a small amount per coin and stops out if the drop is too big.


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

**How it works.** Markets do different things at different times, and one fixed rule rarely works in all of them. This strategy first figures out what a coin is currently doing — trending up, drifting sideways, or crashing — and then only trades the pattern that fits that state:
- In a clear uptrend, it buys when the coin pushes to a new high (momentum).
- When a coin is drifting sideways, it buys the dips and sells the bounces (range).
- When a coin is crashing or jumping wildly on news, it does nothing and holds cash.

Because it changes its approach with the market instead of forcing one style, it aims to hold up across up, down, and sideways periods. It holds more cash when conditions are dangerous.


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

**How it works.** A price move means little if almost no one is trading; it means a lot when a big burst of volume happens. This strategy only acts when a coin breaks out of its quiet range at the same moment trading volume jumps sharply — a sign that a real move (not a fakeout) is starting. When that happens it buys (or shorts) the breakout and rides the move.

Why it filters so hard: most "breakouts" fail because they happen on thin volume. Requiring the volume burst at the same time removes most false signals, so it trades rarely but only on moves with real participation behind them.


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

**How it works.** In perpetual futures, longs and shorts pay each other a small fee every 8 hours. When one side is hugely crowded, that side pays the other. This strategy bets against the crowd: when almost everyone is short, it goes long (and collects from the shorts while price tends to recover); when almost everyone is long, it goes short. Over time it aims to collect those fees while the crowded position unwinds.

Why it can win / lose: extreme one-sided positioning often reverses, which is what it profits from. It can lose if the crowd is right and the trend keeps going, so it caps each position small and stops out if price moves against it.


Prompt:

```text
# FUNDING RATE — run

Run the funding-rate strategy. Read and follow `strategies/funding_rate/strategy.py` in this repo — it has the full logic and rules.

This strategy trades USDT-M FUTURES. Use the Binance Agent OS MCP to fetch data and place the code's MARKET orders.

Act on every live signal. If there is none right now, place nothing and say "no signal".
```

---

## Disclaimer

**This software is provided for educational and experimental purposes only.**
It is **not financial advice**, and nothing here is a recommendation to buy,
sell, or hold any asset.

Trading cryptocurrency, especially with leverage, carries a **high risk of
loss**. Automated / AI-driven trading can lose money quickly — including more
than the amount you intended to risk, and futures positions can be liquidated.
Past performance is not an indicator of future results.

By using this project you acknowledge that:
- You are solely responsible for your own trades and any losses they cause.
- The strategies are experimental and may contain bugs; there is **no
  guarantee** they are profitable or that they behave as described.
- You should only connect an account you are prepared to lose money on, and you
  should start with the smallest amount possible (ideally on a test/paper
  setup before any real funds).
- You must comply with the laws and regulations of your jurisdiction.
  Automated trading may be restricted or prohibited where you live. Check
  before using it.

**No warranty.** This software is provided "as is", without warranty of any
kind, express or implied. The authors are not liable for any loss, damage, or
expense arising from its use.
