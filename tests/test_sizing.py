from decimal import Decimal

from agent_os.sizing import floor_to_step, size_futures, size_spot


def test_floor_to_step():
    assert floor_to_step(Decimal("27.1728"), Decimal("0.1")) == Decimal("27.1")
    assert floor_to_step(Decimal("30.969"), Decimal("1")) == Decimal("30")
    assert floor_to_step(Decimal("0.022977"), Decimal("0.001")) == Decimal("0.022")


def test_size_spot():
    q = size_spot(Decimal("0.2204"), Decimal("6"), Decimal("0.1"),
                  Decimal("0.1"), Decimal("5"))
    assert q == Decimal("27.2")
    # below min notional -> None
    assert size_spot(Decimal("100000"), Decimal("6"), Decimal("0.001"),
                     Decimal("0.001"), Decimal("5")) is None


def test_size_futures():
    q = size_futures(Decimal("60000"), Decimal("1000"), Decimal("0.05"),
                     3, Decimal("0.001"), Decimal("0.001"), Decimal("5"))
    # notional = 1000*0.05*3 = 150 -> qty 0.002
    assert q == Decimal("0.002")
