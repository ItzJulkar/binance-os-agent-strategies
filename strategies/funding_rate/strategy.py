"""FUNDING-RATE strategy (Binance USDT-M perps).

Two mutually-exclusive regimes driven by the 8h funding rate:
  A) DIRECTIONAL FLIP (mean-reversion): extreme funding = crowded positioning.
     Long when funding very negative (shorts crowded), short when very positive.
     Collect funding while price reverts toward spot.
  B) CASH-AND-CARRY HARVEST (delta-neutral): funding positive-but-stable, buy
     spot + short the perp of equal notional to collect funding each settlement.

Only one regime active per symbol. Algorithm params are private.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from engine.base import Strategy
from engine.signal import Signal

# funding fractions are per-8h; e.g. 0.0005 = 0.05%/8h
FLIP_THRESHOLD = Decimal("0.0005")        # |funding| to trigger directional flip
SUSTAINED = Decimal("0.0004")             # min sustained magnitude
LOOKBACK = 3                               # consecutive settlements to confirm
HARVEST_MIN = Decimal("0.0001")
HARVEST_MAX = Decimal("0.0003")
EXIT_REVERT = Decimal("0.0001")


class FundingRateStrategy(Strategy):
    name = "funding_rate"
    venue = "both"

    def scan(self, universe: dict[str, Any]) -> list[Signal]:
        signals: list[Signal] = []
        cfg = self.config
        for sym in universe.get("futures_symbols", []):
            f = universe.get("funding", {}).get(sym)
            if not f:
                continue
            rate = f.funding_rate
            history = self._funding_history(sym)
            # sustained check over last N settlements
            recent = [r for r in history[-LOOKBACK:]]
            if len(recent) < LOOKBACK:
                continue
            # Regime A: directional flip
            if rate <= -FLIP_THRESHOLD and all(r <= -SUSTAINED for r in recent):
                sig = self._directional(sym, "BUY", f, cfg, universe)
                if sig:
                    signals.append(sig)
            elif rate >= FLIP_THRESHOLD and all(r >= SUSTAINED for r in recent):
                sig = self._directional(sym, "SELL", f, cfg, universe)
                if sig:
                    signals.append(sig)
            # Regime B: cash-and-carry harvest (spot long + perp short)
            elif HARVEST_MIN <= rate <= HARVEST_MAX:
                sigs = self._harvest(sym, f, cfg, universe)
                signals.extend(sigs)
        return signals

    def _funding_history(self, sym: str) -> list[Decimal]:
        try:
            return self.market.futures_funding_history(sym, LOOKBACK + 2)
        except Exception:
            return []

    def _directional(self, sym, side, f, cfg, universe):
        from agent_os.sizing import size_futures
        book = universe.get("futures_books", {}).get(sym)
        price = book.ask if side == "BUY" and book else (book.bid if book else None)
        if price is None or price <= 0:
            return None
        bal = Decimal(cfg.get("paper_balance", 1000))
        qty = size_futures(price, bal, Decimal(cfg["sizing"]["futures_balance_fraction"]),
                           Decimal(cfg["sizing"]["futures_leverage"]),
                           Decimal("0.00001"), Decimal("0.001"), Decimal("5"))
        if qty is None:
            return None
        return Signal(strategy="funding_rate", venue="futures", symbol=sym, side=side,
                      entry_price=price, quantity=qty,
                      stop_loss_pct=Decimal("0.03"))

    def _harvest(self, sym, f, cfg, universe):
        """Spot BUY + futures SELL of equal notional (delta-neutral)."""
        from agent_os.sizing import size_futures, size_spot
        book = universe.get("spot_books", {}).get(sym)
        fbook = universe.get("futures_books", {}).get(sym)
        if not book or not fbook:
            return []
        spot_notional = Decimal(cfg["sizing"]["spot_notional_usd"])
        spot_qty = size_spot(fbook.bid, spot_notional, Decimal("0.00001"),
                             Decimal("0.001"), Decimal("5"))
        if spot_qty is None:
            return []
        bal = Decimal(cfg.get("paper_balance", 1000))
        # short perp matching spot notional
        perp_qty = size_futures(fbook.bid, bal, Decimal(cfg["sizing"]["futures_balance_fraction"]),
                                Decimal(cfg["sizing"]["futures_leverage"]),
                                Decimal("0.00001"), Decimal("0.001"), Decimal("5"))
        sigs = []
        if spot_qty:
            sigs.append(Signal(strategy="funding_rate", venue="spot", symbol=sym,
                               side="BUY", entry_price=fbook.ask, quantity=spot_qty))
        if perp_qty:
            sigs.append(Signal(strategy="funding_rate", venue="futures", symbol=sym,
                               side="SELL", entry_price=fbook.bid, quantity=perp_qty,
                               reduce_only=False))
        return sigs
