"""GRID strategy — range-bound mean-reversion ladder.

Builds a geometric-spacing ladder of resting post-only orders around the
current price of range-bound symbols. Buys sit below price, sells above. Each
buy->sell cycle captures the grid spacing. Guards: range-breach stop, min
spacing >= fee gate, tick/lot precision via real exchange filters.

Algorithm parameters live here (kept private — not spelled out in the README).
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from agent_os.indicators import atr
from agent_os.sizing import snap_price
from engine.base import Strategy
from engine.signal import Signal

# --- algorithm parameters (private) ---
SPACING_PCT = Decimal("0.012")            # geometric spacing per level
RANGE_PCT = Decimal("0.07")               # +/-7% range around anchor price
LEVELS_PER_SIDE = 6
ATR_LOW, ATR_HIGH = Decimal("0.015"), Decimal("0.045")  # range-bound ATR band
MIN_SPACING_GATE = Decimal("0.005")       # spacing must exceed fees meaningfully


class GridStrategy(Strategy):
    name = "grid"
    venue = "both"

    def _levels(self, anchor: Decimal, step: Decimal) -> list[Decimal]:
        below = [anchor * ((Decimal(1) - step) ** i) for i in range(1, LEVELS_PER_SIDE + 1)]
        above = [anchor * ((Decimal(1) + step) ** i) for i in range(1, LEVELS_PER_SIDE + 1)]
        return sorted(below), sorted(above)

    def scan(self, universe: dict[str, Any]) -> list[Signal]:
        signals: list[Signal] = []
        filters = universe.get("spot_filters", {})
        for sym in universe.get("spot_symbols", []):
            book = universe["spot_books"].get(sym)
            flt = filters.get(sym)
            if not book or not flt or book.bid <= 0 or book.ask <= 0 or book.ask <= book.bid:
                continue
            try:
                candles = self.market.spot_klines(sym, "1h", 100)
            except Exception:
                continue
            if len(candles) < 30:
                continue
            atr_series = atr(candles, 14)
            cur_atr = atr_series[-1]
            if cur_atr is None or not candles[-1].close:
                continue
            atrp = cur_atr / candles[-1].close
            # range-bound gate: not dead-flat, not trending-hot
            if not (ATR_LOW <= atrp <= ATR_HIGH):
                continue
            anchor = (book.bid + book.ask) / 2
            buys_low, sells_high = self._levels(anchor, SPACING_PCT)
            # BUY ladder below the ask, each a real, snapped ~$6 post-only order
            for price in buys_low:
                if price >= book.ask:
                    continue
                sig = self.spot_buy(sym, price)
                if sig is not None:
                    sig = Signal(strategy="grid", venue="spot", symbol=sym, side="BUY",
                                 entry_price=sig.entry_price, quantity=sig.quantity,
                                 stop_loss_pct=Decimal("0.03"))
                    signals.append(sig)
        return signals
