"""Global risk gate shared by all strategies.

Enforces a hard cap on total open trades (spot + futures) and tracks the
current open trade set so strategies do not over-allocate.
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
    quantity: Decimal
    strategy: str
    order_id: str | None = None


class RiskManager:
    def __init__(self, max_open_trades: int = 5) -> None:
        self.max_open_trades = max_open_trades
        self.trades: list[OpenTrade] = []

    def slots_available(self) -> int:
        return max(0, self.max_open_trades - len(self.trades))

    def can_open(self) -> bool:
        return len(self.trades) < self.max_open_trades

    def register(self, trade: OpenTrade) -> None:
        self.trades.append(trade)

    def remove(self, symbol: str, venue: str) -> None:
        self.trades = [t for t in self.trades if not (t.symbol == symbol and t.venue == venue)]

    def has(self, symbol: str, venue: str) -> bool:
        return any(t.symbol == symbol and t.venue == venue for t in self.trades)

    def open_count(self) -> int:
        return len(self.trades)
