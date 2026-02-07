import logging
import asyncio
import re
import pandas as pd
import numpy as np
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yfinance as yf
import json
from pathlib import Path
import os
from openai import OpenAI
from datetime import datetime
from dotenv import load_dotenv  # ← ADD THIS LINE

# LOAD .env FILE (CRITICAL)
load_dotenv()  # ← ADD THIS LINE

# CLOUD SETUP + TOKEN PROTECTION
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CONFIG_FILE = Path("geewoni_config.json")
OPENAI_KEY = os.getenv("OPENAI_KEY")
# Cost control
ai_usage_today = 0
daily_limit = 1000  # $0.50 max/day

client = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None
ENVIRONMENT = os.getenv('ENVIRONMENT', 'local')

print(f"🧠 GEEWONI AI TRADING BRAIN v6.2")
print(f"{'✅ gpt-4o-mini LIVE' if client else '⚠️ ADD OPENAI_API_KEY'}")

def load_config():
    default = {
        "weekly_profit": 0, 
        "weekly_goal": 1000, 
        "priority": ["NVDA","OKLO","BMNR","RKLB","SOFI","PLTR"], 
        "alert_pct": 3.0,
        "ai_usage": 0
    }
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return {**default, **json.load(f)}
        except:
            pass
    return default

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

config = load_config()

def get_live_data(symbol):
    """LIVE yfinance - Pre-market/After-hours/Weekend + FULL TA"""
    try:
        ticker = yf.Ticker(symbol)
        # 5min + pre/after market
        data = ticker.history(period="30d", interval="5m", prepost=True)
        
        if len(data) > 50:
            df = data.tail(100).copy()
            df['EMA5'] = df['Close'].ewm(span=5).mean()
            df['EMA20'] = df['Close'].ewm(span=20).mean()
            df['RSI'] = compute_rsi(df['Close'], 14)
            df['Support'] = df['Low'].rolling(20).min()
            df['Resistance'] = df['High'].rolling(20).max()
            
            current = df.iloc[-1]
            prev = df.iloc[-2]
            
            return {
                'symbol': symbol,
                'price': current['Close'],
                'change_pct': ((current['Close'] - prev['Close']) / prev['Close']) * 100,
                'volume_ratio': current['Volume'] / prev['Volume'],
                'ema5': current['EMA5'],
                'ema20': current['EMA20'],
                'rsi': current['RSI'],
                'support': current['Support'],
                'resistance': current['Resistance'],
                'trend': 'BULL' if current['EMA5'] > current['EMA20'] else 'BEAR',
                'breakout': current['Close'] > current['Resistance']
            }
        return None
    except:
        return None

def compute_rsi(prices, window=14):
    """RSI Calculation"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

async def ai_trading_brain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """EVERYTHING → AI (Live data injected)"""
    global ai_usage_today
    
    # SAFE MESSAGE HANDLING
    if not update.message or not update.message.text:
        await update.effective_message.reply_text("💬 Type: NVDA entry point?")
        return
        
    user_query = update.message.text.strip()
    symbols = re.findall(r'\b[A-Z]{2,5}\b', user_query)
    
    # STEP 1: LIVE DATA COLLECTION
    live_data = {}
    for symbol in set(symbols)[:3]:  # Max 3 unique
        data = get_live_data(symbol)
        if data:
            live_data[symbol] = data
    
    # STEP 2: AI ANALYSIS (gpt-4o-mini)
    if client and ai_usage_today < daily_limit:
        try:
            ai_usage_today += 1
            config['ai_usage'] = ai_usage_today
            save_config(config)
            
            # LIVE DATA CONTEXT
            data_context = []
            for symbol, data in live_data.items():
                data_context.append(
                    f"{symbol}: ${data['price']:.2f} {data['change_pct']:+.1f}% | "
                    f"Trend: {data['trend']} | RSI: {data['rsi']:.0f} | "
                    f"S: ${data['support']:.2f} R: ${data['resistance']:.2f}"
                )
            
            system_prompt = f"""GEEWONI AI TRADING BRAIN - LIVE DATA ANALYSIS

LIVE MARKET DATA:
{chr(10).join(data_context) if data_context else 'No live data'}

YOUR P&L: ${config['weekly_profit']}/{config['weekly_goal']} ({config['weekly_profit']/config['weekly_goal']*100:.0f}%)
PRIORITY STOCKS: {', '.join(config['priority'])}

RULES:
1. Entry: BUY only above resistance + EMA bull + RSI 40-70
2. Exit: SELL at resistance or EMA bear cross  
3. Risk: Always give 2-5% stop loss from entry
4. Position: 1-2% portfolio risk max

RESPONSE FORMAT:
SYMBOL: $price (+X.X%) | TREND
ENTRY: $XXX → TARGET $YYY (X%) | STOP $ZZZ (X%)
REASON: 1 sentence"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                max_tokens=200,
                temperature=0.2  # Precise signals
            )
            
            await update.message.reply_text(
                f"🧠 <b>AI TRADING SIGNAL</b>\n\n"
                f"{response.choices[0].message.content}\n\n"
                f"⚙️ Usage: {ai_usage_today}/{daily_limit} (${ai_usage_today*0.0006:.3f})",
                parse_mode='HTML'
            )
            return
            
        except Exception as e:
            print(f"AI Error: {e}")
    
    # STEP 3: FALLBACK - Pure Live Data
    if live_data:
        response = "📊 <b>LIVE TECHNICALS</b>\n\n"
        for symbol, data in live_data.items():
            trend_emoji = "🟢" if data['trend'] == 'BULL' else "🔴"
            response += (
                f"{trend_emoji} <b>{symbol}</b>\n"
                f"${data['price']:.2f} {data['change_pct']:+.1f}%\n"
                f"RSI: {data['rsi']:.0f} | S: ${data['support']:.2f}\n\n"
            )
        await update.message.reply_text(response, parse_mode='HTML')
    else:
        await update.message.reply_text(
            f"💬 <b>AI TRADING BRAIN READY</b>\n\n"
            f"Ask: 'NVDA entry point?' 'TSLA support?'\n"
            f"⚙️ AI: {ai_usage_today}/{daily_limit}\n"
            f"{'🟢 LIVE' if client else '⚠️ ADD OPENAI_API_KEY'}"
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    progress = config["weekly_profit"] / config["weekly_goal"] * 100
    ai_status = "🟢 LIVE" if client else "⚠️ ADD OPENAI_API_KEY"
    
    await update.message.reply_text(
        f"🧠 <b>GEEWONI AI TRADING BRAIN v6.2</b>\n\n"
        f"💰 P&L: ${config['weekly_profit']:,}/{config['weekly_goal']:,} ({progress:.0f}%)\n"
        f"{ai_status} | Usage: {ai_usage_today}/{daily_limit}\n\n"
        f"<b>🚀 JUST CHAT:</b>\n"
        f"• 'NVDA entry point?'\n"
        f"• 'TSLA support level?'\n"
        f"• 'Market outlook?'\n"
        f"• 'SMCI vs PLTR?'\n\n"
        f"<b>📊 LIVE DATA:</b>\n"
        f"Pre-market + After-hours + Weekend\n"
        f"EMA/RSI/Support/Resistance calculated",
        parse_mode='HTML'
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    progress = config["weekly_profit"] / config["weekly_goal"] * 100
    await update.message.reply_text(
        f"📊 <b>EMPIRE DASHBOARD</b>\n"
        f"💰 ${int(config['weekly_profit']):,}/{config['weekly_goal']:,} ({progress:.0f}%)\n"
        f"🚨 Alerts: {config['alert_pct']:.1f}%\n"
        f"⭐ Priorities: {', '.join(config['priority'])}\n"
        f"🧠 AI Usage: {ai_usage_today}/{daily_limit}",
        parse_mode='HTML'
    )

async def win(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config['weekly_profit'] += 250
    save_config(config)
    await update.message.reply_text(f"✅ +$250 WIN!\n💰 ${config['weekly_profit']:,}/{config['weekly_goal']:,}")

async def loss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config['weekly_profit'] = max(0, config['weekly_profit'] - 100)
    save_config(config)
    await update.message.reply_text(f"❌ -$100 LOSS\n💰 ${config['weekly_profit']:,}/{config['weekly_goal']:,}")

def main():
    """GEEWONI AI v6.2 - YOUR VERSION"""
    print("🧠 GEEWONI AI TRADING BRAIN v6.2")
    
    # Check YOUR variable names
    if not TELEGRAM_TOKEN:
        print("❌ SET TELEGRAM_TOKEN!")
        return
    if not OPENAI_KEY:  # ← YOUR VARIABLE NAME
        print("⚠️ ADD OPENAI_KEY!")
        return
    
    print("✅ gpt-4o-mini LIVE")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("win", win))
    app.add_handler(CommandHandler("loss", loss))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_trading_brain))
    
    print("🚀 GEEWONI AI v6.2 LIVE!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
