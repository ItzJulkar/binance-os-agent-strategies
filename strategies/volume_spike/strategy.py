"""VOLUME-SPIKE BREAKOUT strategy.

Enters only when three things align on the same candle:
  1. VOLUME SPIKE: current volume >= RVOL threshold x its 20-bar average
  2. PRICE BREAKOUT: candle closes outside a Donchian(20) envelope
  3. VOLATILITY COMPRESSION: ATR(14) < its own 20-bar SMA (coiling before break)

The volume surge is the primary filter separating a real breakout from a
low-volume fakeout. Long on an upside break, short on a downside break.

Algorithm params are private.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from agent_os.indicators import atr, donchian, sma
from engine.base import Strategy
from engine.signal import Signal

RVOL_ENTRY = Decimal("2.0")            # entry-grade volume spike
ATR_COMPRESSION = Decimal("1.0")       # require ATR < SMA(ATR,20) before break
DONCHIAN_PERIOD = 20
VOL_SMA_PERIOD = 20
ATR_PERIOD = 14
ATR_STOP_MULT = Decimal("1.5")         # stop distance in ATR
MIN_CANDLES = 60


class VolumeSpikeStrategy(Strategy):
    name = "volume_spike"
    venue = "both"

    def scan(self, universe: dict[str, Any]) -> list[Signal]:
        signals: list[Signal] = []
        cfg = self.config
        # prefer futures for this directional strategy; fall back to spot symbols
        symbols = universe.get("futures_symbols") or universe.get("spot_symbols", [])
        for sym in symbols:
            try:
                candles = self.market.futures_klines(sym, "1h", 120)
            except Exception:
                continue
            if len(candles) < MIN_CANDLES:
                continue
            sig = self._detect(sym, candles, cfg)
            if sig:
                signals.append(sig)
        return signals

    def _detect(self, sym: str, candles: list, cfg: dict):
        vols = [c.volume for c in candles]
        closes = [c.close for c in candles]
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        # volume spike
        vol_sma = sma(vols, VOL_SMA_PERIOD)[-1]
        if vol_sma is None or vol_sma <= 0:
            return None
        rvol = vols[-1] / vol_sma
        if rvol < RVOL_ENTRY:
            return None
        # ATR compression
        atr_s = atr(candles, ATR_PERIOD)
        atr_last = atr_s[-1]
        atr_sma = sma([a for a in atr_s if a is not None], 20)
        if atr_last is None or atr_sma is None or atr_last >= atr_sma:
            return None
        # Donchian breakout
        u, lo = donchian(highs, lows, DONCHIAN_PERIOD)
        if u[-1] is None:
            return None
        last = candles[-1].close
        side = None
        if last > u[-1]:
            side = "BUY"
        elif last < lo[-1]:
            side = "SELL"
        if side is None:
            return None
        # funding sanity for longs (skip if extreme positive / crowded)
        funding = self._funding(sym, universe)
        if side == "BUY" and funding is not None and funding > Decimal("0.0005"):
            return None
        # sizing: futures 5% balance @ 3x notional
        book = universe.get("futures_books", {}).get(sym)
        price = book.ask if side == "BUY" and book else last
        if side == "SELL":
            price = book.bid if book and book.bid > 0 else last
        if not book:
            return None
        bal = self._futures_balance(cfg)
        from agent_os.sizing import size_futures
        qty = size_futures(price, bal, Decimal(cfg["sizing"]["futures_balance_fraction"]),
                           Decimal(cfg["sizing"]["futures_leverage"]),
                           Decimal("0.00001"), Decimal("0.001"), Decimal("5"))
        if qty is None:
            return None
        return Signal(strategy="volume_spike", venue="futures", symbol=sym, side=side,
                      entry_price=price, quantity=qty,
                      stop_loss_pct=Decimal("0.03"), take_profit_pct=Decimal("0.06"))

    def _funding(self, sym: str, universe) -> Decimal | None:
        f = universe.get("funding", {}).get(sym)
        return f.funding_rate if f else None

    def _futures_balance(self, cfg: dict) -> Decimal:
        # paper default; live reads from account
        return Decimal(cfg.get("paper_balance", 1000))
