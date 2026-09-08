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
        """Default management: close any of this strategy's open trades that hit
        their take-profit or stop-loss. Subclasses may override to add
        strategy-specific exits (e.g. grid range recovery)."""
        exits: list[Signal] = []
        for trade in list(self.risk.trades):
            if trade.strategy != self.name:
                continue
            book = None
            if trade.venue == "spot":
                book = universe.get("spot_books", {}).get(trade.symbol)
            elif trade.venue == "futures":
                book = universe.get("futures_books", {}).get(trade.symbol)
            if not book:
                continue
            # for a BUY, current = bid (what you can sell at); for SELL, ask
            cur = (book.bid if trade.side == "BUY" else book.ask)
            if cur is None or cur <= 0 or trade.entry_price <= 0:
                continue
            chg = (cur - trade.entry_price) / trade.entry_price
            if trade.side == "SELL":
                chg = -chg
            exit_side = "SELL" if trade.side == "BUY" else "BUY"
            hit = False
            if trade.stop_loss_pct is not None and chg <= -trade.stop_loss_pct:
                hit = True
            elif trade.take_profit_pct is not None and chg >= trade.take_profit_pct:
                hit = True
            if hit:
                exits.append(Signal(strategy=self.name, venue=trade.venue,
                                    symbol=trade.symbol, side=exit_side,
                                    entry_price=cur, quantity=trade.quantity,
                                    reduce_only=(trade.venue == "futures")))
        return exits

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

    def atr_stop_tp(self, candles: list) -> tuple[Decimal | None, Decimal | None]:
        """Volatility-based (market-adaptive) stop-loss and take-profit fractions.

        Computed from the symbol's live ATR(14)/price scaled by the config
        multipliers, then clamped to sane bounds. Returns (stop_pct, tp_pct);
        each may be None if that leg is disabled (multiplier 0), in which case
        the caller should fall back to the fixed default.
        """
        from agent_os.indicators import atr_percent
        risk_cfg = self.config.get("risk", {})
        stop_mult = Decimal(str(risk_cfg.get("stop_atr_multiplier", 1.5)))
        tp_mult = Decimal(str(risk_cfg.get("take_profit_atr_multiplier", 3.0)))
        atrp = atr_percent(candles)
        stop = tp = None
        if atrp is not None:
            if stop_mult > 0:
                stop = atrp * stop_mult
                stop = min(max(stop, Decimal(str(risk_cfg.get("stop_min_pct", 0.01)))),
                           Decimal(str(risk_cfg.get("stop_max_pct", 0.08))))
            if tp_mult > 0:
                tp = atrp * tp_mult
                tp = min(tp, Decimal(str(risk_cfg.get("take_profit_max_pct", 0.20))))
        # fall back to fixed defaults for any disabled / unavailable leg
        if stop is None:
            stop = Decimal(str(risk_cfg.get("default_stop_loss_pct", 0.03)))
        if tp is None:
            tp = Decimal(str(risk_cfg.get("default_take_profit_pct", 0.05)))
        return stop, tp

    def _spot_filter(self, symbol: str) -> SymbolFilter | None:
        flts = getattr(self, "_universe", None) and self._universe.get("spot_filters", {})
        return flts.get(symbol) if flts else None

    def _futures_filter(self, symbol: str) -> SymbolFilter | None:
        flts = getattr(self, "_universe", None) and self._universe.get("futures_filters", {})
        return flts.get(symbol) if flts else None
