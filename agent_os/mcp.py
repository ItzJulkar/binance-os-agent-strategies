"""MCP bridge for live execution.

Live order execution runs through the Binance Agent OS MCP server (OAuth).
In an AI session (GPT/Claude/Grok/Hermes) the AI drives trades by calling the
MCP tools directly using the per-strategy prompts in `strategies/*/prompt.md`.

For the standalone CLI, live mode needs an MCP `call_mcp` bridge. If none is
provided, live execution is not available from the CLI (paper mode only) and
the caller is told to run through the AI session instead.
"""
from __future__ import annotations

from typing import Any, Callable


def make_mcp_call(config: dict) -> Callable[[str, dict[str, Any]], Any]:
    """Return a call_mcp bridge, or raise if the CLI cannot do live trading.

    The Binance Agent OS MCP requires an OAuth session that is established by
    the AI client. The standalone CLI does not hold those credentials, so live
    trading from the CLI is intentionally unsupported — the AI drives it.
    """
    raise RuntimeError(
        "Live execution is driven by the AI agent via the Binance Agent OS MCP "
        "server. Run this strategy through an AI session (GPT/Claude/Grok/Hermes) "
        "using the prompts in strategies/*/prompt.md, or run the CLI in --paper mode."
    )
