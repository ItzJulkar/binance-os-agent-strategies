"""Supervisor engine: builds the market universe, runs strategies, executes.

The supervisor is venue-agnostic about execution: it calls `execute(signal)`
which is wired to either the live Agent OS MCP client or a paper simulator.
"""
from __future__ import annotations

import time
from decimal import Decimal
from typing import Any

from agent_os.client import AgentOSClient
from agent_os.market import MarketDataClient
from engine.base import Strategy
from engine.log import StrategyLog
from engine.risk import RiskManager, OpenTrade
from engine.signal import Signal


class Supervisor:
    def __init__(self, market: MarketDataClient, client: AgentOSClient | None,
                 risk: RiskManager, log: StrategyLog, config: dict[str, Any],
                 strategies: list[Strategy], paper: bool = False) -> None:
        self.market = market
        self.client = client
        self.risk = risk
        self.log = log
        self.config = config
        self.strategies = strategies
        self.paper = paper
        self._paper_balance = Decimal(config.get("sizing", {}).get("paper_balance", 1000))

    # ---- universe ----
    def build_universe(self) -> dict[str, Any]:
        allowlist = self.config.get("allowlist") or []
        top_n = self.config.get("top_n_pairs", 20)
        quote = self.config.get("quote_asset", "USDT")
        symbols = allowlist if allowlist else self.market.spot_top_pairs()
        futures_symbols = allowlist if allowlist else self.market.futures_top_pairs()
        books = self.market.spot_tickers(symbols)
        futures_books = self.market.futures_tickers(futures_symbols)
        funding = self.market.futures_funding_rates(futures_symbols)
        spot_filters = self.market.spot_filters(symbols)
        futures_filters = self.market.futures_filters(futures_symbols)
        return {
            "quote": quote,
            "spot_symbols": symbols,
            "futures_symbols": futures_symbols,
            "spot_books": books,
            "futures_books": futures_books,
            "funding": funding,
            "spot_filters": spot_filters,
            "futures_filters": futures_filters,
        }

    # ---- execution ----
    def execute(self, sig: Signal) -> dict[str, Any]:
        if self.paper:
            return self._paper_execute(sig)
        if self.client is None:
            raise RuntimeError("No live client wired and paper=False")
        return self._live_execute(sig)

    def _paper_execute(self, sig: Signal) -> dict[str, Any]:
        cost = sig.entry_price * sig.quantity
        if sig.side == "BUY":
            self._paper_balance -= cost
        else:
            self._paper_balance += cost
        self.log.event("ORDER_CONFIRMED", venue=sig.venue, strategy=sig.strategy,
                       symbol=sig.symbol, side=sig.side, price=str(sig.entry_price),
                       qty=str(sig.quantity), mode="paper")
        return {"symbol": sig.symbol, "side": sig.side, "price": str(sig.entry_price),
                "quantity": str(sig.quantity), "status": "FILLED", "mode": "paper"}

    def _live_execute(self, sig: Signal) -> dict[str, Any]:
        """Execute as a MARKET order so it always fills immediately. No resting
        (LIMIT_MAKER/GTX) orders anywhere — the AI trades and the trade completes."""
        cid = f"bos-{int(time.time()*1000)}-{sig.strategy[:6]}"
        if sig.venue == "spot":
            resp = self.client.spot_place_market(sig.symbol, sig.side, str(sig.quantity))
        else:
            resp = self.client.futures_place_market(sig.symbol, sig.side, str(sig.quantity),
                                                    reduce_only=sig.reduce_only)
        self.log.event("ORDER_CONFIRMED", venue=sig.venue, strategy=sig.strategy,
                       symbol=sig.symbol, side=sig.side, price=str(sig.entry_price),
                       qty=str(sig.quantity), order_id=str(resp.get("orderId", "")), mode="live")
        return resp

    # ---- main loop ----
    def run_once(self) -> dict[str, Any]:
        universe = self.build_universe()
        signals: list[Signal] = []
        for strat in self.strategies:
            strat._universe = universe  # noqa: SLF001  (filter lookup)
            try:
                signals.extend(strat.scan(universe))
                signals.extend(strat.manage(universe))
            except Exception as e:  # noqa: BLE001
                self.log.event("STRATEGY_ERROR", strategy=strat.name, error=str(e))
        # Group signals by (venue, symbol): one grid ladder = one open trade,
        # but every order in an opened group still executes.
        groups: dict[tuple[str, str], list[Signal]] = {}
        for sig in signals:
            groups.setdefault((sig.venue, sig.symbol), []).append(sig)
        executed: list[dict[str, Any]] = []
        for (venue, symbol), grp in groups.items():
            if not self.risk.can_open():
                self.log.event("RISK_CAP", symbol=symbol, venue=venue)
                continue
            if self.risk.has(symbol, venue):
                continue
            placed = [self.execute(s) for s in grp]
            executed.extend(placed)
            self.risk.register(OpenTrade(
                venue=venue, symbol=symbol, side=grp[0].side,
                entry_price=min(s.entry_price for s in grp),
                quantity=sum(s.quantity for s in grp),
                strategy=grp[0].strategy,
                order_ids=[str(p.get("orderId", p.get("order_id", ""))) for p in placed],
            ))
        self.log.snapshot(venue="all", mode="paper" if self.paper else "live",
                         open_trades=self.risk.open_count(), executed=len(executed))
        return {"universe": universe, "signals": len(signals), "executed": executed}
