from decimal import Decimal

from engine.risk import OpenTrade, RiskManager


def test_max_cap():
    r = RiskManager(max_open_trades=2)
    assert r.can_open()
    r.register(OpenTrade("spot", "BTCUSDT", "BUY", Decimal(1), Decimal(1), "grid"))
    r.register(OpenTrade("futures", "ETHUSDT", "BUY", Decimal(1), Decimal(1), "grid"))
    assert not r.can_open()
    assert r.open_count() == 2


def test_remove():
    r = RiskManager(max_open_trades=5)
    r.register(OpenTrade("spot", "BTCUSDT", "BUY", Decimal(1), Decimal(1), "grid"))
    r.remove("BTCUSDT", "spot")
    assert r.open_count() == 0


def test_has():
    r = RiskManager(max_open_trades=5)
    r.register(OpenTrade("spot", "BTCUSDT", "BUY", Decimal(1), Decimal(1), "grid"))
    assert r.has("BTCUSDT", "spot")
    assert not r.has("BTCUSDT", "futures")
