"""Live trading terminal for the Binance OS multi-strategy bot.

Tails the live.jsonl log written by the engine/AI and renders a color-coded,
two-column dashboard: open trades, recent orders per strategy, live spreads,
and account snapshot. Launch from PowerShell:

    powershell -ExecutionPolicy Bypass -File terminal\\terminal.ps1
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# ANSI colors
C = {
    "reset": "\033[0m", "bold": "\033[1m", "dim": "\033[2m",
    "red": "\033[91m", "green": "\033[92m", "yellow": "\033[93m",
    "blue": "\033[94m", "magenta": "\033[95m", "cyan": "\033[96m",
    "white": "\033[97m", "grey": "\033[90m", "bg": "\033[40m",
}


def _side_color(side: str) -> str:
    return C["green"] if side.upper() == "BUY" else C["red"]


def clear() -> None:
    sys.stdout.write("\033[2J\033[H")


def render(log_path: str) -> None:
    events = []
    snap = None
    try:
        with open(Path(log_path).expanduser(), encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if rec.get("kind") == "event":
                    events.append(rec)
                elif rec.get("kind") == "snapshot":
                    snap = rec
    except FileNotFoundError:
        snap = None

    events = events[-20:]
    clear()
    w = 60
    line = "=" * (w * 2 + 3)
    print(f"{C['bold']}{C['cyan']}BINANCE AGENT OS — MULTI-STRATEGY LIVE TERMINAL{C['reset']}")
    print(f"{C['dim']}tail: {log_path}{C['reset']}")
    print(line)

    # Left column: open trades / snapshot
    print(f"{C['bold']}{C['yellow']}OPEN TRADES{C['reset']}")
    if snap:
        print(f"  open_trades: {C['bold']}{snap.get('open_trades', '?')}{C['reset']}  "
              f"mode: {C['magenta']}{snap.get('mode', '?')}{C['reset']}")
    else:
        print("  (no snapshot yet — waiting for first cycle)")

    # Right column: recent orders
    print(f"\n{C['bold']}{C['yellow']}RECENT ORDERS (last {len(events)}){C['reset']}")
    if not events:
        print("  (no orders yet)")
    for e in reversed(events):
        ev = e.get("event", "")
        sym = e.get("symbol", "?")
        side = e.get("side", "")
        price = e.get("price", "")
        qty = e.get("qty", "")
        strat = e.get("strategy", "")
        venue = e.get("venue", "")
        sc = _side_color(side)
        if ev == "ORDER_CONFIRMED":
            print(f"  {C['bold']}{sc}{side:<4}{C['reset']} {sym:<12} @ {price:<14} "
                  f"qty {qty:<12} {C['dim']}{strat}/{venue}{C['reset']}")
        elif ev == "RISK_CAP":
            print(f"  {C['yellow']}RISK_CAP{C['reset']} {sym} (max trades reached)")
        elif ev == "STRATEGY_ERROR":
            print(f"  {C['red']}ERROR{C['reset']} {strat}: {e.get('error','')[:50]}")
        else:
            print(f"  {ev} {sym} {side}")

    print(line)
    print(f"{C['dim']}Auto-refresh every 2s. Ctrl+C to exit. "
          f"Run the bot/AI in another terminal to see live orders.{C['reset']}")


def main() -> int:
    log_path = os.environ.get("BINANCE_OS_LOG",
                              str(Path.home() / ".binance-os-strategies" / "logs" / "live.jsonl"))
    while True:
        try:
            render(log_path)
        except Exception as e:  # noqa: BLE001
            clear()
            print(f"{C['red']}terminal error: {e}{C['reset']}")
        time.sleep(2)
    return 0


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"{C['reset']}\nbye")
