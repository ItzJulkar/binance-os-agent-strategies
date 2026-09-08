"""Base class for all strategies."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from agent_os.client import AgentOSClient
from agent_os.market import MarketDataClient
from engine.log import StrategyLog
from engine.risk import RiskManager
from engine.signal import Signal


class Strategy(ABC):
    """A strategy produces trade signals from market data.

    Subclasses implement `scan()` which is called each refresh cycle. The
    supervisor collects signals, applies the global risk gate, and executes.
    """

    name: str = "base"
    venue: str = "spot"  # default venue; strategies may emit both

    def __init__(self, client: AgentOSClient, market: MarketDataClient,
                 risk: RiskManager, log: StrategyLog, config: dict[str, Any]) -> None:
        self.client = client
        self.market = market
        self.risk = risk
        self.log = log
        self.config = config

    @abstractmethod
    def scan(self, universe: dict[str, Any]) -> list[Signal]:
        """Return signals for the current market snapshot.

        `universe` is a dict keyed by symbol with market data the supervisor
        pre-fetched (books, klines, funding). Strategies may also fetch more.
        """
        raise NotImplementedError

    def manage(self, universe: dict[str, Any]) -> list[Signal]:
        """Optional: manage open trades (TP/SL/grid rebalance). Default none."""
        return []
