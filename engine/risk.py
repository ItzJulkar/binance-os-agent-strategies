"""Global risk gate shared by all strategies.

An "open trade" is a distinct (venue, symbol) position. A grid ladder on one
symbol is a single open trade (all its resting levels place together), so the
max-open-trades cap bounds the number of symbols held, not the number of
resting orders within a grid.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class OpenTrade:
    venue: str            # "spot" | "futures"
    symbol: str
    side: str             # "BUY" | "SELL"
    entry_price: Decimal
    quantity: Decimal     # total across ladder
    strategy: str
    order_ids: list[str] | None = None


class RiskManager:
    def __init__(self, max_open_trades: int = 5) -> None:
        self.max_open_trades = max_open_trades
        self.trades: list[OpenTrade] = []

    @staticmethod
    def _key(venue: str, symbol: str) -> tuple[str, str]:
        return (venue, symbol)

    def slots_available(self) -> int:
        return max(0, self.max_open_trades - len(self.trades))

    def can_open(self) -> bool:
        return len(self.trades) < self.max_open_trades

    def has(self, symbol: str, venue: str) -> bool:
        return any(t.symbol == symbol and t.venue == venue for t in self.trades)

    def register(self, trade: OpenTrade) -> None:
        if not self.has(trade.symbol, trade.venue):
            self.trades.append(trade)

    def remove(self, symbol: str, venue: str) -> None:
        self.trades = [t for t in self.trades if not (t.symbol == symbol and t.venue == venue)]

    def open_count(self) -> int:
        return len(self.trades)
