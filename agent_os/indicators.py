"""Lightweight technical indicators (pure Python, Decimal-friendly).

Used by the strategies for regime detection, breakout, and grid sizing.
All functions operate on lists of Candle or price/volume series.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Sequence

from agent_os.market import Candle


def closes(candles: Sequence[Candle]) -> list[Decimal]:
    return [c.close for c in candles]


def highs(candles: Sequence[Candle]) -> list[Decimal]:
    return [c.high for c in candles]


def lows(candles: Sequence[Candle]) -> list[Decimal]:
    return [c.low for c in candles]


def volumes(candles: Sequence[Candle]) -> list[Decimal]:
    return [c.volume for c in candles]


def sma(values: Sequence[Decimal], period: int) -> list[Decimal | None]:
    out: list[Decimal | None] = []
    acc = Decimal(0)
    for i, v in enumerate(values):
        acc += v
        if i >= period:
            acc -= values[i - period]
        out.append(acc / Decimal(period) if i >= period - 1 else None)
    return out


def ema(values: Sequence[Decimal], period: int) -> list[Decimal | None]:
    if not values:
        return []
    k = Decimal(2) / Decimal(period + 1)
    out: list[Decimal | None] = [None] * (period - 1)
    seed = sum(values[:period]) / Decimal(period)
    out.append(seed)
    prev = seed
    for v in values[period:]:
        prev = v * k + prev * (Decimal(1) - k)
        out.append(prev)
    return out


def rsi(values: Sequence[Decimal], period: int = 14) -> list[Decimal | None]:
    if len(values) < period + 1:
        return [None] * len(values)
    out: list[Decimal | None] = [None] * period
    gains: list[Decimal] = []
    losses: list[Decimal] = []
    for i in range(1, period + 1):
        d = values[i] - values[i - 1]
        gains.append(d if d > 0 else Decimal(0))
        losses.append(-d if d < 0 else Decimal(0))
    avg_gain = sum(gains) / Decimal(period)
    avg_loss = sum(losses) / Decimal(period)
    for i in range(period, len(values)):
        d = values[i] - values[i - 1]
        gain = d if d > 0 else Decimal(0)
        loss = -d if d < 0 else Decimal(0)
        avg_gain = (avg_gain * (period - 1) + gain) / Decimal(period)
        avg_loss = (avg_loss * (period - 1) + loss) / Decimal(period)
        if avg_loss == 0:
            out.append(Decimal(100))
        else:
            rs = avg_gain / avg_loss
            out.append(Decimal(100) - Decimal(100) / (Decimal(1) + rs))
    return out


def atr(candles: Sequence[Candle], period: int = 14) -> list[Decimal | None]:
    if len(candles) < period + 1:
        return [None] * len(candles)
    trs: list[Decimal] = []
    for i in range(1, len(candles)):
        h, l, pc = candles[i].high, candles[i].low, candles[i - 1].close
        tr = max(h - l, abs(h - pc), abs(l - pc))
        trs.append(tr)
    out: list[Decimal | None] = [None] * len(candles)
    first = sum(trs[:period]) / Decimal(period)
    out[period] = first
    for i in range(period + 1, len(candles)):
        out[i] = (out[i - 1] * (period - 1) + trs[i - 1]) / Decimal(period)
    return out


def bollinger(values: Sequence[Decimal], period: int = 20, mult: Decimal = Decimal(2)) -> tuple[list, list, list]:
    """Returns (upper, middle, lower) series aligned to input length."""
    upper: list[Decimal | None] = []
    middle: list[Decimal | None] = []
    lower: list[Decimal | None] = []
    for i in range(len(values)):
        if i < period - 1:
            upper.append(None); middle.append(None); lower.append(None)
            continue
        window = values[i - period + 1 : i + 1]
        mean = sum(window) / Decimal(period)
        var = sum((v - mean) ** 2 for v in window) / Decimal(period)
        sd = var.sqrt()
        upper.append(mean + mult * sd)
        middle.append(mean)
        lower.append(mean - mult * sd)
    return upper, middle, lower


def donchian(highs_seq: Sequence[Decimal], lows_seq: Sequence[Decimal], period: int = 20) -> tuple[list, list]:
    upper: list[Decimal | None] = []
    lower: list[Decimal | None] = []
    for i in range(len(highs_seq)):
        if i < period - 1:
            upper.append(None); lower.append(None)
            continue
        upper.append(max(highs_seq[i - period + 1 : i + 1]))
        lower.append(min(lows_seq[i - period + 1 : i + 1]))
    return upper, lower


def adx(candles: Sequence[Candle], period: int = 14) -> list[Decimal | None]:
    """Wilder's ADX. Returns None until enough bars."""
    if len(candles) < period * 2 + 1:
        return [None] * len(candles)
    out: list[Decimal | None] = [None] * len(candles)
    plus_dm: list[Decimal] = []
    minus_dm: list[Decimal] = []
    trs: list[Decimal] = []
    for i in range(1, len(candles)):
        up = candles[i].high - candles[i - 1].high
        down = candles[i - 1].low - candles[i].low
        plus_dm.append(up if (up > down and up > 0) else Decimal(0))
        minus_dm.append(down if (down > up and down > 0) else Decimal(0))
        h, l, pc = candles[i].high, candles[i].low, candles[i - 1].close
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    # first smoothed values (trs index `period-1` => candle index `period`)
    p = sum(plus_dm[:period]) / Decimal(period)
    m = sum(minus_dm[:period]) / Decimal(period)
    tr = sum(trs[:period]) / Decimal(period)
    # dxs[k] corresponds to trs index (period + k) => candle index (period + 1 + k)
    dxs: list[Decimal] = []
    for i in range(period, len(trs)):
        p = (p * (period - 1) + plus_dm[i]) / Decimal(period)
        m = (m * (period - 1) + minus_dm[i]) / Decimal(period)
        tr = (tr * (period - 1) + trs[i]) / Decimal(period)
        if tr == 0:
            dxs.append(Decimal(0))
        else:
            pdi = p / tr * Decimal(100)
            mdi = m / tr * Decimal(100)
            s = pdi + mdi
            dxs.append(abs(pdi - mdi) / s * Decimal(100) if s else Decimal(0))
    # smooth DX into ADX; adx_vals[j] => candle index (2*period + j)
    adx_val = sum(dxs[:period]) / Decimal(period)
    out[2 * period] = adx_val
    for j in range(period, len(dxs)):
        adx_val = (adx_val * (period - 1) + dxs[j]) / Decimal(period)
        out[2 * period + (j - period + 1)] = adx_val
    return out


def volume_ratio(volumes_seq: Sequence[Decimal], lookback: int = 20) -> Decimal | None:
    """Current volume / rolling average volume."""
    if len(volumes_seq) < lookback + 1:
        return None
    avg = sum(volumes_seq[-lookback - 1 : -1]) / Decimal(lookback)
    if avg == 0:
        return None
    return volumes_seq[-1] / avg
