"""CLI entry point for the Binance Agent OS multi-strategy bot.

Usage:
  python -m scripts.run --paper --cycles 3
  python -m scripts.run --live --cycles 1
  python -m scripts.run --strategies grid,funding_rate --paper
"""
from __future__ import annotations

import argparse
import sys
import time
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402

from agent_os.market import MarketDataClient  # noqa: E402
from engine.log import StrategyLog  # noqa: E402
from engine.risk import RiskManager  # noqa: E402
from engine.supervisor import Supervisor  # noqa: E402


def load_config() -> dict:
    cfg_path = ROOT / "config.yaml"
    with open(cfg_path) as f:
        return yaml.safe_load(f)


def build_strategies(cfg: dict, market, client, risk, log, names: list[str]):
    from strategies.grid.strategy import GridStrategy
    from strategies.regime_rotation.strategy import RegimeRotationStrategy
    from strategies.volume_spike.strategy import VolumeSpikeStrategy
    from strategies.funding_rate.strategy import FundingRateStrategy

    registry = {
        "grid": GridStrategy,
        "regime_rotation": RegimeRotationStrategy,
        "volume_spike": VolumeSpikeStrategy,
        "funding_rate": FundingRateStrategy,
    }
    enabled = cfg["strategies"]["enabled"]
    out = []
    for name in names:
        if not enabled.get(name, False):
            continue
        out.append(registry[name](client, market, risk, log, cfg))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Binance Agent OS multi-strategy bot")
    ap.add_argument("--paper", action="store_true", help="Paper mode (no real orders)")
    ap.add_argument("--live", action="store_true", help="Live mode (Agent OS MCP orders)")
    ap.add_argument("--cycles", type=int, default=1)
    ap.add_argument("--refresh", type=int, default=None)
    ap.add_argument("--strategies", type=str, default="")
    args = ap.parse_args()

    cfg = load_config()
    if args.refresh:
        cfg["execution"]["refresh_seconds"] = args.refresh
    if args.strategies:
        cfg["strategies"]["enabled"] = {k: (k in args.strategies.split(",")) for k in
                                        cfg["strategies"]["enabled"]}

    market = MarketDataClient(
        top_n=cfg["markets"]["top_n_pairs"],
        quote=cfg["markets"]["quote_asset"],
        min_vol=Decimal(cfg["markets"]["min_quote_volume"]),
    )
    risk = RiskManager(max_open_trades=cfg["risk"]["max_open_trades"])
    log_path = cfg["terminal"]["demo_log" if args.paper else "live_log"]
    log = StrategyLog(log_path)

    client = None
    if args.live:
        from agent_os.client import AgentOSClient
        from agent_os.mcp import make_mcp_call
        client = AgentOSClient(make_mcp_call(cfg))

    names = [n for n, on in cfg["strategies"]["enabled"].items() if on]
    strategies = build_strategies(cfg, market, client, risk, log, names)
    sup = Supervisor(market, client, risk, log, cfg, strategies, paper=args.paper)

    print(f"mode={'PAPER' if args.paper else 'LIVE'} strategies={names}")
    for i in range(args.cycles):
        t0 = time.monotonic()
        res = sup.run_once()
        print(f"cycle={i+1}/{args.cycles} signals={res['signals']} executed={len(res['executed'])} "
              f"open={risk.open_count()} elapsed={time.monotonic()-t0:.2f}s")
        if i + 1 < args.cycles:
            time.sleep(cfg["execution"]["refresh_seconds"])
    log.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
