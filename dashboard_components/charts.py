"""
Chart generators for GEEWONI dashboard - Plotly figures.
Uses trades_history and strategies data.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict

try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import pandas as pd
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    px = None
    go = None
    pd = None


def _ensure_df(trades: List[Dict]) -> Optional["pd.DataFrame"]:
    if not pd or not trades:
        return None
    try:
        return pd.DataFrame(trades)
    except Exception:
        return None


def create_equity_curve(trades: List[Dict], weekly_goal: float = 10000) -> Optional[Any]:
    """
    Cumulative P&L over time (equity curve).
    trades: list of trade dicts with 'date' or 'exit_date', 'profit'.
    """
    if not PLOTLY_AVAILABLE or not go:
        return None
    closed = [t for t in trades if t.get("status") == "closed" and t.get("profit") is not None]
    if not closed:
        fig = go.Figure()
        fig.add_annotation(text="No closed trades yet", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title="Equity Curve", height=300, margin=dict(t=40, b=30, l=40, r=20))
        return fig
    df = _ensure_df(closed)
    if df is None:
        return None
    date_col = "exit_date" if "exit_date" in df.columns else "date"
    if date_col not in df.columns:
        return None
    df["date"] = pd.to_datetime(df[date_col], errors="coerce").dt.date
    df = df.dropna(subset=["date", "profit"])
    df = df.sort_values("date")
    df["cumulative_pnl"] = df["profit"].cumsum()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["cumulative_pnl"], mode="lines+markers", name="Cumulative P&L", line=dict(color="#667eea", width=2)))
    if weekly_goal and weekly_goal > 0:
        fig.add_hline(y=weekly_goal, line_dash="dash", line_color="gray", annotation_text="Weekly goal")
    fig.update_layout(title="Equity Curve", xaxis_title="Date", yaxis_title="Cumulative P&L ($)", height=320, margin=dict(t=40, b=30, l=50, r=20), template="plotly_white")
    return fig


def create_strategy_performance_chart(strategies: Dict[str, Dict[str, Any]]) -> Optional[Any]:
    """
    Bar chart: strategy name vs total profit (and optionally win rate).
    strategies: { "EMA Crossover": {"wins": 5, "losses": 2, "profit": 120}, ... }
    """
    if not PLOTLY_AVAILABLE or not go or not strategies:
        return None
    names = []
    profits = []
    win_rates = []
    for name, data in strategies.items():
        names.append(name)
        profits.append(float(data.get("profit", 0)))
        total = (data.get("wins", 0) or 0) + (data.get("losses", 0) or 0)
        wr = (data.get("wins", 0) or 0) / total * 100 if total > 0 else 0
        win_rates.append(round(wr, 1))
    sorted_pairs = sorted(zip(names, profits, win_rates), key=lambda x: x[1], reverse=True)
    names, profits, win_rates = [x[0] for x in sorted_pairs], [x[1] for x in sorted_pairs], [x[2] for x in sorted_pairs]
    colors = ["#22c55e" if p >= 0 else "#ef4444" for p in profits]
    fig = go.Figure(data=[go.Bar(x=names, y=profits, marker_color=colors, text=[f"${p:,.0f}<br>{wr}% WR" for p, wr in zip(profits, win_rates)], textposition="outside")])
    fig.update_layout(title="Strategy Performance (P&L)", xaxis_title="Strategy", yaxis_title="Total P&L ($)", height=340, margin=dict(t=40, b=100, l=50, r=20), template="plotly_white", xaxis_tickangle=-45)
    return fig


def create_daily_pnl_chart(trades: List[Dict]) -> Optional[Any]:
    """
    Bar chart: daily P&L (each day one bar).
    """
    if not PLOTLY_AVAILABLE or not go:
        return None
    closed = [t for t in trades if t.get("status") == "closed" and t.get("profit") is not None]
    if not closed:
        fig = go.Figure()
        fig.add_annotation(text="No closed trades yet", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title="Daily P&L", height=280, margin=dict(t=40, b=30, l=50, r=20))
        return fig
    daily = defaultdict(float)
    for t in closed:
        d = (t.get("exit_date") or t.get("date") or "")[:10]
        if d:
            daily[d] += float(t.get("profit", 0))
    dates = sorted(daily.keys())
    pnls = [daily[d] for d in dates]
    colors = ["#22c55e" if p >= 0 else "#ef4444" for p in pnls]
    fig = go.Figure(data=[go.Bar(x=dates, y=pnls, marker_color=colors)])
    fig.update_layout(title="Daily P&L", xaxis_title="Date", yaxis_title="P&L ($)", height=280, margin=dict(t=40, b=60, l=50, r=20), template="plotly_white", xaxis_tickangle=-45)
    return fig


def create_stock_price_chart(symbol: str, period: str = "1mo") -> Optional[Any]:
    """
    Price line chart for a symbol (yfinance). Optional: add volume or RSI subplot.
    """
    if not PLOTLY_AVAILABLE or not go or not pd:
        return None
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval="1d", prepost=False, repair=True)
        if df is None or df.empty or len(df) < 2:
            return None
        df = df.reset_index()
        df["Date"] = pd.to_datetime(df["Date"]).dt.date
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["Date"], y=df["Close"], mode="lines", name="Close",
            line=dict(color="#667eea", width=2), fill="tozeroy", fillcolor="rgba(102,126,234,0.1)"
        ))
        fig.update_layout(
            title=f"{symbol} – Price ({period})",
            xaxis_title="Date", yaxis_title="Price ($)",
            height=320, margin=dict(t=40, b=40, l=50, r=20),
            template="plotly_white", hovermode="x unified"
        )
        return fig
    except Exception:
        return None


def create_win_rate_by_strategy_chart(strategies: Dict[str, Dict[str, Any]]) -> Optional[Any]:
    """
    Horizontal bar or gauge-style: win rate % per strategy.
    """
    if not PLOTLY_AVAILABLE or not go or not strategies:
        return None
    names = []
    rates = []
    totals = []
    for name, data in strategies.items():
        w = data.get("wins", 0) or 0
        l = data.get("losses", 0) or 0
        total = w + l
        if total > 0:
            names.append(name)
            rates.append(round(w / total * 100, 1))
            totals.append(total)
    if not names:
        fig = go.Figure()
        fig.add_annotation(text="No trade data yet", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title="Win Rate by Strategy", height=320, margin=dict(t=40, b=30, l=20, r=20))
        return fig
    sorted_pairs = sorted(zip(names, rates, totals), key=lambda x: x[1], reverse=True)
    names, rates, totals = [x[0] for x in sorted_pairs], [x[1] for x in sorted_pairs], [x[2] for x in sorted_pairs]
    fig = go.Figure(data=[go.Bar(y=names, x=rates, orientation="h", marker_color="#667eea", text=[f"{r}% ({t})" for r, t in zip(rates, totals)], textposition="outside")])
    fig.update_layout(title="Win Rate by Strategy", xaxis_title="Win Rate %", yaxis_title="Strategy", height=320, margin=dict(t=40, b=30, l=120, r=80), template="plotly_white")
    return fig
