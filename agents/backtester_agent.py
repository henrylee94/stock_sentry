"""
Backtester agent: thin wrapper around backtester.run_backtest; format result into one line.
Input: symbol, orchestrator. Output: string e.g. [Backtest SYMBOL] 60d: BUY x SELL y HOLD z.
"""

from typing import Any, Optional

try:
    from backtester import run_backtest
except ImportError:
    run_backtest = None


def run_backtest_line(symbol: str, orchestrator: Any, days: int = 60) -> str:
    """
    Run backtest for symbol with orchestrator; return one line for context.
    Returns empty string on error or no orchestrator.
    """
    if not run_backtest or not orchestrator:
        return ""
    try:
        bt = run_backtest(symbol, orchestrator, days=days)
        if not bt or bt.get("error"):
            return ""
        total = bt.get("total_days", 0)
        b = bt.get("buy_days", 0)
        s = bt.get("sell_days", 0)
        h = bt.get("hold_days", 0)
        return f"[Backtest {symbol}] {days}d: BUY {b}d SELL {s}d HOLD {h}d (total {total}d)\n"
    except Exception:
        return ""
