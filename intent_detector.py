"""
Intent Detector - Fast, Free Intent Classification
Zero-cost intent detection before calling OpenAI to save tokens
"""

import csv
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

# Minimal fallback only when both stock_aliases.json and nasdaq_screener_*.csv are absent
NAME_TO_TICKER = {
    "apple": "AAPL", "amazon": "AMZN", "nvidia": "NVDA", "tesla": "TSLA",
    "google": "GOOGL", "sofi": "SOFI", "oklo": "OKLO",
}

_PROJECT_ROOT = Path(__file__).resolve().parent
_ALIAS_FILE = _PROJECT_ROOT / "stock_aliases.json"
_OVERRIDE_FILE = _PROJECT_ROOT / "stock_aliases_override.json"
_NASDAQ_SCREENER_GLOB = "nasdaq_screener_*.csv"
_alias_map_cache: Optional[Dict[str, str]] = None


def _normalize_name_for_alias(s: str) -> str:
    """Lowercase, keep letters/spaces/numbers, collapse spaces (for CSV name -> alias)."""
    if not s:
        return ""
    s = re.sub(r"[^a-z0-9\s]", "", s.lower().strip())
    return re.sub(r"\s+", " ", s).strip()


def _add_aliases(alias_to_ticker: Dict[str, str], symbol: str, security_name: str) -> None:
    """Add ticker and normalized company name(s) to alias map."""
    sym = (symbol or "").strip().upper()
    if not sym or len(sym) > 10:
        return
    alias_to_ticker[sym.lower()] = sym
    if not security_name:
        return
    norm = _normalize_name_for_alias(security_name)
    if norm:
        alias_to_ticker[norm] = sym
    first = norm.split()[0] if norm else ""
    if first and len(first) >= 2:
        alias_to_ticker[first] = sym


def _load_alias_map_from_csv() -> Optional[Dict[str, str]]:
    """Build alias -> ticker from newest nasdaq_screener_*.csv in project root. Returns None if no CSV."""
    csv_files = sorted(_PROJECT_ROOT.glob(_NASDAQ_SCREENER_GLOB), key=lambda p: p.stat().st_mtime, reverse=True)
    if not csv_files:
        return None
    out: Dict[str, str] = {}
    try:
        with open(csv_files[0], "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                return out
            col_map = {h.strip().lower(): i for i, h in enumerate(header)}
            sym_idx = col_map.get("symbol", 0)
            name_idx = col_map.get("name", 1)
            for row in reader:
                if len(row) <= max(sym_idx, name_idx):
                    continue
                symbol = (row[sym_idx] or "").strip()
                name = (row[name_idx] or "").strip()
                if symbol.upper() == "SYMBOL":
                    continue
                _add_aliases(out, symbol, name)
        # Merge override so overrides apply when using CSV
        if _OVERRIDE_FILE.exists():
            try:
                with open(_OVERRIDE_FILE, "r", encoding="utf-8") as f:
                    override = json.load(f)
                if isinstance(override, dict):
                    for k, v in override.items():
                        if isinstance(v, str):
                            out[k.strip().lower()] = v.strip().upper()
                        elif isinstance(v, list) and v and isinstance(v[0], str):
                            out[k.strip().lower()] = v[0].strip().upper()
            except Exception:
                pass
        return out
    except Exception:
        return None


def _load_alias_map() -> Dict[str, str]:
    """Load alias -> ticker: 1) stock_aliases.json, 2) CSV (nasdaq_screener_*.csv), 3) minimal NAME_TO_TICKER."""
    global _alias_map_cache
    if _alias_map_cache is not None:
        return _alias_map_cache
    # 1) Prefer stock_aliases.json
    if _ALIAS_FILE.exists():
        try:
            with open(_ALIAS_FILE, "r", encoding="utf-8") as f:
                m = json.load(f)
            if isinstance(m, dict):
                _alias_map_cache = {k.strip().lower(): v.strip().upper() for k, v in m.items() if isinstance(v, str)}
                return _alias_map_cache
        except Exception:
            pass
    # 2) Build from CSV so all screener symbols (e.g. BMNR) resolve without maintaining NAME_TO_TICKER
    from_csv = _load_alias_map_from_csv()
    if from_csv:
        _alias_map_cache = from_csv
        return _alias_map_cache
    # 3) Minimal fallback for development when no JSON/CSV
    _alias_map_cache = dict(NAME_TO_TICKER)
    return _alias_map_cache


def _normalize_input(text: str) -> str:
    """Lowercase and remove spaces for matching (e.g. 'ap p e' -> 'appe')."""
    if not text:
        return ""
    return re.sub(r"\s+", "", text.lower().strip())


def resolve_symbol(text: str) -> str:
    """
    Resolve user input to a ticker: accept ticker (AMZN) or company name (amazon, Amazon).
    Supports partial match (e.g. amazo -> AMZN) when using stock_aliases.json.
    Returns uppercase ticker. Unknown names are returned uppercased as-is.
    """
    if not text or not isinstance(text, str):
        return (text or "").strip().upper()
    s = text.strip()
    if not s:
        return ""
    # Already looks like a ticker (2-5 letters, optional .X)
    if re.match(r"^[A-Za-z]{2,5}(\.[A-Za-z])?$", s):
        return s.upper()
    alias_map = _load_alias_map()
    sl = s.lower()
    snorm = _normalize_input(s)
    # Exact match
    if snorm in alias_map:
        return alias_map[snorm]
    if sl in alias_map:
        return alias_map[sl]
    # Substring: "amazon" in "amazon stock"
    for name, ticker in sorted(alias_map.items(), key=lambda x: -len(x[0])):
        if name in snorm or name in sl:
            return ticker
    # Prefix: "amazo" -> alias "amazon" (alias that starts with snorm; prefer longest)
    if len(snorm) >= 3:
        candidates = [(name, ticker) for name, ticker in alias_map.items() if name.startswith(snorm)]
        if candidates:
            best = max(candidates, key=lambda x: len(x[0]))
            return best[1]
    return s.upper()


class IntentDetector:
    """Zero-cost intent classification - saves API calls"""
    
    def __init__(self):
        self.intent_patterns = {
            'stock_analysis': {
                'keywords': [
                    'entry', 'price', 'buy', 'sell', 'target', 'stop',
                    'analyze', 'look', 'check', 'worth', 'good', 'bad',
                    'how', 'what', 'should', 'can', 'entry point',
                    '分析', '价格', '买', '卖', '入场', '目标', '止损',
                    '怎么样', '如何', '好吗', '检查'
                ],
                'priority': 1
            },
            'news': {
                'keywords': [
                    'news', 'headline', 'happen', 'update', 'latest',
                    'what happen', 'why', 'reason',
                    '新闻', '消息', '发生', '最新', '为什么'
                ],
                'priority': 2
            },
            'strategy': {
                'keywords': [
                    'strategy', 'best', 'recommend', 'which', 'how',
                    'win rate', 'perform',
                    '策略', '推荐', '哪个', '怎么', '表现', '胜率'
                ],
                'priority': 2
            },
            'positions': {
                'keywords': [
                    'position', 'positions', 'holding', 'portfolio', 'my trades',
                    'my stock', 'what i have', 'my positions', 'show positions',
                    '持仓', '仓位', '我的交易', '我的股票'
                ],
                'priority': 0  # Higher priority so "show my positions" -> positions not stock_analysis
            },
            'performance': {
                'keywords': [
                    'profit', 'loss', 'performance', 'win rate',
                    'how am i', 'how did i', 'today', 'this week',
                    '盈利', '亏损', '表现', '胜率', '今天', '本周'
                ],
                'priority': 2
            },
            'help': {
                'keywords': [
                    'help', 'command', 'how to', 'can you',
                    '帮助', '命令', '怎么用'
                ],
                'priority': 3
            }
        }
        
        # User's watchlist from config (optional; for ordering/hints only)
        try:
            from core.config import load_config
            cfg = load_config()
            self.watchlist = [s.upper() for s in (cfg.get("priority") or cfg.get("watchlist") or [])]
        except Exception:
            self.watchlist = []
        if not self.watchlist:
            self.watchlist = ["NVDA", "PLTR", "RKLB", "SOFI", "OKLO", "MP", "BMNR"]
        
        # Company name -> ticker (from stock_aliases.json if present, else NAME_TO_TICKER)
        self.name_to_ticker = _load_alias_map()
    
    def detect(self, message: str) -> Dict:
        """
        Detect intent and extract stock symbols
        
        Returns:
            {
                'intent': str,
                'symbols': List[str],
                'has_data': bool,
                'original_message': str,
                'confidence': str
            }
        """
        message_lower = message.lower().strip()
        
        # Extract stock symbols: (1) company names -> ticker, (2) explicit tickers
        symbols = []
        seen = set()
        
        # Company name -> ticker (longer phrases first to match "rocket lab" before "rocket")
        for name, ticker in sorted(self.name_to_ticker.items(), key=lambda x: -len(x[0])):
            if name in message_lower and ticker not in seen:
                symbols.append(ticker)
                seen.add(ticker)
        
        # Explicit tickers (2-5 uppercase letters)
        for m in re.findall(r'\b[A-Z]{2,5}\b', message):
            t = m.upper()
            if t not in seen:
                symbols.append(t)
                seen.add(t)
        
        # Optional: add watchlist symbols mentioned in message (for ordering)
        for symbol in self.watchlist:
            if symbol.lower() in message_lower and symbol not in seen:
                symbols.append(symbol)
                seen.add(symbol)
        
        symbols = symbols[:3]
        
        # Detect intent based on keywords
        detected_intent = 'general'
        highest_priority = 999
        
        for intent, config in self.intent_patterns.items():
            # Check if any keyword matches
            if any(kw in message_lower for kw in config['keywords']):
                # Use highest priority match (lower number = higher priority)
                if config['priority'] < highest_priority:
                    detected_intent = intent
                    highest_priority = config['priority']
        
        # If symbols found, likely stock analysis even if keywords don't match
        if symbols and detected_intent == 'general':
            detected_intent = 'stock_analysis'
        
        return {
            'intent': detected_intent,
            'symbols': symbols,
            'has_data': len(symbols) > 0,
            'original_message': message,
            'confidence': 'high' if symbols else 'medium'
        }
    
    def update_watchlist(self, new_watchlist: List[str]):
        """Update the watchlist with user's current stocks"""
        self.watchlist = [s.upper() for s in new_watchlist]


# Test function
if __name__ == "__main__":
    # Quick resolve_symbol check (e.g. amazo -> AMZN, ap p e -> AAPL)
    print("resolve_symbol:", [resolve_symbol(t) for t in ["amazon", "amazo", "ap p e", "appl"]])
    detector = IntentDetector()

    test_messages = [
        "NVDA entry point?",
        "what's nvidia looking like?",
        "should i buy nvda today?",
        "检查nvda价格",
        "今天的新闻",
        "show my positions",
        "how am i doing?",
        "what happened to pltr",
        "nvda好吗？",
        "help me"
    ]
    
    print("=" * 60)
    print("INTENT DETECTOR TEST")
    print("=" * 60)
    
    for msg in test_messages:
        result = detector.detect(msg)
        print(f"\nMessage: '{msg}'")
        print(f"  Intent: {result['intent']}")
        print(f"  Symbols: {result['symbols']}")
        print(f"  Has Data: {result['has_data']}")
        print(f"  Confidence: {result['confidence']}")
