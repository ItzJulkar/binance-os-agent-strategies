"""Public Binance market-data client.

Only unauthenticated market data lives here (tickers, klines, funding, order
books). All account/order actions go through the Agent OS MCP client.
"""
from __future__ import annotations

import json
import time
import urllib.request
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

SPOT_API = "https://api.binance.com"
FUTURES_API = "https://fapi.binance.com"


def _get(url: str, timeout: int = 30) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "binance-os-strategies"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


@dataclass(frozen=True)
class Ticker:
    symbol: str
    bid: Decimal
    ask: Decimal
    quote_volume: Decimal
    last: Decimal


@dataclass(frozen=True)
class Candle:
    open_time: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


@dataclass(frozen=True)
class FundingRate:
    symbol: str
    funding_rate: Decimal  # per 8h, e.g. 0.0001 = 0.01%
    next_funding_time: int
    mark_price: Decimal


class MarketDataClient:
    """Fetch top-N USDT pairs, klines, books and funding for spot + futures."""

    def __init__(self, top_n: int = 20, quote: str = "USDT", min_vol: Decimal = Decimal(10_000_000)) -> None:
        self.top_n = top_n
        self.quote = quote
        self.min_vol = min_vol

    # ---- spot ----
    def spot_top_pairs(self) -> list[str]:
        tickers = _get(f"{SPOT_API}/api/v3/ticker/24hr")
        rows = []
        for t in tickers:
            if t["symbol"].endswith(self.quote):
                vol = Decimal(str(t.get("quoteVolume", "0")))
                if vol >= self.min_vol:
                    rows.append((t["symbol"], vol))
        rows.sort(key=lambda r: r[1], reverse=True)
        return [s for s, _ in rows[: self.top_n]]

    def spot_tickers(self, symbols: list[str]) -> dict[str, Ticker]:
        out = {}
        for sym in symbols:
            try:
                t = _get(f"{SPOT_API}/api/v3/ticker/bookTicker?symbol={sym}")
                out[sym] = Ticker(sym, Decimal(t["bidPrice"]), Decimal(t["askPrice"]), Decimal(0), Decimal(0))
            except Exception:
                continue
        return out

    def spot_klines(self, symbol: str, interval: str = "1h", limit: int = 200) -> list[Candle]:
        data = _get(f"{SPOT_API}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}")
        return [
            Candle(int(k[0]), Decimal(k[1]), Decimal(k[2]), Decimal(k[3]), Decimal(k[4]), Decimal(k[5]))
            for k in data
        ]

    # ---- futures ----
    def futures_top_pairs(self) -> list[str]:
        tickers = _get(f"{FUTURES_API}/fapi/v1/ticker/24hr")
        rows = []
        for t in tickers:
            if t["symbol"].endswith(self.quote):
                vol = Decimal(str(t.get("quoteVolume", "0")))
                if vol >= self.min_vol:
                    rows.append((t["symbol"], vol))
        rows.sort(key=lambda r: r[1], reverse=True)
        return [s for s, _ in rows[: self.top_n]]

    def futures_tickers(self, symbols: list[str]) -> dict[str, Ticker]:
        out = {}
        for sym in symbols:
            try:
                t = _get(f"{FUTURES_API}/fapi/v1/ticker/bookTicker?symbol={sym}")
                out[sym] = Ticker(sym, Decimal(t["bidPrice"]), Decimal(t["askPrice"]), Decimal(0), Decimal(0))
            except Exception:
                continue
        return out

    def futures_klines(self, symbol: str, interval: str = "1h", limit: int = 200) -> list[Candle]:
        data = _get(f"{FUTURES_API}/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}")
        return [
            Candle(int(k[0]), Decimal(k[1]), Decimal(k[2]), Decimal(k[3]), Decimal(k[4]), Decimal(k[5]))
            for k in data
        ]

    def futures_funding_rates(self, symbols: list[str]) -> dict[str, FundingRate]:
        out = {}
        for sym in symbols:
            try:
                data = _get(f"{FUTURES_API}/fapi/v1/premiumIndex?symbol={sym}")
                out[sym] = FundingRate(
                    sym,
                    Decimal(str(data.get("lastFundingRate", "0"))),
                    int(data.get("nextFundingTime", 0)),
                    Decimal(str(data.get("markPrice", "0"))),
                )
            except Exception:
                continue
        return out

    def futures_funding_history(self, symbol: str, limit: int = 30) -> list[Decimal]:
        data = _get(f"{FUTURES_API}/fapi/v1/fundingRate?symbol={symbol}&limit={limit}")
        return [Decimal(str(r.get("fundingRate", "0"))) for r in data]
