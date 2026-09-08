"""VOLUME-SPIKE BREAKOUT strategy.

Enters only when three things align on the same 1h candle:
  1. VOLUME SPIKE: current volume >= RVOL x its 20-bar average
  2. PRICE BREAKOUT: candle closes outside a Donchian(20) envelope
  3. VOLATILITY COMPRESSION: ATR(14) < its own 20-bar SMA (coiling before break)

The volume surge separates a genuine breakout from a low-volume fakeout.
Long on upside break, short on downside break. Runs on futures (5% balance @
3x) and can fall back to spot.

Algorithm parameters are private.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from agent_os.indicators import atr, donchian, sma
from engine.base import Strategy
from engine.signal import Signal

RVOL_ENTRY = Decimal("2.0")
DONCHIAN_PERIOD = 20
VOL_PERIOD = 20
ATR_PERIOD = 14
FUNDING_LONG_SKIP = Decimal("0.0005")   # skip crowded long if funding very positive


class VolumeSpikeStrategy(Strategy):
    name = "volume_spike"
    venue = "futures"

    def scan(self, universe: dict[str, Any]) -> list[Signal]:
        signals: list[Signal] = []
        for sym in universe.get("futures_symbols", []):
            try:
                candles = self.market.futures_klines(sym, "1h", 150)
            except Exception:
                continue
            if len(candles) < 80:
                continue
            sig = self._detect(sym, candles, universe)
            if sig:
                signals.append(sig)
        return signals

    def _detect(self, sym: str, candles: list, universe: dict) -> Signal | None:
        vols = [c.volume for c in candles]
        closes = [c.close for c in candles]
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        # 1) volume spike
        vol_sma = sma(vols, VOL_PERIOD)[-1]
        if vol_sma is None or vol_sma <= 0:
            return None
        if vols[-1] / vol_sma < RVOL_ENTRY:
            return None
        # 2) ATR compression (coiling before break)
        atr_series = atr(candles, ATR_PERIOD)
        atr_last = atr_series[-1]
        recent_atr = [a for a in atr_series[-VOL_PERIOD:] if a is not None]
        if atr_last is None or len(recent_atr) < VOL_PERIOD // 2:
            return None
        if atr_last >= sum(recent_atr) / Decimal(len(recent_atr)):
            return None
        # 3) Donchian breakout vs PRIOR-20 channel (exclude current bar, else a
        #    close can never exceed a high that includes itself -> never fires)
        u, lo = donchian(highs[:-1], lows[:-1], DONCHIAN_PERIOD)
        if u[-1] is None:
            return None
        last = candles[-1].close
        if last > u[-1]:
            side = "BUY"
        elif last < lo[-1]:
            side = "SELL"
        else:
            return None
        # skip crowded long
        if side == "BUY":
            fund = universe.get("funding", {}).get(sym)
            if fund is not None and fund.funding_rate > FUNDING_LONG_SKIP:
                return None
        book = universe.get("futures_books", {}).get(sym)
        if not book:
            return None
        price = book.ask if side == "BUY" else book.bid
        if price is None or price <= 0:
            return None
        balance = self._futures_balance()
        return self.futures_directional(sym, price, side, balance,
                                        stop_loss_pct=Decimal("0.03"),
                                        take_profit_pct=Decimal("0.06"))
