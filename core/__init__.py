"""
Core package: config, data, rate limiting.
Single source of truth for paths and load/save of config, trades, strategies.
"""

from .config import (
    CONFIG_FILE,
    TRADES_FILE,
    STRATEGIES_FILE,
    load_config,
    save_config,
    load_trades,
    save_trades,
    load_strategies,
    save_strategies,
    save_trade,
    calculate_win_rate,
    update_strategy_performance,
)

__all__ = [
    "CONFIG_FILE",
    "TRADES_FILE",
    "STRATEGIES_FILE",
    "load_config",
    "save_config",
    "load_trades",
    "save_trades",
    "load_strategies",
    "save_strategies",
    "save_trade",
    "calculate_win_rate",
    "update_strategy_performance",
]
