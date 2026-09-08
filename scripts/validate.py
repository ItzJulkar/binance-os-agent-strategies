"""DEMO / PLACEABILITY VALIDATION — the closest thing to a live trade test
without real money.

Builds the real top-20 universe (books, funding, filters from Binance public
API), runs every strategy once, and for each emitted order asserts it would be
ACCEPTED by the exchange: qty is a valid multiple of the symbol's stepSize,
qty >= minQty, notional >= minNotional, and price is a valid multiple of
tickSize. Any order failing these would have been rejected live (the LOT_SIZE /
PRICE_FILTER bug class), so this catches it in demo before it costs money.
"""
from __future__ import annotations

import sys
from pathlib import Path
from decimal import Decimal

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402
from agent_os.market import MarketDataClient  # noqa: E402
from engine.log import StrategyLog  # noqa: E402
from engine.risk import RiskManager  # noqa: E402
from strategies.grid.strategy import GridStrategy  # noqa: E402
from strategies.regime_rotation.strategy import RegimeRotationStrategy  # noqa: E402
from strategies.volume_spike.strategy import VolumeSpikeStrategy  # noqa: E402
from strategies.funding_rate.strategy import FundingRateStrategy  # noqa: E402


def valid(filters, sig, venue_key):
    flt = filters.get(sig.symbol)
    if flt is None:
        return False, "no filter for symbol"
    q, p = sig.quantity, sig.entry_price
    checks = []
    # qty multiple of step
    if q <= 0 or (q / flt.step_size) % 1 != 0:
        return False, f"qty {q} not a multiple of step {flt.step_size}"
    if q < flt.min_qty:
        return False, f"qty {q} < minQty {flt.min_qty}"
    if q * p < flt.min_notional:
        return False, f"notional {q*p} < minNotional {flt.min_notional}"
    if p <= 0 or (p / flt.tick_size) % 1 != 0:
        return False, f"price {p} not a multiple of tick {flt.tick_size}"
    return True, "ok"


def main():
    cfg = yaml.safe_load(open(ROOT / "config.yaml"))
    cfg["markets"]["top_n_pairs"] = 20
    market = MarketDataClient(top_n=20, quote="USDT",
                              min_vol=Decimal(cfg["markets"]["min_quote_volume"]))
    log = StrategyLog(ROOT / "tests" / "validate_log.jsonl")
    risk = RiskManager(max_open_trades=5)
    strats = [
        GridStrategy(None, market, risk, log, cfg),
        RegimeRotationStrategy(None, market, risk, log, cfg),
        VolumeSpikeStrategy(None, market, risk, log, cfg),
        FundingRateStrategy(None, market, risk, log, cfg),
    ]
    universe = market.spot_filters()  # warm cache is not enough; build full universe
    # build a full universe like the supervisor does
    spot_syms = market.spot_top_pairs()
    fut_syms = market.futures_top_pairs()
    universe = {
        "spot_symbols": spot_syms,
        "futures_symbols": fut_syms,
        "spot_books": market.spot_tickers(spot_syms),
        "futures_books": market.futures_tickers(fut_syms),
        "funding": market.futures_funding_rates(fut_syms),
        "spot_filters": market.spot_filters(spot_syms),
        "futures_filters": market.futures_filters(fut_syms),
    }
    print(f"universe: spot={len(spot_syms)} futures={len(fut_syms)}")
    all_signals = []
    for strat in strats:
        strat._universe = universe
        sigs = strat.scan(universe)
        all_signals += sigs
        print(f"\n== {strat.name}: {len(sigs)} signal(s) ==")
        for s in sigs:
            filters = universe["futures_filters" if s.venue == "futures" else "spot_filters"]
            ok, why = valid(filters, s, s.venue)
            mark = "PASS" if ok else "FAIL"
            print(f"  [{mark}] {s.venue:7} {s.side:4} {s.symbol:12} @ {s.entry_price} qty {s.quantity}"
                  f" notional~{s.entry_price*s.quantity:.2f}" + (f"  <- {why}" if not ok else ""))
    n_fail = sum(1 for s in all_signals
                 if not valid(universe["futures_filters" if s.venue == "futures" else "spot_filters"],
                              s, s.venue)[0])
    print(f"\nTOTAL signals={len(all_signals)}  UNPLACEABLE={n_fail}")
    log.close()
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
