"""
GeewoniStockSentry v6.0 - Simplified Integrated System
一个文件包含所有核心功能 + Token 追踪
"""

import streamlit as st
import yfinance as yf
import requests
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import os

# ==================== 配置 ====================
st.set_page_config(layout="wide", page_title="GEEWONI v6.0", page_icon="🚀")

# 环境变量
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8316634028:AAF_SK8AGtKxjJuKM0KnTjbpfOR-JRaoeCI")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "923799250")
OPENAI_KEY = os.getenv("OPENAI_KEY", "")

# 文件路径
CONFIG_FILE = Path("geewoni_config.json")
TRADES_FILE = Path("trades_history.json")
TOKEN_FILE = Path("token_usage.json")

# ==================== 样式 ====================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0f1419 100%);
}
h1 {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    font-size: 2.5rem !important;
    font-weight: 700 !important;
}
.stMetric {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
    padding: 1.2rem !important;
    border-radius: 16px !important;
    border: 1px solid rgba(102, 126, 234, 0.2);
}
.stButton button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
}
/* Token Counter Style */
.token-counter {
    position: fixed;
    top: 10px;
    right: 10px;
    background: rgba(102, 126, 234, 0.2);
    border: 2px solid #667eea;
    border-radius: 12px;
    padding: 10px 20px;
    color: white;
    font-weight: 600;
    z-index: 9999;
    backdrop-filter: blur(10px);
}
.token-warning {
    border-color: #ffc400;
    background: rgba(255, 196, 0, 0.2);
}
.token-danger {
    border-color: #ff4757;
    background: rgba(255, 71, 87, 0.2);
}
@media (max-width: 768px) {
    h1 { font-size: 1.8rem !important; }
    .token-counter {
        top: 60px;
        font-size: 0.8rem;
        padding: 5px 10px;
    }
}
</style>
""", unsafe_allow_html=True)

# ==================== Token 追踪系统 ====================

def load_token_usage():
    """加载 Token 使用记录"""
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)
    
    # 默认配置
    return {
        "total_tokens": 0,
        "total_cost": 0.0,
        "daily_tokens": 0,
        "daily_cost": 0.0,
        "monthly_tokens": 0,
        "monthly_cost": 0.0,
        "last_reset": datetime.now().strftime("%Y-%m-%d"),
        "model": "gpt-4o-mini",
        "pricing": {
            "gpt-4o-mini": {
                "input": 0.00015,   # $0.15 per 1M tokens
                "output": 0.0006    # $0.60 per 1M tokens
            },
            "gpt-4o": {
                "input": 0.0025,    # $2.50 per 1M tokens
                "output": 0.01      # $10.00 per 1M tokens
            }
        },
        "daily_limit": 1000000,    # 1M tokens/day
        "monthly_budget": 10.0,     # $10/month
        "history": []
    }

def save_token_usage(token_data):
    """保存 Token 使用记录"""
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f, indent=2)

def calculate_cost(tokens, model="gpt-4o-mini", token_type="input"):
    """计算成本"""
    token_data = load_token_usage()
    price_per_token = token_data["pricing"][model][token_type]
    return (tokens / 1000000) * price_per_token

def log_api_call(input_tokens, output_tokens, model="gpt-4o-mini"):
    """记录 API 调用"""
    token_data = load_token_usage()
    
    # 计算成本
    input_cost = calculate_cost(input_tokens, model, "input")
    output_cost = calculate_cost(output_tokens, model, "output")
    total_cost = input_cost + output_cost
    total_tokens = input_tokens + output_tokens
    
    # 更新统计
    token_data["total_tokens"] += total_tokens
    token_data["total_cost"] += total_cost
    token_data["daily_tokens"] += total_tokens
    token_data["daily_cost"] += total_cost
    token_data["monthly_tokens"] += total_tokens
    token_data["monthly_cost"] += total_cost
    
    # 记录历史
    token_data["history"].append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": total_cost
    })
    
    # 只保留最近100条记录
    if len(token_data["history"]) > 100:
        token_data["history"] = token_data["history"][-100:]
    
    # 检查是否需要重置每日计数
    today = datetime.now().strftime("%Y-%m-%d")
    if token_data["last_reset"] != today:
        token_data["daily_tokens"] = total_tokens
        token_data["daily_cost"] = total_cost
        token_data["last_reset"] = today
    
    save_token_usage(token_data)
    return token_data

def reset_monthly_usage():
    """重置月度使用（每月1号）"""
    token_data = load_token_usage()
    today = datetime.now()
    
    if today.day == 1:
        token_data["monthly_tokens"] = 0
        token_data["monthly_cost"] = 0
        save_token_usage(token_data)

# ==================== Telegram Bot ====================

class GeewoniBot:
    def send_alert(self, message):
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            r = requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=5)
            return r.status_code == 200
        except:
            return False

bot = GeewoniBot()

# ==================== 配置管理 ====================

def load_config():
    default = {
        "watchlist": ["NVDA", "PLTR", "RKLB", "SOFI", "OKLO", "MP"],
        "priority": ["NVDA", "OKLO", "MP"],
        "alert_pct": 3.0,
        "win_amount": 250,
        "loss_amount": 100,
        "weekly_goal": 1000,
        "weekly_profit": 0,
        "ai_model": "gpt-4o-mini",  # 或 "gpt-4o"
        "auto_log_tokens": True
    }
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            loaded = json.load(f)
            return {**default, **loaded}
    return default

def save_config(cfg):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f, indent=2)

def load_trades():
    if TRADES_FILE.exists():
        with open(TRADES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_trade(trade):
    trades = load_trades()
    trades.append(trade)
    with open(TRADES_FILE, 'w') as f:
        json.dump(trades, f, indent=2)

# ==================== 股票数据 ====================

@st.cache_data(ttl=300)
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

# ==================== 主应用 ====================

# 加载数据
config = load_config()
trades = load_trades()
token_data = load_token_usage()

# 重置月度统计（如果是1号）
reset_monthly_usage()

# ==================== Token Counter Display ====================

# 计算百分比
daily_pct = (token_data["daily_tokens"] / token_data["daily_limit"]) * 100
monthly_pct = (token_data["monthly_cost"] / token_data["monthly_budget"]) * 100

# 确定样式
counter_class = "token-counter"
if daily_pct > 80 or monthly_pct > 80:
    counter_class += " token-danger"
elif daily_pct > 50 or monthly_pct > 50:
    counter_class += " token-warning"

# Token 显示（右上角）
st.markdown(f"""
<div class="{counter_class}">
    <div style="font-size: 0.8rem; opacity: 0.8;">🤖 AI Usage</div>
    <div style="font-size: 1.1rem; font-weight: 700;">
        {token_data['daily_tokens']:,} / {token_data['daily_limit']:,}
    </div>
    <div style="font-size: 0.75rem; margin-top: 3px;">
        Today: ${token_data['daily_cost']:.4f} | Month: ${token_data['monthly_cost']:.2f}
    </div>
</div>
""", unsafe_allow_html=True)

# ==================== 主标题 ====================

st.markdown("# 🚀 GEEWONI Trading Center")
st.caption(f"v6.0 | {datetime.now().strftime('%Y-%m-%d %H:%M')} | Model: {config['ai_model']}")

# ==================== Tabs ====================

tabs = st.tabs(["📊 Dashboard", "🤖 AI Chat", "📈 Stocks", "📋 Journal", "⚙️ Settings", "💰 Token Usage"])

# TAB 1: Dashboard
with tabs[0]:
    st.header("📊 Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        progress = min(config["weekly_profit"] / config["weekly_goal"] * 100, 100)
        st.metric("💰 Weekly P&L", f"${config['weekly_profit']:,.0f}", f"{progress:.0f}%")
    
    with col2:
        today_trades = [t for t in trades if t.get('date', '').startswith(datetime.now().strftime('%Y-%m-%d'))]
        st.metric("📅 Today", f"${sum([t.get('profit', 0) for t in today_trades]):,.0f}", f"{len(today_trades)} trades")
    
    with col3:
        open_pos = [t for t in trades if t.get('status') == 'open']
        st.metric("💼 Positions", len(open_pos))
    
    with col4:
        st.metric("🤖 AI Tokens", f"{token_data['daily_tokens']:,}", f"${token_data['daily_cost']:.4f}")
    
    st.divider()
    
    # AI Top Picks
    st.subheader("🤖 AI Top 3 Picks")
    
    for i, symbol in enumerate(config['priority'][:3], 1):
        data = get_stock_data(symbol)
        if data:
            col1, col2 = st.columns([4, 1])
            with col1:
                confidence = 85 - (i * 5)
                st.markdown(f"""
                <div style='background: rgba(102,126,234,0.1); padding: 1rem; border-radius: 12px; margin: 0.5rem 0;'>
                    <h4>{'🥇' if i==1 else '🥈' if i==2 else '🥉'} {symbol} - ${data['price']:.2f} ({data['change_pct']:+.1f}%)</h4>
                    <p>📈 Entry: ${data['price']*0.99:.2f} | 🎯 Target: ${data['price']*1.05:.2f} | 🛑 Stop: ${data['price']*0.98:.2f}</p>
                    <p>💡 Confidence: {confidence}% | Strategy: Volume Breakout</p>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("📱 Send", key=f"send_{symbol}"):
                    bot.send_alert(f"🤖 {symbol}: ${data['price']:.2f}")
                    st.success("Sent!")
    
    st.divider()
    
    # Quick Actions
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
        if st.button("🔄 Reset Week", use_container_width=True):
            config["weekly_profit"] = 0
            save_config(config)
            st.rerun()

# TAB 2: AI Chat
with tabs[1]:
    st.header("🤖 AI Chat Assistant")
    
    # 模型选择
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"💬 Current Model: **{config['ai_model']}** | Daily: {token_data['daily_tokens']:,} tokens | ${token_data['daily_cost']:.4f}")
    with col2:
        if st.button("📊 Token Stats", use_container_width=True):
            st.switch_page = "Token Usage"
    
    # 聊天输入
    user_query = st.text_area("Ask AI anything about stocks or trading:", height=100, 
                              placeholder="例如: NVDA 入场点? 或 分析 PLTR 技术面")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🚀 Analyze", type="primary", use_container_width=True):
            if not user_query:
                st.warning("请输入问题")
            elif not OPENAI_KEY:
                st.error("⚠️ 请设置 OPENAI_KEY")
            else:
                with st.spinner("🤖 AI 分析中..."):
                    try:
                        from openai import OpenAI
                        client = OpenAI(api_key=OPENAI_KEY)
                        
                        # 调用 API
                        response = client.chat.completions.create(
                            model=config['ai_model'],
                            messages=[
                                {"role": "system", "content": "你是专业的股票交易分析师。简短专业地回答。"},
                                {"role": "user", "content": user_query}
                            ],
                            max_tokens=500
                        )
                        
                        # 获取使用量
                        usage = response.usage
                        answer = response.choices[0].message.content
                        
                        # 记录 Token
                        if config.get('auto_log_tokens', True):
                            log_api_call(usage.prompt_tokens, usage.completion_tokens, config['ai_model'])
                            st.rerun()  # 刷新显示
                        
                        # 显示回答
                        st.success("✅ 分析完成!")
                        st.markdown(f"""
                        <div style='background: rgba(102,126,234,0.1); padding: 1.5rem; border-radius: 12px; margin: 1rem 0;'>
                            {answer}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 显示使用量
                        st.caption(f"📊 Tokens: {usage.prompt_tokens} in + {usage.completion_tokens} out = {usage.total_tokens} total | Cost: ${calculate_cost(usage.prompt_tokens, config['ai_model'], 'input') + calculate_cost(usage.completion_tokens, config['ai_model'], 'output'):.6f}")
                        
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
    
    with col2:
        if st.button("📱 Send", use_container_width=True):
            if user_query:
                bot.send_alert(f"💬 Query: {user_query[:100]}...")
                st.success("Sent!")

# TAB 3: Live Stocks
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

# TAB 4: Trade Journal
with tabs[3]:
    st.header("📋 Trade Journal")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("✅ Record Trade")
        trade_type = st.radio("Type:", ["Buy", "Sell"], horizontal=True)
        t_symbol = st.selectbox("Symbol:", config['watchlist'])
        t_price = st.number_input("Price:", 0.0, 10000.0, 100.0)
        t_qty = st.number_input("Quantity:", 1, 1000, 10)
        
        if st.button("💾 Save", type="primary", use_container_width=True):
            new_trade = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "type": trade_type.lower(),
                "symbol": t_symbol,
                "price": t_price,
                "quantity": t_qty,
                "status": "open" if trade_type == "Buy" else "closed"
            }
            save_trade(new_trade)
            st.success(f"✅ {trade_type} recorded!")
            st.rerun()
    
    with col2:
        st.subheader("📜 Recent Trades")
        if trades:
            for trade in trades[-5:]:
                st.markdown(f"**{trade.get('symbol')}** - ${trade.get('price'):.2f} × {trade.get('quantity')}")
                st.caption(f"{trade.get('date')}")
        else:
            st.info("No trades yet")

# TAB 5: Settings
with tabs[4]:
    st.header("⚙️ Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Watchlist")
        watch = st.text_area("Watchlist:", ", ".join(config['watchlist']), height=100)
        config['watchlist'] = [s.strip().upper() for s in watch.split(",") if s.strip()]
        
        st.subheader("🎯 Priority")
        priority = st.text_area("Priority:", ", ".join(config['priority']), height=80)
        config['priority'] = [s.strip().upper() for s in priority.split(",") if s.strip()]
    
    with col2:
        st.subheader("💰 Trading")
        config['alert_pct'] = st.slider("Alert %:", 0.5, 10.0, config['alert_pct'], 0.1)
        config['win_amount'] = st.number_input("Win $:", value=config['win_amount'])
        config['loss_amount'] = st.number_input("Loss $:", value=config['loss_amount'])
        config['weekly_goal'] = st.number_input("Weekly Goal $:", value=config['weekly_goal'])
        
        st.subheader("🤖 AI Model")
        config['ai_model'] = st.selectbox("Model:", ["gpt-4o-mini", "gpt-4o"], 
                                          index=0 if config.get('ai_model') == 'gpt-4o-mini' else 1)
        config['auto_log_tokens'] = st.checkbox("Auto log tokens", value=config.get('auto_log_tokens', True))
    
    if st.button("💾 SAVE ALL", type="primary", use_container_width=True):
        save_config(config)
        st.success("✅ Saved!")
        time.sleep(1)
        st.rerun()

# TAB 6: Token Usage
with tabs[5]:
    st.header("💰 Token Usage & Cost Tracking")
    
    # 刷新按钮
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()
    
    # 关键指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Today Tokens", f"{token_data['daily_tokens']:,}", 
                 f"{(token_data['daily_tokens']/token_data['daily_limit']*100):.1f}%")
    
    with col2:
        st.metric("💵 Today Cost", f"${token_data['daily_cost']:.4f}")
    
    with col3:
        st.metric("📅 Month Tokens", f"{token_data['monthly_tokens']:,}")
    
    with col4:
        remaining = token_data['monthly_budget'] - token_data['monthly_cost']
        st.metric("💰 Budget Left", f"${remaining:.2f}", 
                 f"${token_data['monthly_cost']:.2f} / ${token_data['monthly_budget']:.2f}")
    
    st.divider()
    
    # 进度条
    st.subheader("📈 Daily Usage")
    daily_progress = min(token_data['daily_tokens'] / token_data['daily_limit'], 1.0)
    st.progress(daily_progress, text=f"{token_data['daily_tokens']:,} / {token_data['daily_limit']:,} tokens ({daily_progress*100:.1f}%)")
    
    st.subheader("💸 Monthly Budget")
    monthly_progress = min(token_data['monthly_cost'] / token_data['monthly_budget'], 1.0)
    st.progress(monthly_progress, text=f"${token_data['monthly_cost']:.2f} / ${token_data['monthly_budget']:.2f} ({monthly_progress*100:.1f}%)")
    
    st.divider()
    
    # 价格对比
    st.subheader("💲 Model Pricing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **gpt-4o-mini** (推荐)
        - Input: $0.15 / 1M tokens
        - Output: $0.60 / 1M tokens
        - 适合: 日常分析、快速回答
        """)
    
    with col2:
        st.markdown("""
        **gpt-4o**
        - Input: $2.50 / 1M tokens  
        - Output: $10.00 / 1M tokens
        - 适合: 复杂分析、深度研究
        """)
    
    st.divider()
    
    # 最近历史
    st.subheader("📜 Recent API Calls")
    
    if token_data.get('history'):
        history_df = []
        for call in token_data['history'][-10:]:
            history_df.append({
                "Time": call['timestamp'],
                "Model": call['model'],
                "In": call['input_tokens'],
                "Out": call['output_tokens'],
                "Total": call['input_tokens'] + call['output_tokens'],
                "Cost": f"${call['cost']:.6f}"
            })
        
        import pandas as pd
        st.dataframe(pd.DataFrame(history_df), use_container_width=True, hide_index=True)
    else:
        st.info("No API calls yet")
    
    st.divider()
    
    # 配置
    st.subheader("⚙️ Token Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_daily_limit = st.number_input("Daily Limit (tokens):", 
                                         min_value=10000, 
                                         max_value=10000000, 
                                         value=token_data['daily_limit'],
                                         step=100000)
    
    with col2:
        new_monthly_budget = st.number_input("Monthly Budget ($):", 
                                            min_value=1.0, 
                                            max_value=1000.0, 
                                            value=token_data['monthly_budget'],
                                            step=5.0)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Save Settings", use_container_width=True):
            token_data['daily_limit'] = new_daily_limit
            token_data['monthly_budget'] = new_monthly_budget
            save_token_usage(token_data)
            st.success("✅ Saved!")
            st.rerun()
    
    with col2:
        if st.button("🔄 Reset Daily", use_container_width=True):
            token_data['daily_tokens'] = 0
            token_data['daily_cost'] = 0.0
            save_token_usage(token_data)
            st.success("✅ Daily reset!")
            st.rerun()

# Footer
st.divider()
st.caption(f"🚀 GEEWONI v6.0 | 📱 Telegram | 🤖 Model: {config['ai_model']} | 💰 Today: ${token_data['daily_cost']:.4f}")