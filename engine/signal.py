"""Trade signal produced by a strategy."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Signal:
    strategy: str
    venue: str          # "spot" | "futures"
    symbol: str
    side: str           # "BUY" | "SELL"
    entry_price: Decimal
    quantity: Decimal
    # Optional risk per trade (fraction of entry price)
    stop_loss_pct: Decimal | None = None
    take_profit_pct: Decimal | None = None
    reduce_only: bool = False
    # Grid strategies may pass a whole ladder of orders
    ladder: list[tuple[Decimal, Decimal]] | None = None  # (price, qty) pairs
