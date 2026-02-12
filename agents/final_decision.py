"""
Final Decision agent: build system and user prompts from all agent outputs.
Returns dict with system, user, max_tokens so telegram_bot can call the LLM.
"""

from typing import Dict, Any


def build_prompts(
    stock_data_context: str,
    user_query: str,
    detected_intent: str,
    stock_symbols: list,
    *,
    relevant_rules: str = "",
    account_line: str = "",
    learning_context: str = "",
    is_stock_analysis: bool = True,
) -> Dict[str, Any]:
    """
    Build system and user prompt for the Final Decision LLM call.
    is_stock_analysis: when True, use the short actionable rule (建議/入場/目標/止損).
    Returns: {"system": str, "user": str, "max_tokens": int}
    """
    stock_decision_rule = ""
    if stock_data_context and is_stock_analysis:
        stock_decision_rule = """
You are the Final Decision agent. You receive: [Data] technicals, [Consensus] and [Fit] strategies, [Strategy pick] top strategies by performance, [Backtest] 60d signal distribution, [News]. Use all of these. Output MUST be short and help the user decide (max 100 words).
Required format: ① 建議: BUY / SELL / 觀望 ② 入場 $X.XX ③ 目標 $X.XX ④ 止損 $X.XX ⑤ 一句理由 (mention strategy if [Strategy pick] or [Fit] present).
If consensus is all HOLD, do NOT say "neutral" and stop. Say 觀望 and give a CONCRETE trigger (e.g. 突破 $X 可考慮買入 / 跌破 $Y 止損). If there is important news in [News], summarize in one short line. Use support/resistance from data for entry/target/stop when possible. Session "extended" = pre-market or after-hours data."""

    system = f"""{relevant_rules}
{stock_decision_rule}

{account_line}
{learning_context}

Respond in user language. Keep it short and decisive."""

    user = user_query + (stock_data_context if stock_data_context else "")
    max_tokens = 180 if (stock_data_context and stock_symbols) else 300
    return {"system": system.strip(), "user": user, "max_tokens": max_tokens}
