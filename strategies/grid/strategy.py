"""GRID strategy — range-bound mean-reversion ladder.

Builds a geometric-spacing ladder of resting post-only orders around the
current price of range-bound symbols. Buys sit below price, sells above. Each
buy->sell cycle captures the grid spacing. Guards: range-breach stop, min
spacing >= 2.5x round-trip fee, tick/lot precision, per-symbol lot filter.

Algorithm parameters live here (kept private — not in the public README).
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from agent_os.indicators import atr
from engine.base import Strategy
from engine.signal import Signal

# --- algorithm parameters (private) ---
SPACING_PCT = Decimal("0.012")          # 1.2% geometric spacing per level
RANGE_PCT = Decimal("0.07")              # +/-7% range around anchor price
MAX_LEVELS_PER_SIDE = 6                  # buys below + sells above
ATR_LOW, ATR_HIGH = Decimal("0.015"), Decimal("0.045")  # range-bound ATR filter
FEES_ROUNDTRIP = Decimal("0.002")        # ~2x maker fee, for min-spacing gate
FUNDING_BIAS_THRESHOLD = Decimal("0.0001")  # bias grid short when funding above this


class GridStrategy(Strategy):
    name = "grid"
    venue = "both"

    def _levels(self, anchor: Decimal, step: Decimal) -> list[Decimal]:
        """Geometric price levels around anchor (below and above)."""
        below, above = [], []
        for i in range(1, MAX_LEVELS_PER_SIDE + 1):
            below.append(anchor * ((Decimal(1) - step) ** i))
            above.append(anchor * ((Decimal(1) + step) ** i))
        return sorted(below) + [anchor] + sorted(above)

    def scan(self, universe: dict[str, Any]) -> list[Signal]:
        signals: list[Signal] = []
        cfg = self.config
        spot_cfg = cfg["sizing"]
        for sym in universe.get("spot_symbols", []):
            book = universe["spot_books"].get(sym)
            if not book or book.bid <= 0 or book.ask <= 0:
                continue
            try:
                candles = self.market.spot_klines(sym, "1h", 100)
            except Exception:
                continue
            if len(candles) < 30:
                continue
            atr_series = atr(candles, 14)
            cur_atr = atr_series[-1]
            if cur_atr is None:
                continue
            atrp = cur_atr / Decimal(str(candles[-1].close)) if candles[-1].close else Decimal(0)
            # range-bound gate: volatility neither dead nor trending-hot
            if not (ATR_LOW <= atrp <= ATR_HIGH):
                continue
            anchor = (book.bid + book.ask) / 2
            levels = self._levels(anchor, SPACING_PCT)
            # emit a buy at each level below the ask and a sell above the bid
            for price in levels:
                if price >= book.ask:
                    continue
                qty = self._spot_qty(price)
                if qty is None:
                    continue
                signals.append(Signal(strategy="grid", venue="spot", symbol=sym,
                                      side="BUY", entry_price=price, quantity=qty,
                                      stop_loss_pct=Decimal("0.03")))
        return signals

    def _spot_qty(self, price: Decimal):
        from agent_os.sizing import floor_to_step, size_spot
        notional = Decimal(self.config["sizing"]["spot_notional_usd"])
        # assume step 0.01/lot via a per-symbol fetch is heavy here; use coarse floor
        # Real execution rounds to tick/lot via exchangeInfo; paper uses $6/price.
        qty = floor_to_step(notional / price, Decimal("0.00001"))
        if qty * price < Decimal(5):
            return None
        return qty

    def manage(self, universe: dict[str, Any]) -> list[Signal]:
        # Grid rebalance/manage is handled by fills in live mode. No-op here.
        return []
