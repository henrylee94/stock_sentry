"""
GeewoniStockSentry v6.0 - Professional Trading Control Center
现代科技风格 | 手机优先 | 完整策略系统 | AI驱动
"""

import streamlit as st
import yfinance as yf
import requests
import json
import time
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import os

# set_page_config must be the first Streamlit command
st.set_page_config(layout="wide", page_title="GEEWONI v6.0", page_icon="🚀")

# Load .env from script dir so TELEGRAM_* are set
_script_dir = Path(__file__).resolve().parent
try:
    from dotenv import load_dotenv
    load_dotenv(_script_dir / ".env")
    load_dotenv(Path(".env"))
except Exception:
    pass

# ===== 配置 =====
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN_LOCAL") or os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Validate environment variables
if not TELEGRAM_TOKEN:
    st.warning("⚠️ TELEGRAM_TOKEN not set. Telegram alerts will be disabled.")
if not CHAT_ID:
    st.warning("⚠️ TELEGRAM_CHAT_ID not set. Telegram alerts will be disabled.")

from core import (
    CONFIG_FILE,
    TRADES_FILE,
    STRATEGIES_FILE,
    load_config,
    save_config,
    load_trades,
    save_trades,
    load_strategies,
)
from intent_detector import resolve_symbol

# ===== Telegram Bot =====
class GeewoniBot:
    def __init__(self):
        self.enabled = bool(TELEGRAM_TOKEN and CHAT_ID)
    
    def send_alert(self, message):
        """Send alert to Telegram if configured"""
        if not self.enabled:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            r = requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=5)
            return r.status_code == 200
        except Exception as e:
            print(f"Telegram error: {e}")
            return False

bot = GeewoniBot()

# ===== 数据函数 (core) – 真实数据：Finnhub → Yahoo → 仅失败时 demo =====
@st.cache_data(ttl=120)  # Cache 2 minutes
def get_stock_data(symbol):
    """Real data: try core data_manager (Finnhub + Yahoo), then Yahoo only, then demo only if both fail."""
    symbol = (symbol or "").upper().strip()
    if not symbol:
        return None

    # 1st: core data_manager (Finnhub real-time + Yahoo fallback)
    try:
        from core.data_manager import get_extended_stock_data
        ext = get_extended_stock_data(symbol, use_cache=True)
        if ext and ext.get("current_price") is not None:
            src = ext.get("data_source", "live")
            price = float(ext["current_price"])
            pct = float(ext.get("price_change_pct", 0))
            print(f"[PRICE] {symbol} → {src} | ${price:.2f} ({pct:+.2f}%)")
            return {"price": price, "change_pct": pct, "source": src}
    except Exception as e:
        print(f"[PRICE] {symbol} → data_manager failed: {e}")

    # 2nd: Yahoo Finance only
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="5d", interval="1d", prepost=True, repair=True)
        if data.empty or len(data) < 1:
            data = ticker.history(period="1mo", interval="1d")
        if not data.empty and len(data) > 0:
            price = float(data["Close"].iloc[-1])
            prev = float(data["Close"].iloc[-2]) if len(data) > 1 else price
            pct = ((price - prev) / prev * 100) if prev else 0
            print(f"[PRICE] {symbol} → Yahoo | ${price:.2f} ({pct:+.2f}%)")
            return {"price": price, "change_pct": pct, "source": "Yahoo"}
    except Exception as e:
        print(f"[PRICE] {symbol} → Yahoo failed: {e}")

    # 3rd: demo only when APIs fail (e.g. market closed, symbol invalid)
    print(f"[PRICE] {symbol} → demo (APIs failed or symbol unknown)")
    fallback_prices = {
        "NVDA": {"price": 142.35, "change_pct": 1.2},
        "PLTR": {"price": 28.45, "change_pct": -0.8},
        "OKLO": {"price": 15.67, "change_pct": 3.1},
        "RKLB": {"price": 8.92, "change_pct": 2.3},
        "SOFI": {"price": 11.25, "change_pct": -1.1},
        "MP": {"price": 1.85, "change_pct": 4.2},
    }
    result = fallback_prices.get(symbol)
    if result:
        result = {**result, "source": "demo"}
    return result


@st.cache_data(ttl=120)
def get_stock_data_extended(symbol):
    """Full details for one symbol (price, RSI, trend, support/resistance, volume, etc.). Dynamic – any symbol."""
    symbol = (symbol or "").upper().strip()
    if not symbol:
        return None
    try:
        from core.data_manager import get_extended_stock_data
        ext = get_extended_stock_data(symbol, use_cache=True)
        if ext and ext.get("current_price") is not None:
            return ext
    except Exception:
        pass
    # Fallback: basic from get_stock_data
    basic = get_stock_data(symbol)
    if not basic:
        return None
    return {
        "symbol": symbol,
        "current_price": basic["price"],
        "price_change_pct": basic["change_pct"],
        "data_source": basic.get("source", "?"),
        "rsi": None,
        "trend": "—",
        "support": None,
        "resistance": None,
        "volume_ratio": None,
        "day_high": None,
        "day_low": None,
    }

# ===== 现代科技风格 CSS =====
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0f1419 100%);
}
h1 {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.5rem !important;
    font-weight: 700 !important;
    text-align: center;
}
.stMetric {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
    padding: 1.2rem !important;
    border-radius: 16px !important;
    border: 1px solid rgba(102, 126, 234, 0.2);
}
.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
}
@media (max-width: 768px) {
    h1 { font-size: 1.8rem !important; }
}
</style>
""", unsafe_allow_html=True)

# ===== 加载数据 =====
config = load_config()
strategies = load_strategies()
trades = load_trades()

# ===== Sidebar: quick lookup + nav =====
with st.sidebar:
    st.markdown("### 🔍 Quick lookup")
    quick_sym = st.text_input("Symbol or name", key="sidebar_symbol", placeholder="e.g. AAPL, Amazon")
    if st.button("Look up", key="sidebar_lookup", type="primary"):
        if quick_sym and resolve_symbol(quick_sym.strip()):
            st.session_state["lookup_symbol"] = resolve_symbol(quick_sym.strip())
            st.session_state["nav_tab"] = "📈 Stocks"
            st.rerun()
    st.divider()
    nav_options = ["📊 Dashboard", "🤖 AI Strategy", "📈 Stocks", "📋 Journal", "⚙️ Settings", "📊 Analytics"]
    if "nav_tab" not in st.session_state:
        st.session_state["nav_tab"] = nav_options[0]
    if st.session_state.get("lookup_symbol"):
        st.session_state["nav_tab"] = "📈 Stocks"
    selected = st.radio("Go to", nav_options, index=nav_options.index(st.session_state["nav_tab"]) if st.session_state["nav_tab"] in nav_options else 0, key="nav_radio")
    st.session_state["nav_tab"] = selected

# ===== 主标题 =====
st.markdown("# 🚀 GEEWONI Trading Center")
st.caption(f"v6.0 Professional | {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# ===== Content by nav =====
nav_tab = st.session_state.get("nav_tab", "📊 Dashboard")

# TAB 1: Dashboard
if nav_tab == "📊 Dashboard":
    st.header("📊 Dashboard")
    
    # 关键指标
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        progress = min(config["weekly_profit"] / config["weekly_goal"] * 100, 100)
        st.metric("💰 Week", f"${config['weekly_profit']:,.0f}", f"{progress:.0f}%")
    with col2:
        today_trades = [t for t in trades if t.get('date', '').startswith(datetime.now().strftime('%Y-%m-%d'))]
        st.metric("📅 Today", f"${sum([t.get('profit', 0) for t in today_trades]):,.0f}", f"{len(today_trades)} trades")
    with col3:
        open_pos = [t for t in trades if t.get('status') == 'open']
        st.metric("💼 Positions", len(open_pos), f"Max {config['risk']['max_position_pct']}%")
    with col4:
        closed = [t for t in trades if t.get('status') == 'closed']
        wr = (len([t for t in closed if t.get('profit', 0) > 0]) / len(closed) * 100) if closed else 0
        st.metric("📊 Win Rate", f"{wr:.1f}%", f"{len(closed)} trades")
    
    st.divider()
    
    # Your list – clickable buttons; no API calls here. Click a symbol then open 📈 Stocks to load data.
    st.subheader("🤖 Top picks from your list")
    priority = config.get("priority") or config.get("watchlist") or []
    if not priority:
        st.info("Add symbols in **Settings → Basic** (Priority or Watchlist) to see picks here.")
    else:
        st.caption("Click a symbol below, then choose **📈 Stocks** in the sidebar (or use **Quick lookup** there) to load data.")
        for i in range(0, min(len(priority), 10), 5):
            cols = st.columns(5)
            for j, symbol in enumerate(priority[i:i+5]):
                with cols[j]:
                    if st.button(symbol, key=f"home_wl_{symbol}", use_container_width=True):
                        st.session_state["lookup_symbol"] = symbol
                        st.rerun()
        if st.session_state.get("lookup_symbol"):
            st.success(f"Selected **{st.session_state.get('lookup_symbol')}**. Choose **📈 Stocks** in the sidebar to load data.")
    
    st.divider()
    
    # 快速操作
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(f"✅ WIN +${config['win_amount']}", use_container_width=True):
            config["weekly_profit"] += config["win_amount"]
            if save_config(config):
                if bot.send_alert(f"✅ WIN +${config['win_amount']}"):
                    st.success("Alert sent!")
                st.rerun()
    with col2:
        if st.button(f"❌ LOSS -${config['loss_amount']}", use_container_width=True):
            config["weekly_profit"] -= config["loss_amount"]
            if save_config(config):
                if bot.send_alert(f"❌ LOSS -${config['loss_amount']}"):
                    st.success("Alert sent!")
                st.rerun()
    with col3:
        if st.button("🔄 Reset", use_container_width=True):
            config["weekly_profit"] = 0
            if save_config(config):
                st.success("Reset successful!")
                st.rerun()

# TAB 2: AI Strategy
elif nav_tab == "🤖 AI Strategy":
    st.header("🤖 AI Strategy Center")
    
    ai_tabs = st.tabs(["📍 Analysis", "🧪 Lab", "📊 Performance"])
    
    with ai_tabs[0]:
        st.subheader("Real-time Analysis")
        watchlist = config.get("watchlist") or config.get("priority") or []
        symbol_from_list = st.selectbox("From watchlist:", [""] + watchlist, format_func=lambda x: x or "— Select or type below —") if watchlist else ""
        symbol_custom = st.text_input("Or type any symbol or name:", placeholder="e.g. AAPL, Amazon, Tesla")
        raw_symbol = (symbol_custom.strip() or symbol_from_list) if symbol_custom or symbol_from_list else (watchlist[0] if watchlist else "")
        symbol = resolve_symbol(raw_symbol) if raw_symbol else ""
        
        if st.button("🔍 Analyze", type="primary") and symbol:
            with st.spinner(f"Loading {symbol}..."):
                ext = get_stock_data_extended(symbol)
            if ext:
                price = float(ext.get("current_price", 0))
                pct = float(ext.get("price_change_pct", 0))
                rsi = ext.get("rsi")
                trend = ext.get("trend") or "—"
                support = ext.get("support")
                resistance = ext.get("resistance")
                rsi_s = f"{float(rsi):.0f}" if rsi is not None else "—"
                sup_s = f"${float(support):.2f}" if support is not None else "—"
                res_s = f"${float(resistance):.2f}" if resistance is not None else "—"
                # Short interpretation from data (no hardcoded result)
                if rsi is not None:
                    if rsi < 30:
                        signal, color = "Oversold (RSI &lt; 30)", "#00ff88"
                    elif rsi > 70:
                        signal, color = "Overbought (RSI &gt; 70)", "#ff8866"
                    else:
                        signal, color = "Neutral RSI", "#ffcc00"
                else:
                    signal, color = "—", "#888"
                st.success(f"✅ {symbol} analyzed")
                st.markdown(f"""
                <div style='background: rgba(102,126,234,0.15); padding: 1.5rem; border-radius: 16px;'>
                    <h3>📊 {symbol} – Real-time data</h3>
                    <p style='font-size:1.25rem'><b>${price:.2f}</b> <span style='color:{"#0f0" if pct >= 0 else "#f44"}'>({pct:+.2f}%)</span> &nbsp; RSI: {rsi_s} &nbsp; Trend: {trend}</p>
                    <p>Support: {sup_s} &nbsp;|&nbsp; Resistance: {res_s}</p>
                    <p><b style='color: {color}'>{signal}</b></p>
                    <p style='color:#888; font-size:0.9rem'>For full AI recommendation (entry/target/stop), use the Telegram bot.</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning(f"No data for {symbol}. Check symbol or try again.")
    
    with ai_tabs[1]:
        st.subheader("🧪 Weekly Strategy Lab")
        st.info("Create and test a strategy for this week!")
        
        base = st.selectbox("Base Strategy:", config['enabled_strategies'])
        target = st.number_input("Daily Target ($)", 100, 1000, 200, 50)
        
        if st.button("💾 Save Strategy", type="primary"):
            st.success("Saved for this week!")
    
    with ai_tabs[2]:
        st.subheader("📊 Performance")
        
        perf_data = []
        for name, stats in strategies.items():
            total = stats['wins'] + stats['losses']
            wr = (stats['wins']/total*100) if total > 0 else 0
            perf_data.append({
                "Strategy": name,
                "Trades": total,
                "Win Rate": f"{wr:.1f}%",
                "P&L": f"${stats['profit']:,.0f}",
                "Status": "✅" if name in config['enabled_strategies'] else "⏸️"
            })
        
        st.dataframe(pd.DataFrame(perf_data), use_container_width=True, hide_index=True)

# TAB 3: Stocks – dynamic lookup, any symbol; watchlist is optional quick-select
elif nav_tab == "📈 Stocks":
    st.header("📈 Live Stocks")
    st.caption("Search any symbol above or use **Quick lookup** in the sidebar. Type another symbol and click Look up to switch — no refresh needed.")
    
    query = st.text_input("🔍 Symbol or name (e.g. NVDA, Amazon, Tesla)", placeholder="Type ticker or company name, then click Look up", key="stock_query")
    col_btn, _ = st.columns([1, 4])
    with col_btn:
        do_lookup = st.button("Look up", type="primary")
    # Allow Details button from watchlist to trigger lookup on rerun
    if st.session_state.get("lookup_symbol"):
        query = st.session_state.get("lookup_symbol") or query
        do_lookup = True
        del st.session_state["lookup_symbol"]
    
    if do_lookup and query:
        sym = resolve_symbol(query.strip())
        with st.spinner(f"Loading {sym}..."):
            ext = get_stock_data_extended(sym)
        if ext:
            src = ext.get("data_source", "?")
            def _num(v, fmt="${:.2f}"):
                if v is None: return "—"
                try: return fmt.format(float(v))
                except (TypeError, ValueError): return str(v) if v != "" else "—"
            rsi = ext.get("rsi")
            rsi_s = f"{float(rsi):.0f}" if rsi is not None else "—"
            sup_val = ext.get("support")
            res_val = ext.get("resistance")
            sup = _num(sup_val)
            res = _num(res_val)
            dlo = _num(ext.get("day_low"))
            dhi = _num(ext.get("day_high"))
            vol = ext.get("volume_ratio")
            vol_s = f"{float(vol):.1f}x" if vol is not None else "—"
            price = float(ext.get("current_price", 0))
            # Suggested in/out from support/resistance (for decision making)
            entry_sug = _num(price) if price else "—"
            target_sug = res if res_val is not None else _num(price * 1.02) if price else "—"
            stop_sug = sup if sup_val is not None else _num(price * 0.98) if price else "—"
            st.markdown(f"""
            <div style='background: rgba(102,126,234,0.12); padding: 1.25rem; border-radius: 12px; margin: 0.75rem 0; border-left: 4px solid #667eea;'>
                <h3>{ext.get('symbol', sym)} <small style='color:#888'>{src}</small></h3>
                <p style='font-size:1.5rem; margin:0.5rem 0'><b>${price:.2f}</b> <span style='color:{"#0f0" if (ext.get("price_change_pct") or 0) >= 0 else "#f44"}'>({float(ext.get("price_change_pct",0)):+.2f}%)</span></p>
                <table style='width:100%; margin-top:0.5rem; font-size:0.95rem'>
                <tr><td>RSI</td><td>{rsi_s}</td><td>Trend</td><td>{ext.get('trend') or "—"}</td></tr>
                <tr><td>Support</td><td>{sup}</td><td>Resistance</td><td>{res}</td></tr>
                <tr><td>Day range</td><td>{dlo} – {dhi}</td><td>Vol ratio</td><td>{vol_s}</td></tr>
                <tr><td colspan="3" style='padding-top:0.4rem; border-top:1px solid rgba(102,126,234,0.3)'><b>Suggested:</b> Entry {entry_sug} → Target {target_sug} | Stop {stop_sug}</td></tr>
                </table>
                <p style='margin-top:0.5rem; color:#888; font-size:0.85rem'>{ext.get('last_update') or ''}</p>
            </div>
            """, unsafe_allow_html=True)
            # Price chart to enrich details
            try:
                from dashboard_components.charts import create_stock_price_chart
                chart_fig = create_stock_price_chart(sym, period="1mo")
                if chart_fig:
                    st.plotly_chart(chart_fig, use_container_width=True)
            except Exception:
                pass
        else:
            st.warning(f"No data for {sym}. Check symbol or try later.")
    
    st.divider()
    st.subheader("Your watchlist (quick select)")
    watchlist = config.get("watchlist") or config.get("priority") or []
    if watchlist:
        # Buttons only: click sets lookup and triggers one fetch (no bulk get_stock_data on load)
        for i in range(0, min(len(watchlist), 12), 4):
            cols = st.columns(4)
            for j, symbol in enumerate(watchlist[i:i+4]):
                with cols[j]:
                    if st.button(symbol, key=f"wl_{symbol}", use_container_width=True):
                        st.session_state["lookup_symbol"] = symbol
                        st.rerun()
    else:
        st.info("No watchlist yet. Add symbols in **Settings → Basic** (Watchlist), or search any symbol above.")

# TAB 4: Journal
elif nav_tab == "📋 Journal":
    st.header("📋 Trade Journal")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("✅ Record Trade")
        trade_type = st.radio("Type:", ["Buy", "Sell"], horizontal=True)
        watchlist_j = config.get("watchlist") or config.get("priority") or []
        t_symbol_list = st.selectbox("Symbol (watchlist):", watchlist_j if watchlist_j else [""], key="journal_symbol") or ""
        t_symbol_custom = st.text_input("Or type symbol or name:", placeholder="e.g. AAPL or Amazon", key="journal_custom")
        t_symbol = resolve_symbol((t_symbol_custom.strip() if t_symbol_custom else "") or t_symbol_list or "") or ""
        t_price = st.number_input("Price:", 0.0, 10000.0, 100.0)
        t_qty = st.number_input("Quantity:", 1, 1000, 10)
        t_strategy = st.selectbox("Strategy:", config['enabled_strategies'])
        
        if st.button("💾 Save Trade", type="primary"):
            new_trade = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "type": trade_type.lower(),
                "symbol": t_symbol,
                "price": t_price,
                "quantity": t_qty,
                "strategy": t_strategy,
                "status": "open" if trade_type == "Buy" else "closed",
                "profit": 0 if trade_type == "Buy" else None
            }
            trades.append(new_trade)
            try:
                if save_trades(trades):
                    st.success(f"✅ {trade_type} recorded!")
                    st.rerun()
                else:
                    st.error("Error saving trade")
            except Exception as e:
                st.error(f"Error saving trade: {e}")
    
    with col2:
        st.subheader("📜 Recent Trades")
        if trades:
            for trade in trades[-5:]:
                st.markdown(f"**{trade.get('symbol')}** - ${trade.get('price'):.2f} × {trade.get('quantity')}")
                st.caption(f"{trade.get('date')} | {trade.get('strategy')}")
        else:
            st.info("No trades yet")

# TAB 5: Settings
elif nav_tab == "⚙️ Settings":
    st.header("⚙️ Control Center")
    
    setting_tabs = st.tabs(["📊 Basic", "⏰ Push Times", "👀 Monitor", "🎯 Strategies", "⚠️ Risk"])
    
    with setting_tabs[0]:
        st.subheader("Basic Settings")
        
        col1, col2 = st.columns(2)
        with col1:
            watch = st.text_area("Watchlist:", ", ".join(config['watchlist']))
            config['watchlist'] = [s.strip().upper() for s in watch.split(",") if s.strip()]
        
        with col2:
            priority = st.text_area("Priority:", ", ".join(config['priority']))
            config['priority'] = [s.strip().upper() for s in priority.split(",") if s.strip()]
        
        config['alert_pct'] = st.slider("Alert %:", 0.5, 10.0, config['alert_pct'], 0.1)
        config['win_amount'] = st.number_input("Win $:", value=config['win_amount'])
        config['loss_amount'] = st.number_input("Loss $:", value=config['loss_amount'])
        config['weekly_goal'] = st.number_input("Goal $:", value=config['weekly_goal'])
    
    with setting_tabs[1]:
        st.subheader("⏰ Push Times (MY Time)")
        for key in ['morning', 'premarket', 'close']:
            config['push_times'][key] = st.time_input(f"{key.title()}:", 
                value=datetime.strptime(config['push_times'].get(key, "09:00"), "%H:%M").time()).strftime("%H:%M")
    
    with setting_tabs[2]:
        st.subheader("👀 Monitor Rules")
        config['monitor_rules']['price_change'] = st.slider("Price Change %:", 1.0, 10.0, config['monitor_rules']['price_change'])
        config['monitor_rules']['volume_mult'] = st.slider("Volume Mult:", 1.0, 5.0, config['monitor_rules']['volume_mult'])
        config['monitor_rules']['rsi_low'] = st.slider("RSI Low:", 10, 40, config['monitor_rules']['rsi_low'])
        config['monitor_rules']['rsi_high'] = st.slider("RSI High:", 60, 90, config['monitor_rules']['rsi_high'])
    
    with setting_tabs[3]:
        st.subheader("🎯 Strategies")
        all_strats = list(strategies.keys())
        config['enabled_strategies'] = st.multiselect("Enabled:", all_strats, default=config['enabled_strategies'])
    
    with setting_tabs[4]:
        st.subheader("⚠️ Risk Management")
        config['risk']['max_position_pct'] = st.slider("Max Position %:", 1, 20, config['risk']['max_position_pct'])
        config['risk']['stop_loss_pct'] = st.slider("Stop Loss %:", 1, 10, config['risk']['stop_loss_pct'])
        config['risk']['max_daily_loss'] = st.number_input("Max Daily Loss $:", value=config['risk']['max_daily_loss'])
    
    if st.button("💾 SAVE ALL SETTINGS", type="primary", use_container_width=True):
        if save_config(config):
            st.success("✅ Settings saved!")
            st.rerun()
        else:
            st.error("❌ Failed to save settings")

# TAB 6: Analytics
elif nav_tab == "📊 Analytics":
    st.header("📊 Analytics")
    
    # Top row: weekly progress + key metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        progress_pct = min(config['weekly_profit'] / config['weekly_goal'], 1.0) if config['weekly_goal'] else 0
        st.progress(progress_pct)
        st.metric("Weekly Progress", f"${config['weekly_profit']:,.0f} / ${config['weekly_goal']:,.0f}", f"{progress_pct*100:.0f}%")
    with col2:
        closed = [t for t in trades if t.get('status') == 'closed']
        wins = len([t for t in closed if (t.get('profit') or 0) > 0])
        total = len(closed)
        wr = (wins / total * 100) if total > 0 else 0
        st.metric("Win Rate", f"{wr:.1f}%", f"{wins}/{total} trades")
    with col3:
        total_pnl = sum(t.get('profit', 0) or 0 for t in closed)
        st.metric("Total P&L (closed)", f"${total_pnl:,.2f}", "")
    
    st.divider()
    
    # Charts (Phase 3)
    try:
        from dashboard_components.charts import (
            create_equity_curve,
            create_strategy_performance_chart,
            create_daily_pnl_chart,
            create_win_rate_by_strategy_chart,
        )
        # Normalize trade keys for charts (support both 'price' and 'entry_price')
        trades_for_charts = []
        for t in trades:
            tc = dict(t)
            if 'profit' not in tc and t.get('status') == 'closed':
                tc['profit'] = 0
            if 'exit_date' not in tc and t.get('status') == 'closed':
                tc['exit_date'] = t.get('date', '')
            trades_for_charts.append(tc)
        
        st.subheader("📈 Equity Curve")
        fig_equity = create_equity_curve(trades_for_charts, config.get('weekly_goal'))
        if fig_equity:
            st.plotly_chart(fig_equity, use_container_width=True)
        
        st.subheader("📊 Strategy Performance")
        fig_strat = create_strategy_performance_chart(strategies)
        if fig_strat:
            st.plotly_chart(fig_strat, use_container_width=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📅 Daily P&L")
            fig_daily = create_daily_pnl_chart(trades_for_charts)
            if fig_daily:
                st.plotly_chart(fig_daily, use_container_width=True)
        with c2:
            st.subheader("🎯 Win Rate by Strategy")
            fig_wr = create_win_rate_by_strategy_chart(strategies)
            if fig_wr:
                st.plotly_chart(fig_wr, use_container_width=True)
    except ImportError as e:
        st.info("Install plotly for charts: pip install plotly")
        st.progress(min(config['weekly_profit'] / config['weekly_goal'], 1.0))
        st.metric("Progress", f"${config['weekly_profit']:,.0f} / ${config['weekly_goal']:,.0f}")
        for name, stats in list(strategies.items())[:5]:
            total = stats['wins'] + stats['losses']
            if total > 0:
                wr = stats['wins'] / total
                st.progress(wr, text=f"{name}: {wr*100:.0f}%")

st.divider()
st.caption("🚀 GEEWONI v6.0 | 💬 Telegram @YourBot | 📱 Mobile Optimized")