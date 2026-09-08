"""Regression test for the exit-management bug.

Previously NO strategy produced exit signals, so the engine opened up to 5
positions and never closed them (no TP/SL, no range recovery) — it froze at the
cap forever. This locks in that manage() emits exit signals and the supervisor
closes a held position and frees the slot.
"""
from decimal import Decimal
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent_os.market import Candle, MarketDataClient, SymbolFilter
from agent_os.sizing import snap_price
from engine.base import Strategy
from engine.log import StrategyLog
from engine.risk import OpenTrade, RiskManager
from engine.supervisor import Supervisor
from strategies.grid.strategy import GridStrategy
from strategies.regime_rotation.strategy import RegimeRotationStrategy

F = SymbolFilter("TESTUSDT", Decimal("0.01"), Decimal("0.01"), Decimal("0.01"), Decimal("5"))
CFG = {"markets": {"top_n_pairs": 3, "quote_asset": "USDT", "allowlist": [], "min_quote_volume": 0},
       "sizing": {"spot_notional_usd": 6, "futures_balance_fraction": 0.05,
                  "futures_leverage": 3, "paper_balance": 1000},
       "strategies": {"enabled": {}}}
CFG["risk"] = {"max_open_trades": 5, "default_stop_loss_pct": 0.03, "default_take_profit_pct": 0.05}


def _book(bid, ask):
    return type("B", (), {"bid": Decimal(str(bid)), "ask": Decimal(str(ask))})()


def _mk_candles(close_path):
    out = []
    prev = Decimal(str(close_path[0]))
    for i, p in enumerate(close_path):
        p = Decimal(str(p))
        h = max(prev, p) * Decimal("1.0005")
        l = min(prev, p) * Decimal("0.9995")
        out.append(Candle(i, prev, h, l, p, Decimal("10")))
        prev = p
    return out


class FakeMarket:
    def __init__(self, candles=None):
        self._candles = candles or _mk_candles([Decimal("100")] * 40)
    def spot_klines(self, *a, **k): return self._candles
    def futures_klines(self, *a, **k): return self._candles
    def futures_funding_history(self, *a, **k): return []


def _universe(book):
    return {"spot_symbols": ["TESTUSDT"], "futures_symbols": [],
            "spot_books": {"TESTUSDT": book}, "futures_books": {},
            "funding": {}, "spot_filters": {"TESTUSDT": F}, "futures_filters": {}}


def test_base_manage_emits_stoploss_exit():
    """A held BUY that has fallen past its stop must produce a SELL exit."""
    risk = RiskManager(5)
    log = StrategyLog("tests/_exit.jsonl")
    # candles: steady then a drop so current book is well below the entry stop
    m = FakeMarket()
    cls = RegimeRotationStrategy  # inherits base manage()
    s = cls(None, m, risk, log, CFG)
    # register an open BUY at 100 with a 3% stop
    risk.register(OpenTrade("spot", "TESTUSDT", "BUY", Decimal("100"), Decimal("0.1"),
                            "regime_rotation", stop_loss_pct=Decimal("0.03")))
    u = _universe(_book("95", "95.1"))  # -5% -> past 3% stop
    s._universe = u
    exits = s.manage(u)
    log.close()
    assert len(exits) == 1, f"expected 1 stop-loss exit, got {len(exits)}"
    assert exits[0].side == "SELL" and exits[0].venue == "spot"


def test_grid_manage_exits_on_range_recovery():
    """Grid must market-sell a held dip-buy once price recovers into the upper
    half of the 20-bar range (its profit leg)."""
    risk = RiskManager(5)
    log = StrategyLog("tests/_exit.jsonl")
    m = FakeMarket(_mk_candles([Decimal("100")] * 25 + [Decimal("110")] * 10))
    s = GridStrategy(None, m, risk, log, CFG)
    risk.register(OpenTrade("spot", "TESTUSDT", "BUY", Decimal("95"), Decimal("0.06"),
                            "grid", stop_loss_pct=None, take_profit_pct=None))
    u = _universe(_book("111", "111.2"))  # well into upper half -> exit
    s._universe = u
    exits = s.manage(u)
    log.close()
    assert len(exits) == 1, f"expected 1 grid recovery exit, got {len(exits)}"
    assert exits[0].side == "SELL"


def test_supervisor_exits_futures_reduceonly_trade():
    """Regression: a FUTURES take-profit exit carries reduce_only=True (the
    execution flag). The supervisor's exit loop must NOT skip it for that reason
    — it must close the position and free the slot."""
    risk = RiskManager(max_open_trades=1)
    log = StrategyLog("tests/_exit.jsonl")
    m = FakeMarket()
    # futures long that has gained well past its take-profit
    risk.register(OpenTrade("futures", "TESTUSDT", "BUY", Decimal("100"), Decimal("1"),
                            "volume_spike", stop_loss_pct=Decimal("0.03"),
                            take_profit_pct=Decimal("0.06")))
    sup = Supervisor(m, None, risk, log, CFG, [], paper=True)
    class VolStrat(Strategy):
        name = "volume_spike"
        def scan(self, u): return []
    vs = VolStrat(None, m, risk, log, CFG)
    sup.strategies = [vs]
    # futures book at 110 -> +10% past 6% take-profit
    sup.build_universe = lambda: {"spot_symbols": [], "futures_symbols": ["TESTUSDT"],
                                  "spot_books": {}, "futures_books": {"TESTUSDT": _book("110", "110.1")},
                                  "funding": {}, "spot_filters": {}, "futures_filters": {"TESTUSDT": F}}
    res = sup.run_once()
    log.close()
    assert risk.open_count() == 0, "futures TP trade must be closed (reduce_only exit executed)"
    assert len(res["executed"]) == 1, f"expected the reduce-only exit to execute, got {len(res['executed'])}"
