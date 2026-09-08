"""GRID strategy — range mean-reversion, MARKET execution.

The grid trades a RANGE defined by the recent 20-bar high/low of a symbol. It
takes a MARKET BUY when price is in the LOWER half of that range (buy the dip)
and (via the prompt's lifecycle) MARKET-SELLS when price reaches the upper half
again. Everything fills at market — no resting/ladder orders. One open trade
per symbol (max 5 symbols), enforced by the risk layer.

Algorithm parameters live here (kept private).
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from agent_os.indicators import atr
from engine.base import Strategy
from engine.signal import Signal

# --- algorithm parameters (private) ---
ATR_LOW, ATR_HIGH = Decimal("0.015"), Decimal("0.045")  # range-bound ATR band
RANGE_LOOKBACK = 20                 # bars for the high/low range
LOWER_HALF_BUFFER = Decimal("1.00") # buy when price <= buffer x range mid


class GridStrategy(Strategy):
    name = "grid"
    venue = "spot"

    def scan(self, universe: dict[str, Any]) -> list[Signal]:
        """One MARKET BUY per symbol trading in the lower half of its range."""
        signals: list[Signal] = []
        filters = universe.get("spot_filters", {})
        for sym in universe.get("spot_symbols", []):
            book = universe["spot_books"].get(sym)
            flt = filters.get(sym)
            if not book or not flt or book.ask <= 0:
                continue
            try:
                candles = self.market.spot_klines(sym, "1h", 60)
            except Exception:
                continue
            if len(candles) < 30:
                continue
            atr_series = atr(candles, 14)
            cur_atr = atr_series[-1]
            if cur_atr is None or not candles[-1].close:
                continue
            atrp = cur_atr / candles[-1].close
            # only a range-bound symbol (not dead-flat, not trending-hot)
            if not (ATR_LOW <= atrp <= ATR_HIGH):
                continue
            # recent range high/low (PRIOR bars, so price can trade at the edges)
            window = candles[-(RANGE_LOOKBACK + 1):-1]
            if len(window) < RANGE_LOOKBACK:
                continue
            hi = max(c.high for c in window)
            lo = min(c.low for c in window)
            if hi <= lo:
                continue
            mid_range = (hi + lo) / 2
            # buy the dip: price is at/below the lower half of the range
            if book.ask <= mid_range * LOWER_HALF_BUFFER:
                sig = self.spot_buy(sym, book.ask,
                                    stop_loss_pct=Decimal("0.03"),
                                    take_profit_pct=Decimal("0.04"))
                if sig:
                    signals.append(sig)
        return signals

    def manage(self, universe: dict[str, Any]) -> list[Signal]:
        # Market-sell exits on recovery / TP / SL are driven by the AI lifecycle
        # in the prompt; the risk layer tracks the open symbol.
        return []
