"""
Strategy Agents - Each agent evaluates one trading strategy against market data.
"""

from .base_agent import StrategyAgent, TradingSignal

__all__ = ['StrategyAgent', 'TradingSignal']
