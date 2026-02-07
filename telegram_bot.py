import logging
import re
import pandas as pd
import numpy as np
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters  # v13.15
import yfinance as yf
import json
from pathlib import Path
import os
from openai import OpenAI
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CONFIG_FILE = Path("geewoni_config.json")
OPENAI_KEY = os.getenv("OPENAI_KEY")
ai_usage_today = 0
daily_limit = 1000

client = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None
ENVIRONMENT = os.getenv('ENVIRONMENT', 'local')

print(f"🧠 GEEWONI AI TRADING BRAIN v6.2")
print(f"{'✅ gpt-4o-mini LIVE' if client else '⚠️ ADD OPENAI_KEY'}")

# ... [KEEP ALL your other functions EXACTLY THE SAME: load_config, save_config, get_live_data, compute_rsi] ...

# v13.15 COMPATIBLE HANDLERS (NO ContextTypes)
def ai_trading_brain(update, context):  # ← NO ContextTypes
    global ai_usage_today
    
    if not update.message or not update.message.text:
        update.message.reply_text("💬 Type: NVDA entry point?")
        return
        
    user_query = update.message.text.strip()
    symbols = re.findall(r'\b[A-Z]{2,5}\b', user_query)
    
    live_data = {}
    for symbol in set(symbols)[:3]:
        data = get_live_data(symbol)
        if data:
            live_data[symbol] = data
    
    if client and ai_usage_today < daily_limit:
        try:
            ai_usage_today += 1
            config['ai_usage'] = ai_usage_today
            save_config(config)
            
            data_context = []
            for symbol, data in live_data.items():
                data_context.append(
                    f"{symbol}: ${data['price']:.2f} {data['change_pct']:+.1f}% | "
                    f"Trend: {data['trend']} | RSI: {data['rsi']:.0f}"
                )
            
            system_prompt = f"""GEEWONI AI TRADING BRAIN - LIVE DATA
{chr(10).join(data_context) if data_context else 'No live data'}

P&L: ${config['weekly_profit']}/{config['weekly_goal']}
PRIORITIES: {', '.join(config['priority'])}

Entry: BUY above resistance + EMA bull + RSI 40-70
Exit: SELL at resistance or EMA bear
Risk: 2-5% stop loss

FORMAT: SYMBOL: $price | ENTRY: $XXX→$YYY | STOP: $ZZZ"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": system_prompt},
                         {"role": "user", "content": user_query}],
                max_tokens=200,
                temperature=0.2
            )
            
            update.message.reply_text(
                f"🧠 <b>AI TRADING SIGNAL</b>\n\n"
                f"{response.choices[0].message.content}\n\n"
                f"⚙️ Usage: {ai_usage_today}/{daily_limit}",
                parse_mode='HTML'
            )
            return
            
        except Exception as e:
            print(f"AI Error: {e}")
    
    if live_data:
        response = "📊 <b>LIVE TECHNICALS</b>\n\n"
        for symbol, data in live_data.items():
            trend_emoji = "🟢" if data['trend'] == 'BULL' else "🔴"
            response += f"{trend_emoji} <b>{symbol}</b>\n${data['price']:.2f} {data['change_pct']:+.1f}%\nRSI: {data['rsi']:.0f}\n\n"
        update.message.reply_text(response, parse_mode='HTML')
    else:
        update.message.reply_text("💬 Ask: 'NVDA entry point?'")

def start(update, context):  # ← NO ContextTypes
    progress = config["weekly_profit"] / config["weekly_goal"] * 100
    ai_status = "🟢 LIVE" if client else "⚠️ ADD OPENAI_KEY"
    
    update.message.reply_text(
        f"🧠 <b>GEEWONI AI TRADING BRAIN v6.2</b>\n\n"
        f"💰 P&L: ${config['weekly_profit']:,}/{config['weekly_goal']:,} ({progress:.0f}%)\n"
        f"{ai_status} | Usage: {ai_usage_today}/{daily_limit}\n\n"
        f"<b>🚀 CHAT:</b> 'NVDA entry point?' 'TSLA support?'",
        parse_mode='HTML'
    )

def stats(update, context):
    progress = config["weekly_profit"] / config["weekly_goal"] * 100
    update.message.reply_text(
        f"📊 <b>EMPIRE DASHBOARD</b>\n"
        f"💰 ${int(config['weekly_profit']):,}/{config['weekly_goal']:,} ({progress:.0f}%)\n"
        f"⭐ Priorities: {', '.join(config['priority'])}",
        parse_mode='HTML'
    )

def win(update, context):
    config['weekly_profit'] += 250
    save_config(config)
    update.message.reply_text(f"✅ +$250 WIN!\n💰 ${config['weekly_profit']:,}/{config['weekly_goal']:,}")

def loss(update, context):
    config['weekly_profit'] = max(0, config['weekly_profit'] - 100)
    save_config(config)
    update.message.reply_text(f"❌ -$100 LOSS\n💰 ${config['weekly_profit']:,}/{config['weekly_goal']:,}")

def main():
    print("🧠 GEEWONI AI TRADING BRAIN v6.2")
    
    if not TELEGRAM_TOKEN:
        print("❌ SET TELEGRAM_TOKEN!")
        return
    if not OPENAI_KEY:
        print("⚠️ ADD OPENAI_KEY!")
        return
    
    print("✅ gpt-4o-mini LIVE")
    
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)  # ← FIXED
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("stats", stats))
    dispatcher.add_handler(CommandHandler("win", win))
    dispatcher.add_handler(CommandHandler("loss", loss))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, ai_trading_brain))
    
    print("🚀 GEEWONI AI v6.2 LIVE!")
    updater.start_polling(clean=True)
    updater.idle()

if __name__ == "__main__":
    main()
