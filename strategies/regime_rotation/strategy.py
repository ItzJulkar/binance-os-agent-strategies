"""REGIME-AWARE ROTATION strategy (supervisor/meta).

Classifies each symbol's market regime from 1h candles (ADX, RSI, volume
ratio, 24h return) and only lets a sub-strategy trade in the regime where it
has an edge:
  TRENDING  -> momentum/breakout (Donchian + ADX + price>EMA50)
  RANGING   -> mean-reversion (close below lower Bollinger + RSI oversold)
  HIGH_VOL_NEWS / CRASH -> stand aside (cash)

Hysteresis: a trend label must persist for consecutive scans before acting.

Algorithm parameters are private.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from agent_os.indicators import adx, bollinger, donchian, ema, rsi, volume_ratio
from engine.base import Strategy
from engine.signal import Signal

ADX_TREND = Decimal(25)
ADX_RANGE = Decimal(20)
RSI_MR_BUY = Decimal(35)
CRASH_RETURN = Decimal("0.08")        # -8% in 24h
VOL_SPIKE = Decimal("2.0")
MIN_CANDLES = 60


class RegimeRotationStrategy(Strategy):
    name = "regime_rotation"
    venue = "spot"

    def __init__(self, *a, **kw) -> None:
        super().__init__(*a, **kw)
        self._state: dict[str, Any] = {}

    def _classify(self, candles: list) -> str:
        closes = [c.close for c in candles]
        vols = [c.volume for c in candles]
        last = candles[-1].close
        r24 = (last - candles[-8].close) / candles[-8].close if len(candles) > 8 else Decimal(0)
        adxv = adx(candles, 14)[-1] or Decimal(0)
        rsiv = rsi(closes, 14)[-1]
        vr = volume_ratio(vols, 20)
        if r24 < -CRASH_RETURN:
            return "CRASH"
        if vr is not None and vr >= VOL_SPIKE and adxv < ADX_TREND:
            return "HIGH_VOL_NEWS"
        if adxv >= ADX_TREND:
            return "TRENDING"
        if adxv <= ADX_RANGE and rsiv is not None:
            return "RANGING"
        return "RANGING"

    def scan(self, universe: dict[str, Any]) -> list[Signal]:
        signals: list[Signal] = []
        for sym in universe.get("spot_symbols", []):
            book = universe["spot_books"].get(sym)
            if not book:
                continue
            try:
                candles = self.market.spot_klines(sym, "1h", 150)
            except Exception:
                continue
            if len(candles) < MIN_CANDLES:
                continue
            regime = self._classify(candles)
            prev_regime = self._state.get(sym)
            streak = self._state.get(sym + "_streak", 0)
            streak = streak + 1 if regime == prev_regime else 1
            self._state[sym] = regime
            self._state[sym + "_streak"] = streak
            self.log.event("REGIME", symbol=sym, regime=regime, streak=streak)
            if regime == "TRENDING" and streak >= 2:
                self._momentum(signals, sym, candles, book)
            elif regime == "RANGING":
                self._meanrev(signals, sym, candles, book)
        return signals

    def _momentum(self, signals, sym, candles, book):
        # Donchian over PRIOR bars so a close can actually break out
        u, _ = donchian([c.high for c in candles[:-1]], [c.low for c in candles[:-1]], 20)
        if u[-1] is None:
            return
        closes = [c.close for c in candles]
        last = candles[-1].close
        adxv = adx(candles, 14)[-1] or Decimal(0)
        if not (last > u[-1] and adxv >= ADX_TREND):
            return
        ema50 = ema(closes, 50)[-1]
        if ema50 is None or last <= ema50:
            return
        sig = self.spot_buy(sym, book.ask if book.ask > 0 else last,
                            stop_loss_pct=Decimal("0.03"), take_profit_pct=Decimal("0.06"))
        if sig:
            signals.append(sig)

    def _meanrev(self, signals, sym, candles, book):
        closes = [c.close for c in candles]
        up, mid, low = bollinger(closes, 20, Decimal(2))
        if low[-1] is None:
            return
        rsiv = rsi(closes, 14)[-1]
        last = candles[-1].close
        if rsiv is not None and rsiv < RSI_MR_BUY and last < low[-1]:
            sig = self.spot_buy(sym, book.bid if book.bid > 0 else last,
                                take_profit_pct=Decimal("0.03"))
            if sig:
                signals.append(sig)
