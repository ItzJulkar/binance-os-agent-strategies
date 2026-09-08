"""FUNDING-RATE strategy (Binance USDT-M perps) — directional flip.

Exploits extreme funding as a crowded-position signal. When shorts are crowded
(funding very negative), go LONG to collect funding from shorts and ride the
short-squeeze reversion toward spot. When longs are crowded (funding very
positive), go SHORT to collect from longs and ride the unwind. Mean-reversion
bet on funding normalizing to ~0.

A "delta-neutral cash-and-carry" is intentionally NOT used here: the user's
sizing caps (spot $6 only, perp 5% of balance @ 3x) cannot build an equal-leg
hedge, so a harvest would just be an oversized unhedged short. Directional
flip respects the caps and the 5-open-trade limit with one position per pair.

Algorithm parameters are private.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from engine.base import Strategy
from engine.signal import Signal

FLIP = Decimal("0.0005")          # |funding| per 8h to trigger (0.05%)
SUSTAINED = Decimal("0.0004")     # must have been at/above for lookback settles
LOOKBACK = 3                      # consecutive settlements to confirm (24h)
REVERT = Decimal("0.0001")        # close when funding reverts to ~zero


class FundingRateStrategy(Strategy):
    name = "funding_rate"
    venue = "futures"

    def scan(self, universe: dict[str, Any]) -> list[Signal]:
        signals: list[Signal] = []
        for sym in universe.get("futures_symbols", []):
            f = universe.get("funding", {}).get(sym)
            if not f:
                continue
            hist = self._history(sym)
            if len(hist) < LOOKBACK:
                continue
            rate = f.funding_rate
            recent = hist[-LOOKBACK:]
            if rate <= -FLIP and all(h <= -SUSTAINED for h in recent):
                sig = self._flip(sym, "BUY", universe)
            elif rate >= FLIP and all(h >= SUSTAINED for h in recent):
                sig = self._flip(sym, "SELL", universe)
            else:
                sig = None
            if sig:
                signals.append(sig)
        return signals

    def _history(self, sym: str) -> list[Decimal]:
        try:
            return self.market.futures_funding_history(sym, LOOKBACK + 2)
        except Exception:
            return []

    def _flip(self, sym: str, side: str, universe: dict) -> Signal | None:
        book = universe.get("futures_books", {}).get(sym)
        if not book:
            return None
        price = book.ask if side == "BUY" else book.bid
        if price is None or price <= 0:
            return None
        balance = Decimal(self.config["sizing"]["paper_balance"])
        return self.futures_directional(sym, price, side, balance,
                                        stop_loss_pct=Decimal("0.03"),
                                        take_profit_pct=Decimal("0.06"))
