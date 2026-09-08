from decimal import Decimal

from agent_os.indicators import adx, atr, bollinger, donchian, ema, rsi, sma, volume_ratio
from agent_os.market import Candle


def _mk(prices):
    return [Candle(i, p, p, p, p, Decimal(1)) for i, p in enumerate(prices)]


def test_sma():
    v = [Decimal(i) for i in range(1, 6)]
    out = sma(v, 3)
    assert out[:2] == [None, None]
    assert out[2] == Decimal(2)
    assert out[4] == Decimal(4)


def test_ema_align():
    v = [Decimal(i) for i in range(1, 11)]
    out = ema(v, 3)
    assert len(out) == 10
    assert out[0] is None and out[1] is None
    assert out[2] is not None


def test_rsi_bounds():
    v = [Decimal(i) for i in range(1, 30)]
    out = rsi(v, 14)
    assert all(x is None or (Decimal(0) <= x <= Decimal(100)) for x in out)


def test_atr_positive():
    c = _mk([Decimal(i) for i in range(1, 30)])
    out = atr(c, 14)
    assert out[-1] is not None and out[-1] > 0


def test_bollinger():
    v = [Decimal(i) for i in range(1, 30)]
    u, m, l = bollinger(v, 20)
    assert u[-1] > m[-1] > l[-1]


def test_donchian():
    h = [Decimal(i) for i in range(1, 30)]
    lo = [Decimal(1) for _ in range(29)]
    u, l = donchian(h, lo, 20)
    assert u[-1] == Decimal(29)
    assert l[-1] == Decimal(1)


def test_adx_returns():
    c = _mk([Decimal(i) for i in range(1, 60)])
    out = adx(c, 14)
    assert out[-1] is not None


def test_volume_ratio():
    v = [Decimal(10)] * 25
    v[-1] = Decimal(50)
    assert volume_ratio(v, 20) == Decimal(5)
