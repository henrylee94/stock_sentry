"""
Technical Analyst agent: fetch extended stock data and format into a fixed text block.
Input: symbol(s). Output: string block for context (e.g. [Data] lines).
"""

from typing import Dict, List, Any, Tuple

try:
    from core.data_manager import get_extended_stock_data
except ImportError:
    get_extended_stock_data = None


def get_block(symbols: List[str], max_symbols: int = 3) -> Tuple[str, Dict[str, Any]]:
    """
    For each symbol, call get_extended_stock_data and format into a block.
    Returns (context_string, stock_data_dict).
    stock_data_dict is {symbol: data} for use by consensus/news etc.
    """
    if not get_extended_stock_data or not symbols:
        return "\n[Data]\n(no data)\n", {}

    stock_data: Dict[str, Any] = {}
    lines = ["\n[Data]"]
    for sym in list(symbols)[:max_symbols]:
        data = get_extended_stock_data(sym)
        if data:
            stock_data[sym] = data
            sess = data.get("session", "regular")
            lines.append(
                f"{sym}: ${data['current_price']:.2f} ({data['price_change_pct']:+.2f}%) "
                f"{data['trend']} RSI{data['rsi']:.0f} sup${data['support']:.2f} res${data['resistance']:.2f} "
                f"vol{data['volume_ratio']:.2f}x session:{sess}"
            )
        else:
            lines.append(f"{sym}: (no data)")
    lines.append("")
    return "\n".join(lines), stock_data
