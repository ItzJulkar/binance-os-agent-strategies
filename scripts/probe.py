"""Probe all 4 strategies live on real market data. Shows signals or 'no signal',
and flags any runtime error (which would be a bug)."""
import sys, time
from pathlib import Path
from decimal import Decimal
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import yaml

from agent_os.market import MarketDataClient
from engine.log import StrategyLog
from engine.risk import RiskManager

cfg = yaml.safe_load(open(ROOT / "config.yaml"))
m = MarketDataClient(top_n=cfg["markets"]["top_n_pairs"], quote="USDT",
                     min_vol=Decimal(cfg["markets"]["min_quote_volume"]))
log = StrategyLog(ROOT / "_probe.jsonl")
risk = RiskManager(5)
t0 = time.monotonic()

from strategies.grid.strategy import GridStrategy
from strategies.regime_rotation.strategy import RegimeRotationStrategy
from strategies.volume_spike.strategy import VolumeSpikeStrategy
from strategies.funding_rate.strategy import FundingRateStrategy

strats = [
    GridStrategy(None, m, risk, log, cfg),
    RegimeRotationStrategy(None, m, risk, log, cfg),
    VolumeSpikeStrategy(None, m, risk, log, cfg),
    FundingRateStrategy(None, m, risk, log, cfg),
]

# Build universe once
spot_syms = m.spot_top_pairs()
fut_syms = m.futures_top_pairs()
universe = {
    "spot_symbols": spot_syms, "futures_symbols": fut_syms,
    "spot_books": m.spot_tickers(spot_syms), "futures_books": m.futures_tickers(fut_syms),
    "funding": m.futures_funding_rates(fut_syms),
    "spot_filters": m.spot_filters(spot_syms), "futures_filters": m.futures_filters(fut_syms),
}
print(f"universe spot={len(spot_syms)} futures={len(fut_syms)} ({time.monotonic()-t0:.1f}s)")

for s in strats:
    s._universe = universe
    err = None
    try:
        sigs = s.scan(universe)
    except Exception as e:
        sigs, err = [], e
    nm = s.name
    if err:
        print(f"\n== {nm}: RUNTIME ERROR (BUG) ==\n   {type(err).__name__}: {err}")
    else:
        print(f"\n== {nm}: {len(sigs)} signal(s) ==")
        for sg in sigs:
            print(f"   {sg.venue:8} {sg.side:4} {sg.symbol:12} qty {sg.quantity} notional~{sg.entry_price*sg.quantity:.2f}")
        if not sigs:
            print("   (no signal right now — conditions not met)")
log.close()
print(f"\ntotal elapsed {time.monotonic()-t0:.1f}s")
