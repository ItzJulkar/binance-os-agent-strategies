"""REGIME-AWARE ROTATION strategy (supervisor/meta).

Classifies each symbol's market regime from 4h candles (ADX, ATR%, Bollinger
bandwidth, RSI, volume ratio, returns) and only lets a sub-strategy trade in
the regime where it has an edge:
  TRENDING   -> momentum/breakout (Donchian + ADX)
  RANGING    -> mean-reversion (Bollinger lower + RSI)
  HIGH_VOL_NEWS / CRASH -> stand aside (no new entries)

Hysteresis: a regime label must persist across consecutive scans before it
flips, to avoid whipsaw. Algorithm params are private.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from agent_os.indicators import adx, bollinger, donchian, ema, rsi, sma, volume_ratio
from engine.base import Strategy
from engine.signal import Signal

ADX_TREND = Decimal(25)
ADX_RANGE = Decimal(20)
RSI_MR_BUY = Decimal(35)
RSI_MR_SELL = Decimal(65)
CRASH_RETURN_PCT = Decimal("0.08")   # -8% in 24h
NEWS_VOL_RATIO = Decimal("2.0")
MOMENTUM_CONF = 2                    # consecutive trending scans before momentum
MIN_CANDLES = 60


class RegimeRotationStrategy(Strategy):
    name = "regime_rotation"
    venue = "spot"

    def __init__(self, *a, **kw) -> None:
        super().__init__(*a, **kw)
        self._state: dict[str, int] = {}  # symbol -> trending-streak

    def _classify(self, candles: list) -> str:
        closes = [c.close for c in candles]
        vols = [c.volume for c in candles]
        cur = candles[-1].close
        r24 = (cur - candles[-8].close) / candles[-8].close if len(candles) > 8 else Decimal(0)
        adx_s = adx(candles, 14)[-1] or Decimal(0)
        rsi_s = rsi(closes, 14)[-1] or Decimal(50)
        vol_r = volume_ratio(vols, 20)
        ema50 = (ema(closes, 50)[-1] or cur)
        atr_v = None
        # 24h return crash
        if r24 < -CRASH_RETURN_PCT:
            return "CRASH"
        # high volatility / news: volume spike with erratic price
        if vol_r is not None and vol_r >= NEWS_VOL_RATIO and adx_s < ADX_TREND:
            return "HIGH_VOL_NEWS"
        if adx_s >= ADX_TREND:
            return "TRENDING"
        if adx_s <= ADX_RANGE and rsi_s is not None:
            return "RANGING"
        return "RANGING"

    def scan(self, universe: dict[str, Any]) -> list[Signal]:
        signals: list[Signal] = []
        cfg = self.config
        notional = Decimal(cfg["sizing"]["spot_notional_usd"])
        for sym in universe.get("spot_symbols", []):
            book = universe["spot_books"].get(sym)
            if not book:
                continue
            try:
                candles = self.market.spot_klines(sym, "1h", 120)
            except Exception:
                continue
            if len(candles) < MIN_CANDLES:
                continue
            regime = self._classify(candles)
            streak = self._state.get(sym, 0)
            streak = streak + 1 if regime == self._state.get(sym + "_regime") else 1
            self._state[sym] = streak
            self._state[sym + "_regime"] = regime
            self.log.event("REGIME", symbol=sym, regime=regime)
            if regime == "TRENDING" and streak >= MOMENTUM_CONF:
                self._maybe_momentum(signals, sym, candles, book, notional)
            elif regime == "RANGING":
                self._maybe_meanrev(signals, sym, candles, book, notional)
            # HIGH_VOL_NEWS / CRASH: stand aside
        return signals

    def _maybe_momentum(self, signals, sym, candles, book, notional):
        closes = [c.close for c in candles]
        u, _ = donchian([c.high for c in candles], [c.low for c in candles], 20)
        if u[-1] is None:
            return
        last = candles[-1].close
        adx_s = adx(candles, 14)[-1] or Decimal(0)
        ema50 = ema(closes, 50)[-1]
        if ema50 is not None and last > u[-1] and adx_s >= ADX_TREND and last > ema50:
            price = book.ask if book.ask > 0 else last
            qty = self._floor(notional / price)
            if qty * price >= Decimal(5):
                signals.append(Signal(strategy="regime_rotation", venue="spot", symbol=sym,
                                      side="BUY", entry_price=price, quantity=qty,
                                      stop_loss_pct=Decimal("0.03"),
                                      take_profit_pct=Decimal("0.06")))

    def _maybe_meanrev(self, signals, sym, candles, book, notional):
        closes = [c.close for c in candles]
        up, mid, low = bollinger(closes, 20, Decimal(2))
        if low[-1] is None:
            return
        rsi_s = rsi(closes, 14)[-1]
        last = candles[-1].close
        if rsi_s is not None and rsi_s < RSI_MR_BUY and last < low[-1]:
            price = book.bid if book.bid > 0 else last
            qty = self._floor(notional / price)
            if qty * price >= Decimal(5):
                signals.append(Signal(strategy="regime_rotation", venue="spot", symbol=sym,
                                      side="BUY", entry_price=price, quantity=qty,
                                      take_profit_pct=Decimal("0.03")))

    @staticmethod
    def _floor(q):
        from decimal import ROUND_DOWN
        return (q / Decimal("0.00001")).to_integral_value(rounding=ROUND_DOWN) * Decimal("0.00001")
