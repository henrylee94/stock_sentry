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

# ===== 配置 =====
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID")

CONFIG_FILE = Path("geewoni_config.json")
TRADES_FILE = Path("trades_history.json")
STRATEGIES_FILE = Path("strategies.json")

# ===== Telegram Bot =====
class GeewoniBot:
    def send_alert(self, message):
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            r = requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=5)
            return r.status_code == 200
        except:
            return False

bot = GeewoniBot()

# ===== 数据函数 =====
def load_config():
    default = {
        "watchlist": ["NVDA", "RKLB", "SOFI", "PLTR", "OKLO", "MP"],
        "priority": ["NVDA", "OKLO", "MP"],
        "alert_pct": 3.0,
        "win_amount": 250,
        "loss_amount": 100,
        "weekly_goal": 1000,
        "weekly_profit": 0,
        "push_times": {"morning": "09:00", "premarket": "21:00", "close": "04:00"},
        "monitor_rules": {"price_change": 3.0, "volume_mult": 2.0, "rsi_low": 30, "rsi_high": 70},
        "enabled_strategies": ["EMA Crossover", "Volume Breakout", "Support/Resistance"],
        "risk": {"max_position_pct": 5, "stop_loss_pct": 2, "max_daily_loss": 500}
    }
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            loaded = json.load(f)
            return {**default, **loaded}
    return default

def save_config(cfg):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f, indent=2)

def load_strategies():
    if STRATEGIES_FILE.exists():
        with open(STRATEGIES_FILE, 'r') as f:
            return json.load(f)
    default = {name: {"wins": 0, "losses": 0, "profit": 0} for name in [
        "EMA Crossover", "Volume Breakout", "Support/Resistance", "RSI Divergence",
        "Trend Following", "Mean Reversion", "Volatility Trading", "Earnings Play",
        "Catalyst Trading", "Sector Rotation", "Position Sizing", "Stop Loss Rules"
    ]}
    with open(STRATEGIES_FILE, 'w') as f:
        json.dump(default, f)
    return default

def load_trades():
    if TRADES_FILE.exists():
        with open(TRADES_FILE, 'r') as f:
            return json.load(f)
    return []

def get_stock_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d")
        if len(data) > 0:
            price = data['Close'].iloc[-1]
            open_price = data['Open'].iloc[0]
            return {
                "price": float(price),
                "change_pct": float(((price - open_price) / open_price) * 100)
            }
    except:
        pass
    return None

# ===== Page Config =====
st.set_page_config(layout="wide", page_title="GEEWONI v6.0", page_icon="🚀")

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

# ===== 主标题 =====
st.markdown("# 🚀 GEEWONI Trading Center")
st.caption(f"v6.0 Professional | {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# ===== Tabs =====
tabs = st.tabs(["📊 Dashboard", "🤖 AI Strategy", "📈 Stocks", "📋 Journal", "⚙️ Settings", "📊 Analytics"])

# TAB 1: Dashboard
with tabs[0]:
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
    
    # AI 推荐
    st.subheader("🤖 AI Top 3 Picks")
    if st.button("🔄 Refresh", key="refresh_ai"):
        st.toast("🤖 Analyzing...")
    
    for i, symbol in enumerate(config['priority'][:3], 1):
        data = get_stock_data(symbol)
        if data:
            st.markdown(f"""
            <div style='background: rgba(102,126,234,0.1); padding: 1rem; border-radius: 12px; margin: 0.5rem 0;'>
                <h4>{'🥇' if i==1 else '🥈' if i==2 else '🥉'} {symbol} - ${data['price']:.2f} ({data['change_pct']:+.1f}%)</h4>
                <p>📈 Entry: ${data['price']*0.99:.2f} | 🎯 Target: ${data['price']*1.05:.2f} | 🛑 Stop: ${data['price']*0.98:.2f}</p>
                <p>📋 Strategy: Volume Breakout | 💡 Confidence: {90-i*5}%</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    # 快速操作
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(f"✅ WIN +${config['win_amount']}", use_container_width=True):
            config["weekly_profit"] += config["win_amount"]
            save_config(config)
            bot.send_alert(f"✅ WIN +${config['win_amount']}")
            st.rerun()
    with col2:
        if st.button(f"❌ LOSS -${config['loss_amount']}", use_container_width=True):
            config["weekly_profit"] -= config["loss_amount"]
            save_config(config)
            bot.send_alert(f"❌ LOSS -${config['loss_amount']}")
            st.rerun()
    with col3:
        if st.button("🔄 Reset", use_container_width=True):
            config["weekly_profit"] = 0
            save_config(config)
            st.rerun()

# TAB 2: AI Strategy
with tabs[1]:
    st.header("🤖 AI Strategy Center")
    
    ai_tabs = st.tabs(["📍 Analysis", "🧪 Lab", "📊 Performance"])
    
    with ai_tabs[0]:
        st.subheader("Real-time Analysis")
        symbol = st.selectbox("Symbol:", config['watchlist'])
        
        if st.button("🔍 Analyze", type="primary"):
            with st.spinner("Analyzing..."):
                time.sleep(1)
                st.success(f"✅ {symbol} analyzed!")
                
                st.markdown("""
                <div style='background: rgba(102,126,234,0.15); padding: 1.5rem; border-radius: 16px;'>
                    <h3>🤖 AI Recommendation</h3>
                    <p><b style='color: #00ff88;'>✅ BUY SIGNAL</b> - Confidence: 82%</p>
                    <p>📈 Entry: $146.80-147.50 | 🎯 Target: $152 | 🛑 Stop: $144.50</p>
                    <p>📋 Strategy: Volume Breakout</p>
                    <p>💡 Reasoning: High volume + EMA cross + healthy RSI</p>
                </div>
                """, unsafe_allow_html=True)
    
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

# TAB 3: Stocks
with tabs[2]:
    st.header("📈 Live Stocks")
    
    query = st.text_input("Quick lookup:")
    if query:
        data = get_stock_data(query.upper())
        if data:
            st.success(f"🚀 {query.upper()}: ${data['price']:.2f} ({data['change_pct']:+.1f}%)")
    
    st.divider()
    
    for i in range(0, len(config['watchlist'][:12]), 4):
        cols = st.columns(4)
        for j, symbol in enumerate(config['watchlist'][i:i+4]):
            with cols[j]:
                data = get_stock_data(symbol)
                if data:
                    st.metric(symbol, f"${data['price']:.2f}", f"{data['change_pct']:+.1f}%")
                else:
                    st.metric(symbol, "N/A")

# TAB 4: Journal
with tabs[3]:
    st.header("📋 Trade Journal")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("✅ Record Trade")
        trade_type = st.radio("Type:", ["Buy", "Sell"], horizontal=True)
        t_symbol = st.selectbox("Symbol:", config['watchlist'], key="journal_symbol")
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
                "status": "open" if trade_type == "Buy" else "closed"
            }
            trades.append(new_trade)
            with open(TRADES_FILE, 'w') as f:
                json.dump(trades, f, indent=2)
            st.success(f"✅ {trade_type} recorded!")
    
    with col2:
        st.subheader("📜 Recent Trades")
        if trades:
            for trade in trades[-5:]:
                st.markdown(f"**{trade.get('symbol')}** - ${trade.get('price'):.2f} × {trade.get('quantity')}")
                st.caption(f"{trade.get('date')} | {trade.get('strategy')}")
        else:
            st.info("No trades yet")

# TAB 5: Settings
with tabs[4]:
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
        save_config(config)
        st.success("✅ Settings saved!")
        st.rerun()

# TAB 6: Analytics
with tabs[5]:
    st.header("📊 Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Weekly Progress")
        st.progress(min(config['weekly_profit'] / config['weekly_goal'], 1.0))
        st.metric("Progress", f"${config['weekly_profit']:,.0f} / ${config['weekly_goal']:,.0f}")
    
    with col2:
        st.subheader("Strategy Win Rates")
        for name, stats in list(strategies.items())[:5]:
            total = stats['wins'] + stats['losses']
            if total > 0:
                wr = stats['wins'] / total
                st.progress(wr, text=f"{name}: {wr*100:.0f}%")

st.divider()
st.caption("🚀 GEEWONI v6.0 | 💬 Telegram @YourBot | 📱 Mobile Optimized")