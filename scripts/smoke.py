"""Quick smoke test: run all strategies once against real public data in paper mode."""
import sys, time
from pathlib import Path
from decimal import Decimal
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import yaml

from agent_os.market import MarketDataClient
from engine.log import StrategyLog
from engine.risk import RiskManager
from engine.supervisor import Supervisor

cfg = yaml.safe_load(open(ROOT / "config.yaml"))
cfg["markets"]["top_n_pairs"] = 6  # small universe for speed

market = MarketDataClient(top_n=cfg["markets"]["top_n_pairs"],
                          quote=cfg["markets"]["quote_asset"],
                          min_vol=Decimal(cfg["markets"]["min_quote_volume"]))
risk = RiskManager(max_open_trades=cfg["risk"]["max_open_trades"])
log = StrategyLog(ROOT / "tests" / "smoke_live.jsonl")

from strategies.grid.strategy import GridStrategy
from strategies.regime_rotation.strategy import RegimeRotationStrategy
from strategies.volume_spike.strategy import VolumeSpikeStrategy
from strategies.funding_rate.strategy import FundingRateStrategy
strats = [GridStrategy(None, market, risk, log, cfg),
          RegimeRotationStrategy(None, market, risk, log, cfg),
          VolumeSpikeStrategy(None, market, risk, log, cfg),
          FundingRateStrategy(None, market, risk, log, cfg)]
sup = Supervisor(market, None, risk, log, cfg, strats, paper=True)
t0 = time.monotonic()
res = sup.run_once()
print(f"OK in {time.monotonic()-t0:.1f}s signals={res['signals']} executed={len(res['executed'])}")
print("log tail:")
import json
for line in open(ROOT/"tests"/"smoke_live.jsonl", encoding="utf-8").read().strip().splitlines()[-8:]:
    print(" ", line[:160])
log.close()
