"""Binance Agent OS MCP execution client.

All authenticated account/order actions route through the Binance Agent OS
MCP server (OAuth, no API keys). The client is driven either by the local
engine or by an AI agent that calls the MCP tools directly.

The `call_mcp` callable is injected so this works with any MCP client.
"""
from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from typing import Any


def _parse(payload: Any) -> Any:
    """Unwrap common MCP envelope shapes into the raw result."""
    if isinstance(payload, dict) and "structuredContent" in payload:
        payload = payload["structuredContent"]
    if isinstance(payload, dict) and set(payload) == {"result"}:
        payload = payload["result"]
    return payload


class AgentOSClient:
    def __init__(self, call_mcp: Callable[[str, dict[str, Any]], Any]) -> None:
        self.call_mcp = call_mcp

    # ---- spot ----
    def spot_account(self) -> dict[str, Any]:
        return _parse(self.call_mcp("spot.getAccount", {"omitZeroBalances": True}))

    def spot_open_orders(self, symbol: str | None = None) -> list[dict[str, Any]]:
        args = {"symbol": symbol} if symbol else {}
        return _parse(self.call_mcp("spot.getOpenOrders", args))

    def spot_place_market(self, symbol: str, side: str, quantity: str) -> dict[str, Any]:
        return _parse(self.call_mcp("spot.newOrder", {
            "symbol": symbol, "side": side, "type": "MARKET", "quantity": quantity,
        }))

    def spot_cancel(self, symbol: str, order_id: int) -> dict[str, Any]:
        return _parse(self.call_mcp("spot.deleteOrder", {"symbol": symbol, "orderId": order_id}))

    # ---- futures ----
    def futures_account(self) -> dict[str, Any]:
        return _parse(self.call_mcp("futures_usds.accountInformationV3", {}))

    def futures_positions(self, symbol: str | None = None) -> list[dict[str, Any]]:
        args = {"symbol": symbol} if symbol else {}
        return _parse(self.call_mcp("futures_usds.positionInformationV2", args))

    def futures_open_orders(self, symbol: str | None = None) -> list[dict[str, Any]]:
        args = {"symbol": symbol} if symbol else {}
        return _parse(self.call_mcp("futures_usds.currentAllOpenOrders", args))

    def futures_set_leverage(self, symbol: str, leverage: int) -> dict[str, Any]:
        return _parse(self.call_mcp("futures_usds.changeInitialLeverage",
                                    {"symbol": symbol, "leverage": leverage}))

    def futures_place_market(self, symbol: str, side: str, quantity: str,
                             reduce_only: bool = False) -> dict[str, Any]:
        return _parse(self.call_mcp("futures_usds.newOrder", {
            "symbol": symbol, "side": side, "type": "MARKET",
            "quantity": quantity, "reduceOnly": reduce_only,
        }))

    def futures_cancel(self, symbol: str, order_id: int) -> dict[str, Any]:
        return _parse(self.call_mcp("futures_usds.cancelOrder",
                                    {"symbol": symbol, "orderId": order_id}))
