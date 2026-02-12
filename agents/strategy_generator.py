"""
Strategy Generator agent: pick top 2 strategies by win rate then P&L from strategies.json.
Output: string line e.g. [Strategy pick] A, B (by win rate & P&L).
"""

from typing import Optional

try:
    from core.config import load_strategies
except ImportError:
    load_strategies = None


def get_top_strategies_line(top_n: int = 2) -> str:
    """Return a single line for context: [Strategy pick] name1, name2 (by win rate & P&L)."""
    if not load_strategies:
        return ""
    try:
        strat_list = load_strategies()
        if not strat_list:
            return ""

        def _score(item):
            name, data = item
            w, L = data.get("wins", 0), data.get("losses", 0)
            total = w + L
            wr = (w / total) if total > 0 else 0
            return (wr, data.get("profit", 0))

        ranked = sorted(strat_list.items(), key=_score, reverse=True)
        top = [s[0] for s in ranked[:top_n]]
        return "[Strategy pick] " + ", ".join(top) + " (by win rate & P&L)\n"
    except Exception:
        return ""
