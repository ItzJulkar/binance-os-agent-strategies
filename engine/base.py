"""Base class for all strategies."""
from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any

from agent_os.client import AgentOSClient
from agent_os.market import MarketDataClient, SymbolFilter
from engine.log import StrategyLog
from engine.risk import RiskManager
from engine.signal import Signal


class Strategy(ABC):
    """A strategy produces trade signals from market data.

    Subclasses implement `scan()` which is called each refresh cycle. The
    supervisor collects signals, applies the global risk gate, and executes.
    """

    name: str = "base"
    venue: str = "spot"  # default venue; strategies may emit both

    def __init__(self, client: AgentOSClient, market: MarketDataClient,
                 risk: RiskManager, log: StrategyLog, config: dict[str, Any]) -> None:
        self.client = client
        self.market = market
        self.risk = risk
        self.log = log
        self.config = config

    @abstractmethod
    def scan(self, universe: dict[str, Any]) -> list[Signal]:
        """Return signals for the current market snapshot.

        `universe` is a dict keyed by symbol with market data the supervisor
        pre-fetched (books, klines, funding, filters). Strategies may also fetch more.
        """
        raise NotImplementedError

    def manage(self, universe: dict[str, Any]) -> list[Signal]:
        """Optional: manage open trades (TP/SL/grid rebalance). Default none."""
        return []

    # ---- filter-aware order building ----
    def spot_buy(self, symbol: str, price: Decimal, strategy: str | None = None,
                 **extra) -> Signal | None:
        """Build a spot order of ~$6 notional snapped to real tick/lot.

        Returns None if the price level is unplaceable (below min qty/notional).
        """
        flt = self._spot_filter(symbol)
        if flt is None:
            return None
        from agent_os.sizing import snap_price, spot_qty_for_notional
        notional = Decimal(self.config["sizing"]["spot_notional_usd"])
        qty = spot_qty_for_notional(price, notional, flt)
        if qty is None:
            return None
        p = snap_price(price, flt.tick_size)
        if p <= 0:
            return None
        return Signal(strategy=strategy or self.name, venue="spot", symbol=symbol,
                      side="BUY", entry_price=p, quantity=qty, **extra)

    def futures_directional(self, symbol: str, price: Decimal, side: str,
                            balance: Decimal, strategy: str | None = None,
                            **extra) -> Signal | None:
        """Build a futures order = fraction of balance at leverage, snapped."""
        flt = self._futures_filter(symbol)
        if flt is None:
            return None
        from agent_os.sizing import futures_qty_from_balance, snap_price
        cfg = self.config["sizing"]
        qty = futures_qty_from_balance(price, balance,
                                       Decimal(cfg["futures_balance_fraction"]),
                                       Decimal(cfg["futures_leverage"]), flt)
        if qty is None:
            return None
        p = snap_price(price, flt.tick_size)
        if p <= 0:
            return None
        return Signal(strategy=strategy or self.name, venue="futures", symbol=symbol,
                      side=side, entry_price=p, quantity=qty, **extra)

    def _futures_balance(self) -> Decimal:
        """Real futures wallet balance if a live client is wired, else paper."""
        if self.client is not None:
            try:
                acct = self.client.futures_account()
                # accountInformationV3: available balance in 'availableBalance'
                for key in ("availableBalance", "available_balance", "totalWalletBalance"):
                    if key in acct:
                        return Decimal(str(acct[key]))
            except Exception:
                pass
        return Decimal(self.config["sizing"]["paper_balance"])

    def _spot_filter(self, symbol: str) -> SymbolFilter | None:
        flts = getattr(self, "_universe", None) and self._universe.get("spot_filters", {})
        return flts.get(symbol) if flts else None

    def _futures_filter(self, symbol: str) -> SymbolFilter | None:
        flts = getattr(self, "_universe", None) and self._universe.get("futures_filters", {})
        return flts.get(symbol) if flts else None
