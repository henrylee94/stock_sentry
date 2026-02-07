import streamlit as st
import yfinance as yf
import requests
import json
import time
from pathlib import Path

TELEGRAM_TOKEN = "8316634028:AAF_SK8AGtKxjJuKM0KnTjbpfOR-JRaoeCI"
CHAT_ID = "923799250"

class GeewoniBot:
    def __init__(self):
        self.buffer = []
        self.last_sent = 0
        
    def send_alert(self, message):
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=5)
            return True
        except:
            return False
    
    def add_alert(self, alerts, config):
        self.buffer.extend(alerts)
        if time.time() - self.last_sent > 30 and self.buffer:
            header = config["alert_header"].format(count=len(self.buffer), time=time.strftime("%H:%M"))
            msg = f"{header}\n\n" + "\n".join(self.buffer[-8:])
            if self.send_alert(msg):
                self.buffer = []
                self.last_sent = time.time()

bot = GeewoniBot()
CONFIG_FILE = Path("geewoni_config.json")

def load_config():
    default = {
        "watchlist": ["NVDA", "RKLB", "SOFI", "PLTR", "OKLO", "BMNR"],
        "priority": ["NVDA", "OKLO", "BMNR", "RKLB", "SOFI", "PLTR"],
        "alert_pct": 3.0,
        "alert_header": "🚨 <b>GEEWONI US STOCKS ({count})</b> | {time}",
        "alert_format": "🚨 {symbol} {pct:+.1f}%\n💰 ${price:.2f}",
        "win_amount": 250,
        "loss_amount": 100,
        "weekly_goal": 1000,
        "weekly_profit": 0
    }
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                loaded = json.load(f)
                return {**default, **loaded}
        except:
            pass
    return default

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

config = load_config()

st.set_page_config(layout="wide", page_title="GeewoniStockSentry v5.1")
st.markdown("""
<style>
.stApp {background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%);}
h1 {color: #00d4ff !important; text-align: center; font-size: 2.8rem;}
h2 {color: #00ff88 !important;}
.stMetric > label {color: white !important;}
.stMetric > div > span {color: #00d4ff !important;}
button {background: linear-gradient(45deg, #16213e, #0f3460); color: white; border-radius: 12px;}
</style>
""", unsafe_allow_html=True)

st.title("🚀 GeewoniStockSentry v5.1")
tab1, tab2, tab3 = st.tabs(["⚙️ Settings", "📈 Dashboard", "🎯 Strategy"])

with tab1:
    st.header("🎛️ Control Panel")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**📊 Watchlist**")
        watch_input = st.text_area("", value=", ".join(config["watchlist"]), height=120)
        config["watchlist"] = [s.strip().upper() for s in watch_input.split(",") if s.strip()]
    
    with col2:
        st.markdown("**🔥 Priority (Alerts)**")
        priority_input = st.text_area("", value=", ".join(config["priority"]), height=120)
        config["priority"] = [s.strip().upper() for s in priority_input.split(",") if s.strip()]
    
    col1, col2 = st.columns(2)
    config["alert_pct"] = col1.slider("Alert %", 0.5, 10.0, config["alert_pct"], 0.1)
    
    col1, col2, col3 = st.columns(3)
    config["win_amount"] = col1.number_input("Win $", value=config["win_amount"])
    config["loss_amount"] = col2.number_input("Loss $", value=config["loss_amount"])
    config["weekly_goal"] = col3.number_input("Goal $", value=config["weekly_goal"])
    
    if st.button("💾 SAVE", use_container_width=True):
        save_config(config)
        st.success("✅ SAVED!")
        st.rerun()

with tab2:
    st.header("📈 Live Dashboard")
    
    # P&L Header
    col1, col2, col3, col4 = st.columns([2,1.2,1,1])
    with col1:
        st.markdown("**📊 Live US Stocks**")
    with col2:
        progress = min(config["weekly_profit"] / config["weekly_goal"] * 100, 100)
        st.metric("💰 Weekly", f"${int(config['weekly_profit']):,}/{config['weekly_goal']:,}", f"{progress:.0f}%")
    
    with col3:
        if st.button(f"✅ WIN\n${int(config['win_amount']):,}", use_container_width=True):
            config["weekly_profit"] += config["win_amount"]
            save_config(config)
            bot.send_alert(f"✅ <b>GEEWONI WIN!</b>\n💰 +${int(config['win_amount']):,}")
            st.rerun()
    
    with col4:
        if st.button(f"❌ LOSS\n${int(config['loss_amount']):,}", use_container_width=True):
            config["weekly_profit"] -= config["loss_amount"]
            save_config(config)
            bot.send_alert(f"❌ <b>GEEWONI Loss</b>\n💸 -${int(config['loss_amount']):,}")
            st.rerun()
    
    # Quick Stock Check
    st.markdown("**🔍 Quick Lookup**")
    query = st.text_input("Enter symbol:").strip().upper()
    if query:
        try:
            ticker = yf.Ticker(query)
            data = ticker.history(period="1d")
            if len(data) > 0:
                price = data['Close'].iloc[-1]
                open_price = data['Open'].iloc[0]
                change_pct = ((price - open_price) / open_price) * 100
                st.success(f"🚀 {query}: ${price:.2f} ({change_pct:+.1f}%)")
                if st.button(f"📱 Send {query} to Telegram", key=f"send_{query}"):
                    bot.send_alert(f"🔍 <b>{query}:</b>\n💰 ${price:.2f} ({change_pct:+.1f}%)")
            else:
                st.error("No data")
        except:
            st.error("Invalid symbol")
    
    # Live Grid
    watchlist = config["watchlist"][:16]
    for i in range(0, len(watchlist), 4):
        cols = st.columns(4)
        for j, symbol in enumerate(watchlist[i:i+4]):
            with cols[j]:
                try:
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(period="1d")
                    if len(data) > 0:
                        price = data['Close'].iloc[-1]
                        open_price = data['Open'].iloc[0]
                        change_pct = ((price - open_price) / open_price) * 100
                        
                        if symbol in config["priority"] and abs(change_pct) >= config["alert_pct"]:
                            alert_msg = config["alert_format"].format(symbol=symbol, pct=change_pct, price=price)
                            bot.add_alert([alert_msg], config)
                        
                        color = "inverse" if abs(change_pct) >= config["alert_pct"] else "normal"
                        st.metric(symbol, f"${price:.2f}", f"{change_pct:+.1f}%", delta_color=color)
                except:
                    st.metric(symbol, "N/A")

with tab3:
    st.header("🎯 Strategy")
    if st.button("🔥 Analyze Priority Stocks"):
        for symbol in config["priority"][:8]:
            try:
                data = yf.download(symbol, period="2mo", progress=False)
                if len(data) > 20:
                    ema5 = data['Close'].ewm(span=5).mean().iloc[-1]
                    ema20 = data['Close'].ewm(span=20).mean().iloc[-1]
                    trend = "🟢 BULLISH" if ema5 > ema20 else "🔴 BEARISH"
                    col1, col2 = st.columns(2)
                    col1.metric(symbol, f"${data['Close'].iloc[-1]:.2f}")
                    col2.metric("Trend", trend)
            except:
                st.write(f"{symbol}: Loading...")

st.info(f"📱 Phone: http://192.168.50.55:8501 | 🤖 Telegram Bot: /nvda /stats | Alerts: {config['alert_pct']}%")
