"""Position sizing for spot and perpetual futures.

Spot  : fixed notional per order (default $6).
Futures: fraction of the futures wallet balance per entry, at fixed leverage.
"""
from __future__ import annotations

from decimal import ROUND_DOWN, Decimal


def floor_to_step(value: Decimal, step: Decimal) -> Decimal:
    if step <= 0:
        return value
    return (value / step).to_integral_value(rounding=ROUND_DOWN) * step


def size_spot(price: Decimal, notional_usd: Decimal, step_size: Decimal,
              min_qty: Decimal, min_notional: Decimal) -> Decimal | None:
    """Quantity for a spot order of fixed notional. None if below filters."""
    qty = floor_to_step(notional_usd / price, step_size)
    if qty < min_qty or qty * price < min_notional:
        return None
    return qty


def size_futures(price: Decimal, balance: Decimal, balance_fraction: Decimal,
                 leverage: int, step_size: Decimal, min_qty: Decimal,
                 min_notional: Decimal) -> Decimal | None:
    """Quantity for a futures order: fraction of balance * leverage notional."""
    notional = balance * balance_fraction * Decimal(leverage)
    qty = floor_to_step(notional / price, step_size)
    if qty < min_qty or qty * price < min_notional:
        return None
    return qty
