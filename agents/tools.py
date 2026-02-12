"""
OpenAI function-calling tools: get_stock_data, run_backtest, get_news.
Tool schemas for the API and executor that runs them (with injected dependencies).
"""

from typing import Any, Dict, List, Optional, Callable

# OpenAI tool definitions (JSON schema for chat.completions.create(tools=...))
OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_stock_data",
            "description": "Get current price, EMA, RSI, support/resistance, volume and trend for a US stock ticker. Use when the user asks about a symbol's price or technicals.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "US stock ticker symbol (e.g. NVDA, AAPL)"},
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_backtest",
            "description": "Run a 60-day historical backtest for a symbol using strategy consensus. Returns BUY/SELL/HOLD day counts. Use when user wants historical performance or backtest.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "US stock ticker symbol"},
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_news",
            "description": "Get the latest one-line headline news for a stock symbol. Use when user asks about news or what happened.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "US stock ticker symbol"},
                },
                "required": ["symbol"],
            },
        },
    },
]


def _format_stock_data(data: Dict[str, Any], symbol: str) -> str:
    """Format get_extended_stock_data result as short text for the model."""
    if not data:
        return f"{symbol}: No data available."
    sess = data.get("session", "regular")
    return (
        f"{symbol}: ${data['current_price']:.2f} ({data['price_change_pct']:+.2f}%) "
        f"{data['trend']} RSI{data['rsi']:.0f} support${data['support']:.2f} resistance${data['resistance']:.2f} "
        f"vol{data['volume_ratio']:.2f}x session:{sess}"
    )


def execute_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    *,
    get_stock_data_fn: Optional[Callable[[str], Optional[Dict]]] = None,
    orchestrator: Any = None,
) -> str:
    """
    Run one tool by name with the given arguments. Returns result string for the API.
    get_stock_data_fn and orchestrator must be passed by the caller (telegram_bot).
    """
    if tool_name == "get_stock_data":
        symbol = (arguments.get("symbol") or "").strip().upper()
        if not symbol:
            return "Error: symbol is required."
        if not get_stock_data_fn:
            return "Error: get_stock_data not available."
        try:
            data = get_stock_data_fn(symbol)
            return _format_stock_data(data, symbol) if data else f"{symbol}: No data."
        except Exception as e:
            return f"Error: {e}"

    if tool_name == "run_backtest":
        symbol = (arguments.get("symbol") or "").strip().upper()
        if not symbol:
            return "Error: symbol is required."
        if not orchestrator:
            return "Error: backtester not available."
        try:
            from backtester import run_backtest
            bt = run_backtest(symbol, orchestrator, days=60)
            if bt.get("error"):
                return f"Backtest error: {bt['error']}"
            total = bt.get("total_days", 0)
            b, s, h = bt.get("buy_days", 0), bt.get("sell_days", 0), bt.get("hold_days", 0)
            return f"{symbol} 60d backtest: BUY {b}d SELL {s}d HOLD {h}d (total {total}d)"
        except Exception as e:
            return f"Error: {e}"

    if tool_name == "get_news":
        symbol = (arguments.get("symbol") or "").strip().upper()
        if not symbol:
            return "Error: symbol is required."
        try:
            import feedparser
            rss = feedparser.parse(
                f"https://finance.yahoo.com/rss/headline?s={symbol}",
                request_headers={"User-Agent": "Mozilla/5.0"},
            )
            if rss.entries:
                return f"[News {symbol}] {rss.entries[0].get('title', '')[:120]}"
            return f"No recent headline for {symbol}."
        except Exception as e:
            return f"Error: {e}"

    return f"Unknown tool: {tool_name}"
