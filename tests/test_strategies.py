"""Strategy regression tests with synthetic candles.

Particularly protects the Donchian-semantics bug: a close can only "break out"
of a channel built from PRIOR bars (a channel that includes the current bar can
never be closed beyond, so the strategy would never fire).
"""
from decimal import Decimal

from agent_os.market import Candle, SymbolFilter
from engine.log import StrategyLog
from engine.risk import RiskManager
from strategies.funding_rate.strategy import FundingRateStrategy
from strategies.grid.strategy import GridStrategy
from strategies.regime_rotation.strategy import RegimeRotationStrategy
from strategies.volume_spike.strategy import VolumeSpikeStrategy

# Realistic filter for a ~$100 asset: tick/step 0.01, minQty 0.01, minNotional 5
F = SymbolFilter("TESTUSDT", Decimal("0.01"), Decimal("0.01"), Decimal("0.01"), Decimal("5"))
CFG = {"sizing": {"spot_notional_usd": 6, "futures_balance_fraction": 0.05,
                  "futures_leverage": 3, "paper_balance": 1000},
       "strategies": {"enabled": {}}}


def _mk(prices, vols, amp_pct=Decimal("0.0005")):
    """Build candles: each bar high/low = price ± amp_pct (intrabar range)."""
    out = []
    prev = Decimal("0")
    for i, p in enumerate(prices):
        o = prev if prev else p
        h = max(o, p) * (Decimal(1) + amp_pct)
        l = min(o, p) * (Decimal(1) - amp_pct)
        out.append(Candle(i, o, h, l, p, vols[i] if i < len(vols) else Decimal("10")))
        prev = p
    return out


def _universe(funding_rate=None, funding_hist=None):
    return {
        "spot_symbols": ["TESTUSDT"], "futures_symbols": ["TESTUSDT"],
        "spot_books": {"TESTUSDT": type("B", (), {"bid": Decimal("100"), "ask": Decimal("100.01")})()},
        "futures_books": {"TESTUSDT": type("B", (), {"bid": Decimal("100"), "ask": Decimal("100.01")})()},
        "funding": ({"TESTUSDT": type("F", (), {"funding_rate": funding_rate})()} if funding_rate is not None else {}),
        "spot_filters": {"TESTUSDT": F}, "futures_filters": {"TESTUSDT": F},
    }


class FakeMarket:
    def __init__(self, spot=None, fut=None, hist=None):
        self.spot = spot or []
        self.fut = fut or []
        self.hist = hist or []

    def spot_klines(self, *a, **k): return self.spot
    def futures_klines(self, *a, **k): return self.fut
    def futures_funding_history(self, *a, **k): return self.hist


def _mk_strategy(cls, market, universe):
    log = StrategyLog("tests/_strat_test.log.jsonl")
    s = cls(None, market, RiskManager(5), log, CFG)
    s._universe = universe
    return s, log


def test_volume_spike_fires_on_prior_channel_break():
    # phase 1: noisy wide-range bars (high ATR), phase 2: 20 calm compressed
    # bars, then a final 12x-volume candle that closes well above the calm
    # prior-20 high.
    prices = [Decimal("100") + Decimal(i) * Decimal("0.01") for i in range(100)]
    prices += [Decimal("101.0")] * 19
    prices += [Decimal("105.0")]  # final breakthrough close
    vols = [Decimal("10")] * 119 + [Decimal("120")]
    candles = _mk(prices, vols, amp_pct=Decimal("0.02"))  # wide intrabar range early
    candles = candles[:-20] + _mk(prices[-20:], [Decimal("10")] * 19 + [Decimal("120")],
                                  amp_pct=Decimal("0.0005"))  # calm window before final
    m = FakeMarket(fut=candles)
    s, log = _mk_strategy(VolumeSpikeStrategy, m, _universe())
    sigs = s.scan(_universe())
    log.close()
    assert len(sigs) == 1, f"expected 1 signal, got {len(sigs)}"
    assert sigs[0].side == "BUY" and sigs[0].venue == "futures"
    q, p = sigs[0].quantity, sigs[0].entry_price
    assert (q / F.step_size) % 1 == 0 and q >= F.min_qty and q * p >= F.min_notional


def test_volume_spike_no_fire_without_spike():
    prices = [Decimal("100") + Decimal(i) * Decimal("0.005") for i in range(120)]
    candles = _mk(prices, [Decimal("10")] * 120)
    s, log = _mk_strategy(VolumeSpikeStrategy, FakeMarket(fut=candles), _universe())
    assert s.scan(_universe()) == []
    log.close()


def test_funding_rate_flip_long():
    hist = [Decimal("-0.0006")] * 5
    m = FakeMarket(fut=_mk([Decimal("100")] * 30, [Decimal("10")] * 30), hist=hist)
    s, log = _mk_strategy(FundingRateStrategy, m, _universe(funding_rate=Decimal("-0.0006")))
    sigs = s.scan(_universe(funding_rate=Decimal("-0.0006")))
    log.close()
    assert len(sigs) == 1 and sigs[0].side == "BUY" and sigs[0].venue == "futures"


def test_funding_rate_flat_no_trade():
    hist = [Decimal("0.0001")] * 5
    m = FakeMarket(fut=_mk([Decimal("100")] * 30, [Decimal("10")] * 30), hist=hist)
    s, log = _mk_strategy(FundingRateStrategy, m, _universe(funding_rate=Decimal("0.0001")))
    assert s.scan(_universe(funding_rate=Decimal("0.0001"))) == []
    log.close()


def test_regime_classify_crash():
    prices = [Decimal("100")]
    for _ in range(60):
        prices.append(prices[-1] * Decimal("1.001"))
    for _ in range(8):  # last 8 bars: -1.5% each => ~ -11% in 24h-window
        prices.append(prices[-1] * Decimal("0.985"))
    candles = _mk(prices, [Decimal("10")] * len(prices))
    s, log = _mk_strategy(RegimeRotationStrategy, FakeMarket(spot=candles), _universe())
    assert s._classify(candles) == "CRASH"
    log.close()


def test_grid_emits_ladder():
    # ±1.2% alternating closes with no extra intrabar range => ATR% ~2.4%,
    # inside the range-bound band [1.5%, 4.5%] the grid trades.
    prices = []
    base = Decimal("100")
    for i in range(100):
        prices.append(base * (Decimal("1.012") if i % 2 else Decimal("0.988")))
    candles = _mk(prices, [Decimal("10")] * 100, amp_pct=Decimal("0.0"))
    m = FakeMarket(spot=candles)
    s, log = _mk_strategy(GridStrategy, m, _universe())
    sigs = s.scan(_universe())
    log.close()
    assert len(sigs) >= 2, f"grid should emit a ladder of buys, got {len(sigs)}"
    for sg in sigs:
        assert sg.venue == "spot" and sg.side == "BUY"
