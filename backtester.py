"""
Backtester - Simple historical backtest for strategy agents.
Uses daily OHLCV from Yahoo to simulate signals and P&L (no execution simulation).
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import json

try:
    import yfinance as yf
    import pandas as pd
except ImportError:
    yfinance = None
    pd = None


def fetch_historical(symbol: str, days: int = 60) -> Optional[pd.DataFrame]:
    """Fetch daily OHLCV for symbol. Returns DataFrame with Close, High, Low, Volume."""
    if not yfinance or not pd:
        return None
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=f"{days}d", interval="1d")
        if df is None or len(df) < 14:
            return None
        # EMAs
        df["ema_5"] = df["Close"].ewm(span=5, adjust=False).mean()
        df["ema_9"] = df["Close"].ewm(span=9, adjust=False).mean()
        df["ema_21"] = df["Close"].ewm(span=21, adjust=False).mean()
        
        # RSI
        delta = df["Close"].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, 1e-10)
        df["rsi"] = 100 - (100 / (1 + rs))
        
        # Volume
        df["volume_ratio"] = df["Volume"] / df["Volume"].rolling(20).mean().replace(0, 1)
        
        # Support/Resistance
        df["support"] = df["Low"].rolling(20).min()
        df["resistance"] = df["High"].rolling(20).max()
        
        # Bollinger Bands
        df["sma_20"] = df["Close"].rolling(20).mean()
        df["bb_std"] = df["Close"].rolling(20).std()
        df["bb_upper"] = df["sma_20"] + (2 * df["bb_std"])
        df["bb_middle"] = df["sma_20"]
        df["bb_lower"] = df["sma_20"] - (2 * df["bb_std"])
        
        # Donchian Channels
        df["donchian_upper_20"] = df["High"].rolling(20).max()
        df["donchian_lower_20"] = df["Low"].rolling(20).min()
        df["donchian_upper_40"] = df["High"].rolling(40).max()
        df["donchian_lower_40"] = df["Low"].rolling(40).min()
        
        # ATR
        high_low = df["High"] - df["Low"]
        high_close = (df["High"] - df["Close"].shift()).abs()
        low_close = (df["Low"] - df["Close"].shift()).abs()
        df["true_range"] = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df["atr"] = df["true_range"].rolling(14).mean()
        
        # 52-week high/low
        if len(df) >= 252:
            df["week_52_high"] = df["High"].rolling(252).max()
            df["week_52_low"] = df["Low"].rolling(252).min()
        else:
            df["week_52_high"] = df["High"].rolling(min(len(df), 60)).max()
            df["week_52_low"] = df["Low"].rolling(min(len(df), 60)).min()
        
        return df
    except Exception as e:
        print(f"Backtest fetch error {symbol}: {e}")
        return None


def run_backtest(
    symbol: str,
    orchestrator: Any,
    days: int = 60,
) -> Dict[str, Any]:
    """
    Run a simple backtest: for each day, build market_data from row,
    get consensus signal. If BUY, record "trade" (no real P&L, just count).
    Returns summary: total_signals, buy_days, sell_days, sample_signals.
    """
    df = fetch_historical(symbol, days)
    if df is None or orchestrator is None:
        return {"error": "No data or no orchestrator", "total_days": 0}

    buy_days = 0
    sell_days = 0
    sample_signals = []

    for i in range(21, len(df)):
        row = df.iloc[i]
        market_data = {
            "current_price": float(row["Close"]),
            "ema_9": float(row["ema_9"]),
            "ema_21": float(row["ema_21"]),
            "rsi": float(row["rsi"]) if not pd.isna(row["rsi"]) else 50,
            "volume_ratio": float(row["volume_ratio"]) if not pd.isna(row["volume_ratio"]) else 1.0,
            "support": float(row["support"]),
            "resistance": float(row["resistance"]),
            "trend_en": "bullish" if row["Close"] > row["ema_9"] else "bearish",
        }
        try:
            result = orchestrator.get_consensus_signal(market_data, symbol)
            if result["action"] == "BUY":
                buy_days += 1
            elif result["action"] == "SELL":
                sell_days += 1
            if len(sample_signals) < 5:
                sample_signals.append({
                    "date": str(df.index[i])[:10],
                    "action": result["action"],
                    "summary": result.get("summary", ""),
                })
        except Exception as e:
            pass

    total_days = len(df) - 21
    return {
        "symbol": symbol,
        "total_days": total_days,
        "buy_days": buy_days,
        "sell_days": sell_days,
        "hold_days": total_days - buy_days - sell_days,
        "sample_signals": sample_signals,
    }


def run_backtest_single_strategy(
    symbol: str,
    agent: Any,
    days: int = 60,
) -> Dict[str, Any]:
    """
    Run backtest using one StrategyAgent (not orchestrator).
    Returns per-strategy BUY/SELL/HOLD counts for the symbol over N days.
    """
    df = fetch_historical(symbol, days)
    if df is None or agent is None:
        return {"error": "No data or agent", "total_days": 0}
    
    buy_days = 0
    sell_days = 0
    sample_signals = []
    
    # Start at 41 to have enough data for 40-period Donchian
    start_idx = max(41, 21)
    for i in range(start_idx, len(df)):
        row = df.iloc[i]
        market_data = {
            "current_price": float(row["Close"]),
            "ema_5": float(row["ema_5"]) if "ema_5" in row and not pd.isna(row["ema_5"]) else 0,
            "ema_9": float(row["ema_9"]),
            "ema_21": float(row["ema_21"]),
            "rsi": float(row["rsi"]) if not pd.isna(row["rsi"]) else 50,
            "volume_ratio": float(row["volume_ratio"]) if not pd.isna(row["volume_ratio"]) else 1.0,
            "support": float(row["support"]),
            "resistance": float(row["resistance"]),
            "trend_en": "bullish" if row["Close"] > row["ema_9"] else "bearish",
            "bb_upper": float(row["bb_upper"]) if "bb_upper" in row and not pd.isna(row["bb_upper"]) else 0,
            "bb_middle": float(row["bb_middle"]) if "bb_middle" in row and not pd.isna(row["bb_middle"]) else 0,
            "bb_lower": float(row["bb_lower"]) if "bb_lower" in row and not pd.isna(row["bb_lower"]) else 0,
            "donchian_upper_20": float(row["donchian_upper_20"]) if "donchian_upper_20" in row and not pd.isna(row["donchian_upper_20"]) else 0,
            "donchian_lower_20": float(row["donchian_lower_20"]) if "donchian_lower_20" in row and not pd.isna(row["donchian_lower_20"]) else 0,
            "donchian_upper_40": float(row["donchian_upper_40"]) if "donchian_upper_40" in row and not pd.isna(row["donchian_upper_40"]) else 0,
            "donchian_lower_40": float(row["donchian_lower_40"]) if "donchian_lower_40" in row and not pd.isna(row["donchian_lower_40"]) else 0,
            "atr": float(row["atr"]) if "atr" in row and not pd.isna(row["atr"]) else 0,
            "week_52_high": float(row["week_52_high"]) if "week_52_high" in row and not pd.isna(row["week_52_high"]) else 0,
            "week_52_low": float(row["week_52_low"]) if "week_52_low" in row and not pd.isna(row["week_52_low"]) else 0,
        }
        try:
            signal = agent.analyze(market_data)
            if signal.action == "BUY":
                buy_days += 1
            elif signal.action == "SELL":
                sell_days += 1
            if len(sample_signals) < 3:
                sample_signals.append({
                    "date": str(df.index[i])[:10],
                    "action": signal.action,
                    "reason": signal.reasoning[:50],
                })
        except Exception as e:
            pass
    
    total_days = len(df) - start_idx
    return {
        "symbol": symbol,
        "strategy": agent.skill_name,
        "total_days": total_days,
        "buy_days": buy_days,
        "sell_days": sell_days,
        "hold_days": total_days - buy_days - sell_days,
        "sample_signals": sample_signals,
    }
