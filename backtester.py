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
        df["ema_9"] = df["Close"].ewm(span=9, adjust=False).mean()
        df["ema_21"] = df["Close"].ewm(span=21, adjust=False).mean()
        delta = df["Close"].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, 1e-10)
        df["rsi"] = 100 - (100 / (1 + rs))
        df["volume_ratio"] = df["Volume"] / df["Volume"].rolling(20).mean().replace(0, 1)
        df["support"] = df["Low"].rolling(20).min()
        df["resistance"] = df["High"].rolling(20).max()
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
