"""
Shared config, trades, and strategies I/O.
Single source of truth for paths and file operations.
"""

import json
from pathlib import Path
from typing import List, Dict, Any

CONFIG_FILE = Path("geewoni_config.json")
TRADES_FILE = Path("trades_history.json")
STRATEGIES_FILE = Path("strategies.json")

# Defaults that satisfy both telegram_bot and tradesniper
DEFAULT_CONFIG = {
    "weekly_profit": 0,
    "weekly_goal": 10000,
    "priority": ["NVDA", "PLTR", "RKLB", "SOFI", "OKLO", "MP", "BMNR"],
    "watchlist": ["NVDA", "RKLB", "SOFI", "PLTR", "OKLO", "MP"],
    "ai_usage": 0,
    "language": "both",
    "favorite_setups": [],
    "alert_pct": 3.0,
    "win_amount": 250,
    "loss_amount": 100,
    "push_times": {"morning": "09:00", "premarket": "21:00", "close": "04:00"},
    "monitor_rules": {"price_change": 3.0, "volume_mult": 2.0, "rsi_low": 30, "rsi_high": 70},
    "enabled_strategies": ["EMA Crossover", "Volume Breakout", "Support/Resistance"],
    "risk": {"max_position_pct": 5, "stop_loss_pct": 2, "max_daily_loss": 500},
}


def load_config() -> Dict[str, Any]:
    """Load config from file; merge with defaults."""
    if CONFIG_FILE.exists():
        try:
            loaded = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            return {**DEFAULT_CONFIG, **loaded}
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)


def save_config(config: Dict[str, Any]) -> bool:
    """Save config to file. Returns True on success."""
    try:
        CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def load_trades() -> List[Dict]:
    """Load trades history from file."""
    if TRADES_FILE.exists():
        try:
            return json.loads(TRADES_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def save_trades(trades: List[Dict]) -> bool:
    """Save full trades list to file. Returns True on success."""
    try:
        TRADES_FILE.write_text(json.dumps(trades, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def load_strategies() -> Dict[str, Dict[str, Any]]:
    """Load strategies from file; return defaults if missing."""
    if STRATEGIES_FILE.exists():
        try:
            return json.loads(STRATEGIES_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {name: {"wins": 0, "losses": 0, "profit": 0} for name in [
        "EMA Crossover", "Volume Breakout", "Support/Resistance", "RSI Divergence",
        "Trend Following", "Mean Reversion", "Volatility Trading", "Earnings Play",
        "Catalyst Trading", "Sector Rotation", "Position Sizing", "Stop Loss Rules",
        "Reversal",
    ]}


def save_strategies(strategies: Dict[str, Dict[str, Any]]) -> bool:
    """Save strategies to file. Returns True on success."""
    try:
        STRATEGIES_FILE.write_text(json.dumps(strategies, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def save_trade(trade: Dict) -> bool:
    """Append one trade and save. Returns True on success."""
    trades = load_trades()
    trades.append(trade)
    return save_trades(trades)


def calculate_win_rate() -> tuple:
    """Returns (win_rate_pct, wins, total) from closed trades."""
    trades = load_trades()
    closed = [t for t in trades if t.get("status") == "closed"]
    if not closed:
        return 0.0, 0, 0
    wins = len([t for t in closed if (t.get("profit") or 0) > 0])
    total = len(closed)
    pct = (wins / total * 100) if total > 0 else 0.0
    return pct, wins, total


def update_strategy_performance(strategy_name: str, profit: float) -> None:
    """Update wins/losses/profit for a strategy."""
    strategies = load_strategies()
    if strategy_name not in strategies:
        strategies[strategy_name] = {"wins": 0, "losses": 0, "profit": 0}
    if profit > 0:
        strategies[strategy_name]["wins"] += 1
    else:
        strategies[strategy_name]["losses"] += 1
    strategies[strategy_name]["profit"] += profit
    save_strategies(strategies)
