"""
Multi-agent pipeline: Analyzer → Technical Analyst → Strategy Generator → Backtester → Final Decision.
"""

from .analyzer import run as analyzer_run
from .technical_analyst import get_block as technical_analyst_get_block
from .strategy_generator import get_top_strategies_line as strategy_generator_get_line
from .backtester_agent import run_backtest_line as backtester_agent_run_line
from .final_decision import build_prompts as final_decision_build_prompts

__all__ = [
    "analyzer_run",
    "technical_analyst_get_block",
    "strategy_generator_get_line",
    "backtester_agent_run_line",
    "final_decision_build_prompts",
]
