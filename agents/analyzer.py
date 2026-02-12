"""
Analyzer agent: parse user message → intent, symbols[], want_strategy, want_backtest, want_scan.
Uses intent_detector.detect() and resolve_symbol().
"""

from typing import Dict, List, Any

try:
    from intent_detector import IntentDetector, resolve_symbol
    _detector: Any = IntentDetector()
except ImportError:
    _detector = None
    resolve_symbol = lambda t: (t or "").strip().upper()


def run(message: str) -> Dict[str, Any]:
    """
    Parse user message. Returns:
      intent: str
      symbols: List[str]  (resolved tickers)
      want_strategy: bool
      want_backtest: bool
      want_scan: bool
    """
    msg_lower = (message or "").lower().strip()
    want_strategy = any(k in msg_lower for k in ("strategy", "strategies", "策略", "推荐", "win rate", "胜率"))
    want_backtest = any(k in msg_lower for k in ("backtest", "back test", "回测", "历史表现"))
    want_scan = any(k in msg_lower for k in ("scan", "screener", "扫描", "筛选"))

    if _detector is None:
        import re
        symbols = list(set(re.findall(r"\b[A-Z]{2,5}\b", (message or "").upper())))[:3]
        intent = "stock_analysis" if symbols else "general"
        return {
            "intent": intent,
            "symbols": symbols,
            "want_strategy": want_strategy,
            "want_backtest": want_backtest,
            "want_scan": want_scan,
        }

    result = _detector.detect(message)
    raw_symbols = result.get("symbols", [])
    # Resolve each so we have canonical tickers (e.g. company name -> ticker)
    symbols = []
    seen = set()
    for s in raw_symbols:
        resolved = resolve_symbol(s) if isinstance(s, str) else str(s).upper()
        if resolved and resolved not in seen:
            symbols.append(resolved)
            seen.add(resolved)
    symbols = symbols[:3]

    return {
        "intent": result.get("intent", "general"),
        "symbols": symbols,
        "want_strategy": want_strategy,
        "want_backtest": want_backtest,
        "want_scan": want_scan,
    }
