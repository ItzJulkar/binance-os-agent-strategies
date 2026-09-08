"""Regression tests for the supervisor config wiring (the bugs fixed in the
debug pass): build_universe must read top_n/quote/allowlist from the NESTED
markets section of config.yaml, and futures strategies must fall back to
paper_balance when no live client is wired."""
from decimal import Decimal
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import yaml

from agent_os.market import MarketDataClient, SymbolFilter
from engine.base import Strategy
from engine.log import StrategyLog
from engine.risk import RiskManager
from engine.supervisor import Supervisor


def _cfg():
    c = yaml.safe_load(open(Path(__file__).resolve().parent.parent / "config.yaml"))
    c["markets"]["top_n_pairs"] = 3  # small, and confirms nested key is honored
    return c


def test_build_universe_honors_nested_markets_config():
    """The bug: build_universe read self.config.get('top_n_pairs') which is the
    WRONG key (config nests it under markets.top_n_pairs), so a non-default
    value was silently ignored and it always used 20. This asserts the nested
    config is actually read by monkeypatching the top-pairs fetchers."""
    m = MarketDataClient(top_n=3)
    cfg = _cfg()
    risk = RiskManager(2)
    log = StrategyLog("tests/_cfg.jsonl")
    # stub network calls so no live HTTP in the test
    m.spot_top_pairs = lambda: ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    m.futures_top_pairs = lambda: ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    m.spot_tickers = lambda s: {x: type("T", (), {"bid": Decimal("1"), "ask": Decimal("1.0001")})() for x in s}
    m.futures_tickers = lambda s: {x: type("T", (), {"bid": Decimal("1"), "ask": Decimal("1.0001")})() for x in s}
    m.futures_funding_rates = lambda s: {}
    m.spot_filters = lambda s: {x: SymbolFilter(x, Decimal("0.01"), Decimal("0.01"), Decimal("0.01"), Decimal("5")) for x in s}
    m.futures_filters = lambda s: {x: SymbolFilter(x, Decimal("0.01"), Decimal("0.01"), Decimal("0.01"), Decimal("5")) for x in s}

    class Dummy(Strategy):
        name = "dummy"
        def scan(self, u): return []
    sup = Supervisor(m, None, risk, log, cfg, [Dummy(None, m, risk, log, cfg)], paper=True)
    u = sup.build_universe()
    # config says top_n=3 -> must return exactly 3, proving nested key read
    assert len(u["spot_symbols"]) == 3, f"expected 3 (nested config honored), got {len(u['spot_symbols'])}"
    log.close()


def test_futures_balance_falls_back_to_paper():
    c = _cfg()
    log = StrategyLog("tests/_cfg.jsonl")
    risk = RiskManager(2)
    m = MarketDataClient(top_n=3)
    class Dummy(Strategy):
        name = "dummy"
        def scan(self, u): return []
    d = Dummy(None, m, risk, log, c)  # client=None
    assert d._futures_balance() == Decimal(c["sizing"]["paper_balance"]), \
        "no live client -> must use config paper_balance"
    log.close()
