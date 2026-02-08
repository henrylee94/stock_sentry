"""
Strategy Orchestrator - Coordinates all strategy agents and returns consensus signals.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path

# Optional: use skills from skillset_manager
try:
    from skillset_manager import SkillsetManager
    _skills_manager = SkillsetManager("skills")
except ImportError:
    _skills_manager = None

from strategy_agents.base_agent import StrategyAgent, TradingSignal


class StrategyOrchestrator:
    """
    Holds one agent per strategy. Given a symbol, fetches market data,
    runs all agents, and returns weighted consensus (BUY/SELL/HOLD + confidence).
    """

    def __init__(self, skills_dir: str = "skills"):
        self.agents: List[StrategyAgent] = []
        self._load_agents(skills_dir)

    def _load_agents(self, skills_dir: str):
        """Build one StrategyAgent per skill from SkillsetManager or skills JSON."""
        if _skills_manager and _skills_manager.skills:
            for name, skill_data in _skills_manager.skills.items():
                try:
                    self.agents.append(StrategyAgent(name, skill_data))
                except Exception as e:
                    print(f"⚠️ Agent init failed for {name}: {e}")
        else:
            # Fallback: load from skills dir
            from pathlib import Path
            import json
            root = Path(skills_dir)
            for f in root.rglob("*.json"):
                try:
                    data = json.loads(f.read_text(encoding='utf-8'))
                    name = data.get('name')
                    if name:
                        self.agents.append(StrategyAgent(name, data))
                except Exception as e:
                    print(f"⚠️ Load skill {f}: {e}")
        print(f"📊 StrategyOrchestrator: {len(self.agents)} agents loaded")

    def get_consensus_signal(
        self,
        market_data: Dict[str, Any],
        symbol: str = "",
    ) -> Dict[str, Any]:
        """
        Run all agents on market_data and aggregate into consensus.
        market_data can be one symbol's get_extended_stock_data() result.
        Returns dict: buy_count, sell_count, hold_count, avg_confidence, action (BUY/SELL/HOLD), top_signals[].
        """
        if not market_data or not self.agents:
            return {
                "action": "HOLD",
                "buy_count": 0,
                "sell_count": 0,
                "hold_count": 0,
                "total_agents": 0,
                "avg_confidence": 0,
                "top_signals": [],
                "summary": "No agents or no data",
            }

        signals: List[TradingSignal] = []
        for agent in self.agents:
            try:
                sig = agent.analyze(market_data)
                signals.append(sig)
            except Exception as e:
                print(f"⚠️ Agent {agent.skill_name} error: {e}")

        buy_count = sum(1 for s in signals if s.action == "BUY")
        sell_count = sum(1 for s in signals if s.action == "SELL")
        hold_count = sum(1 for s in signals if s.action == "HOLD")
        total = len(signals)

        # Weight by confidence
        buy_conf = sum(s.confidence for s in signals if s.action == "BUY") or 0
        sell_conf = sum(s.confidence for s in signals if s.action == "SELL") or 0
        if buy_count > 0:
            buy_conf /= buy_count
        if sell_count > 0:
            sell_conf /= sell_count

        if buy_count > sell_count and buy_count >= total / 3:
            action = "BUY"
            avg_confidence = buy_conf
        elif sell_count > buy_count and sell_count >= total / 3:
            action = "SELL"
            avg_confidence = sell_conf
        else:
            action = "HOLD"
            avg_confidence = 50.0

        # Top 3 by confidence for the chosen action
        top = [s for s in signals if s.action == action]
        top.sort(key=lambda s: s.confidence, reverse=True)
        top_signals = [
            {"strategy": s.strategy_name, "confidence": s.confidence, "reasoning": s.reasoning}
            for s in top[:3]
        ]

        summary = f"{buy_count}/{total} BUY, {sell_count}/{total} SELL, {hold_count}/{total} HOLD. Consensus: {action} (conf ~{avg_confidence:.0f})"

        return {
            "action": action,
            "buy_count": buy_count,
            "sell_count": sell_count,
            "hold_count": hold_count,
            "total_agents": total,
            "avg_confidence": round(avg_confidence, 1),
            "top_signals": top_signals,
            "summary": summary,
            "all_signals": [{"strategy": s.strategy_name, "action": s.action, "confidence": s.confidence} for s in signals],
        }

    def get_rankings(self) -> List[Dict[str, Any]]:
        """Return strategies ranked by performance (win_rate, total_pnl). Uses skills' performance if available."""
        rankings = []
        for agent in self.agents:
            perf = agent.performance
            total = perf.get("total_trades", 0) or 0
            wins = perf.get("wins", 0) or 0
            win_rate = (wins / total * 100) if total > 0 else 0
            pnl = perf.get("total_pnl", 0) or 0
            rankings.append({
                "name": agent.skill_name,
                "win_rate": round(win_rate, 1),
                "total_trades": total,
                "total_pnl": round(pnl, 2),
            })
        rankings.sort(key=lambda x: (x["win_rate"], x["total_pnl"]), reverse=True)
        return rankings
