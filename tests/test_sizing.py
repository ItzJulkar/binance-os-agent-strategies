from decimal import Decimal

from agent_os.market import SymbolFilter
from agent_os.sizing import (
    floor_to_step,
    futures_qty_from_balance,
    futures_qty_for_notional,
    snap_price,
    spot_qty_for_notional,
)

# BTC-like filter: tick 0.01, step 0.00001, minQty 0.00001, minNotional 5
BTC = SymbolFilter("BTCUSDT", Decimal("0.01"), Decimal("0.00001"),
                   Decimal("0.00001"), Decimal("5"))


def test_floor_to_step():
    assert floor_to_step(Decimal("27.1728"), Decimal("0.1")) == Decimal("27.1")
    assert floor_to_step(Decimal("30.969"), Decimal("1")) == Decimal("30")
    assert floor_to_step(Decimal("0.022977"), Decimal("0.001")) == Decimal("0.022")


def test_snap_price():
    # rounds to nearest tick (0.01)
    assert snap_price(Decimal("78826.314"), Decimal("0.01")) == Decimal("78826.31")
    # exact multiple unchanged
    assert snap_price(Decimal("100.00"), Decimal("0.01")) == Decimal("100.00")


def test_spot_qty_for_notional():
    # DOGE-like: price 0.0908, step 1.0 -> $6/0.0908 = 66 units (floored to step)
    doge = SymbolFilter("DOGEUSDT", Decimal("0.00001"), Decimal("1"),
                        Decimal("1"), Decimal("1"))
    q = spot_qty_for_notional(Decimal("0.0908"), Decimal("6"), doge)
    assert q == Decimal("66")
    # BTC: $6/78826 ~ 0.000076, floor to step 0.00001
    q = spot_qty_for_notional(Decimal("78826"), Decimal("6"), BTC)
    assert q == Decimal("0.00007")
    # below minNotional -> None (expensive asset, tiny qty not enough notional)
    assert spot_qty_for_notional(Decimal("100000000"), Decimal("6"), BTC) is None


def test_futures_qty_from_balance():
    # 5% of 1000 @3x = notional 150 at price 78826 -> qty 0.00190 (floored)
    q = futures_qty_from_balance(Decimal("78826"), Decimal("1000"),
                                 Decimal("0.05"), 3, BTC)
    assert q == Decimal("0.00190")
    # too-small balance -> None
    assert futures_qty_from_balance(Decimal("78826"), Decimal("1"),
                                    Decimal("0.05"), 3, BTC) is None


def test_futures_qty_for_notional():
    q = futures_qty_for_notional(Decimal("78826"), Decimal("150"), BTC)
    assert q == Decimal("0.00190")
