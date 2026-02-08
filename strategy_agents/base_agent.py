"""
StrategyAgent - Evaluates one trading strategy (skill) against live market data.
Returns BUY / SELL / HOLD with confidence 0-100 and short reasoning.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List


@dataclass
class TradingSignal:
    """Output of one strategy agent"""
    action: str   # "BUY", "SELL", "HOLD"
    confidence: float  # 0-100
    reasoning: str
    strategy_name: str
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target: Optional[float] = None


class StrategyAgent:
    """
    One agent = one strategy (skill). Evaluates market_data against skill rules
    and returns a TradingSignal. Uses skill's parameters (EMA, RSI, volume rules).
    """

    def __init__(self, skill_name: str, skill_data: Dict[str, Any]):
        self.skill_name = skill_name
        self.skill = skill_data
        self.rules = skill_data.get('rules', {})
        self.params = skill_data.get('parameters', {})
        self.performance = skill_data.get('performance', {})

    def analyze(self, market_data: Dict[str, Any]) -> TradingSignal:
        """
        Evaluate market_data against this strategy's rules.
        market_data should have: current_price, ema_9, ema_21, rsi, volume_ratio,
        support, resistance, trend_en (bullish/bearish/neutral).
        """
        price = float(market_data.get('current_price', 0) or 0)
        ema_9 = float(market_data.get('ema_9', 0) or 0)
        ema_21 = float(market_data.get('ema_21', 0) or 0)
        rsi = float(market_data.get('rsi', 50) or 50)
        vol_ratio = float(market_data.get('volume_ratio', 1) or 1)
        support = float(market_data.get('support', 0) or 0)
        resistance = float(market_data.get('resistance', 0) or 0)
        trend_en = (market_data.get('trend_en') or 'neutral').lower()

        if price <= 0:
            return TradingSignal("HOLD", 0, "No valid price", self.skill_name)

        # Strategy-specific logic (rule-based)
        action, confidence, reasoning = self._evaluate(
            price, ema_9, ema_21, rsi, vol_ratio, support, resistance, trend_en
        )

        entry_price = price
        stop_loss = None
        target = None
        if action == "BUY" and support > 0:
            stop_loss = round(support * 0.98, 2)
            target = round(resistance * 1.02, 2) if resistance > price else round(price * 1.03, 2)
        elif action == "SELL" and resistance > 0:
            stop_loss = round(resistance * 1.02, 2)
            target = round(support * 0.98, 2) if support < price else round(price * 0.97, 2)

        return TradingSignal(
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            strategy_name=self.skill_name,
            entry_price=entry_price,
            stop_loss=stop_loss,
            target=target,
        )

    def _evaluate(
        self,
        price: float,
        ema_9: float,
        ema_21: float,
        rsi: float,
        vol_ratio: float,
        support: float,
        resistance: float,
        trend_en: str,
    ) -> tuple:
        """Return (action, confidence, reasoning) based on skill name and params."""
        name = self.skill_name.lower()
        rsi_min = self.params.get('rsi_min', 40)
        rsi_max = self.params.get('rsi_max', 70)
        vol_min = self.params.get('volume_ratio', 1.5)

        # EMA Crossover
        if 'ema' in name and 'crossover' in name:
            if ema_9 > ema_21 and price > ema_9:
                if rsi_min <= rsi <= rsi_max and vol_ratio >= vol_min:
                    return "BUY", min(90, 50 + (rsi - 40) + (vol_ratio - 1) * 10), "EMA9>EMA21, price above EMA9, RSI and volume OK"
                elif rsi_min <= rsi <= rsi_max:
                    return "BUY", 65, "EMA bull cross, RSI OK, volume weak"
                else:
                    return "HOLD", 40, "EMA bull but RSI or volume not ideal"
            elif ema_9 < ema_21 and price < ema_9:
                return "SELL", 60, "EMA bear cross, price below EMA9"
            return "HOLD", 30, "No clear EMA crossover"

        # Volume Breakout
        if 'volume' in name or 'breakout' in name:
            if vol_ratio >= 2.0 and price > resistance * 0.99 and resistance > 0:
                return "BUY", min(85, 60 + (vol_ratio - 2) * 10), "Volume breakout above resistance"
            if vol_ratio >= vol_min and price > ema_9 and rsi > 50:
                return "BUY", 60, "Volume confirms, trend up"
            return "HOLD", 35, "Volume or price not at breakout"

        # Support / Resistance (skill name e.g. "Support Resistance Bounce")
        if 'support' in name and 'resistance' in name:
            dist_sup = (price - support) / support if support > 0 else 1
            dist_res = (resistance - price) / resistance if resistance > 0 else 1
            if dist_sup < 0.02 and rsi < 45:
                return "BUY", 70, "Near support, RSI oversold"
            if dist_res < 0.02 and rsi > 55:
                return "SELL", 65, "Near resistance, RSI elevated"
            return "HOLD", 40, "Not at key level"

        # RSI Divergence (simplified: use RSI extremes)
        if 'rsi' in name:
            if rsi < 30:
                return "BUY", 65, "RSI oversold"
            if rsi > 70:
                return "SELL", 65, "RSI overbought"
            return "HOLD", 40, "RSI neutral"

        # Trend Following
        if 'trend' in name:
            if trend_en == 'bullish' and price > ema_9:
                return "BUY", 70, "Trend following: bullish, price above EMA9"
            if trend_en == 'bearish' and price < ema_9:
                return "SELL", 65, "Trend following: bearish"
            return "HOLD", 35, "Trend not clear"

        # Mean Reversion
        if 'mean' in name or 'reversion' in name:
            if rsi < 35:
                return "BUY", 65, "Mean reversion: RSI oversold"
            if rsi > 65:
                return "SELL", 60, "Mean reversion: RSI overbought"
            return "HOLD", 40, "No extreme"

        # Default: generic trend + RSI
        if trend_en == 'bullish' and rsi_min <= rsi <= rsi_max and vol_ratio >= 1:
            return "BUY", 55, "Bullish trend, RSI and volume OK"
        if trend_en == 'bearish':
            return "SELL", 50, "Bearish trend"
        return "HOLD", 40, "No clear signal"
