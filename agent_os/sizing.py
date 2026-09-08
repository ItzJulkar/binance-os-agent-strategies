"""Exchange-filter-aware position sizing and order building.

Every order's quantity is snapped to the pair's REAL stepSize and rejected if
it falls below minQty or minNotional — so nothing generated here can be
rejected by Binance for LOT_SIZE / MIN_NOTIONAL, which is the most common bug
in exchange bots (orders rejected for precision).

All rounding is done with Decimal to avoid float drift.
"""
from __future__ import annotations

from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

from agent_os.market import SymbolFilter


def snap_price(price: Decimal, tick: Decimal) -> Decimal:
    """Round price to the nearest valid tick multiple."""
    if tick <= 0:
        return price
    return (price / tick).to_integral_value(rounding=ROUND_HALF_UP) * tick


def floor_to_step(value: Decimal, step: Decimal) -> Decimal:
    if step <= 0:
        return value
    return (value / step).to_integral_value(rounding=ROUND_DOWN) * step


def spot_qty_for_notional(price: Decimal, notional_usd: Decimal, flt: SymbolFilter) -> Decimal | None:
    """Quantity to spend ~notional_usd on a spot order. None if unplaceable."""
    qty = floor_to_step(notional_usd / price, flt.step_size)
    if qty < flt.min_qty:
        return None
    if qty * price < flt.min_notional:
        return None
    return qty


def futures_qty_for_notional(price: Decimal, notional: Decimal, flt: SymbolFilter) -> Decimal | None:
    """Quantity whose notional ~= given value on a futures order. None if unplaceable."""
    qty = floor_to_step(notional / price, flt.step_size)
    if qty < flt.min_qty:
        return None
    if qty * price < flt.min_notional:
        return None
    return qty


def futures_qty_from_balance(price: Decimal, balance: Decimal, balance_fraction: Decimal,
                             leverage: int, flt: SymbolFilter) -> Decimal | None:
    """Futures qty for `balance_fraction` of balance as margin at `leverage`.

    notional = balance * fraction * leverage.
    """
    notional = balance * balance_fraction * Decimal(leverage)
    return futures_qty_for_notional(price, notional, flt)


def snap_to_tick(price: Decimal, flt: SymbolFilter) -> Decimal:
    return snap_price(price, flt.tick_size)
