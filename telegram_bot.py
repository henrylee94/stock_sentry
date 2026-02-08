import logging
import re
import pandas as pd
import numpy as np
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import yfinance as yf
import json
from pathlib import Path
import os
from openai import OpenAI
from datetime import datetime, timedelta
import asyncio
import pytz
import nest_asyncio
nest_asyncio.apply()  # 🔥 FIXES EVENT LOOP IN DOCKER

# 🆕 Import SkillsetManager
try:
    from skillset_manager import SkillsetManager
    SKILLS_ENABLED = True
except ImportError:
    print("⚠️ skillset_manager not found - Skills disabled")
    SKILLS_ENABLED = False


# 🆕 Import SkillsetManager
try:
    from skillset_manager import SkillsetManager
    SKILLS_ENABLED = True
except ImportError:
    print("⚠️ skillset_manager not found - Skills disabled")
    SKILLS_ENABLED = False


# READ .env FILE DIRECTLY
def load_env_file():
    """加载 .env 文件（仅本地开发时）"""
    env_file = Path('.env')
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()
        print("✅ .env loaded from file")
    else:
        print("ℹ️ No .env file (using system environment variables)")

load_env_file()

# 直接从环境变量读取（无论是 .env 还是系统变量）
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")

# 调试输出（移除实际的 key 值）
print(f"DEBUG - TELEGRAM_TOKEN: {'✅ Found' if TELEGRAM_TOKEN else '❌ Missing'}")
print(f"DEBUG - OPENAI_KEY: {'✅ Found' if OPENAI_KEY else '❌ Missing'}")
if OPENAI_KEY:
    print(f"DEBUG - OPENAI_KEY starts with: {OPENAI_KEY[:10]}...")

CONFIG_FILE = Path("geewoni_config.json")
TRADES_FILE = Path("trades_history.json")
STRATEGIES_FILE = Path("strategies.json")
AI_LEARNING_FILE = Path("ai_learning.json")

ai_usage_today = 0
daily_limit = 1000

# Initialize OpenAI client with error handling
client = None

print(f"\n🔍 OpenAI 初始化调试:")
print(f"OPENAI_KEY 存在: {bool(OPENAI_KEY)}")

if OPENAI_KEY:
    print(f"OPENAI_KEY 长度: {len(OPENAI_KEY)}")
    print(f"OPENAI_KEY 开头: {OPENAI_KEY[:10]}...")
    print(f"OPENAI_KEY 结尾: ...{OPENAI_KEY[-10:]}")
    
    try:
        # 清理 key（移除空格、引号、换行）
        api_key_clean = OPENAI_KEY.strip().strip('"').strip("'").strip()
        
        print(f"清理后长度: {len(api_key_clean)}")
        print(f"清理后开头: {api_key_clean[:10]}...")
        
        # 尝试初始化
        from openai import OpenAI
        client = OpenAI(api_key=api_key_clean)
        
        # 测试调用（验证 key 是否有效）
        print("🧪 测试 API key...")
        test_response = client.models.list()
        
        print(f"✅ OpenAI client initialized successfully")
        print(f"✅ API key 有效！")
        
    except Exception as e:
        print(f"❌ OpenAI initialization error: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        client = None
else:
    print("⚠️ OPENAI_KEY not found")

print(f"最终 client 状态: {'✅ 可用' if client else '❌ None'}\n")

# 🆕 Initialize SkillsetManager
skills_manager = None
if SKILLS_ENABLED:
    try:
        skills_manager = SkillsetManager("skills")
        print(skills_manager.get_skills_summary())
    except Exception as e:
        print(f"⚠️ Skills 加载失败: {e}")
        skills_manager = None


# 🆕 Initialize SkillsetManager
skills_manager = None
if SKILLS_ENABLED:
    try:
        skills_manager = SkillsetManager("skills")
        print(skills_manager.get_skills_summary())
    except Exception as e:
        print(f"⚠️ Skills 加载失败: {e}")
        skills_manager = None


print(f"🧠 GEEWONI AI 交易大脑 v7.1 - with Skills")
print(f"{'✅ gpt-4o-mini LIVE' if client else '⚠️ ADD OPENAI_KEY'}")

# Config functions
config = {}
def load_config():
    global config
    if CONFIG_FILE.exists():
        config = json.loads(CONFIG_FILE.read_text())
    else:
        config = {
            'weekly_profit': 0,
            'weekly_goal': 10000,
            'priority': ['NVDA', 'PLTR', 'RKLB', 'SOFI', 'OKLO', 'MP', 'BMNR'],
            'ai_usage': 0,
            'language': 'both',  # both, chinese, english
            'favorite_setups': []
        }
        save_config(config)

def save_config(config):
    CONFIG_FILE.write_text(json.dumps(config, indent=2))

# Trade tracking
def load_trades():
    if TRADES_FILE.exists():
        return json.loads(TRADES_FILE.read_text())
    return []

def save_trade(trade):
    trades = load_trades()
    trades.append(trade)
    TRADES_FILE.write_text(json.dumps(trades, indent=2))

def calculate_win_rate():
    trades = load_trades()
    if not trades:
        return 0, 0, 0
    
    closed_trades = [t for t in trades if t.get('status') == 'closed']
    if not closed_trades:
        return 0, 0, 0
    
    wins = len([t for t in closed_trades if t.get('profit', 0) > 0])
    total = len(closed_trades)
    win_rate = (wins / total * 100) if total > 0 else 0
    
    total_profit = sum([t.get('profit', 0) for t in closed_trades])
    
    return win_rate, wins, total

# Strategy tracking
def load_strategies():
    if STRATEGIES_FILE.exists():
        return json.loads(STRATEGIES_FILE.read_text())
    return {
        'EMA Crossover': {'wins': 0, 'losses': 0, 'profit': 0},
        'Volume Breakout': {'wins': 0, 'losses': 0, 'profit': 0},
        'Support/Resistance': {'wins': 0, 'losses': 0, 'profit': 0},
        'Reversal': {'wins': 0, 'losses': 0, 'profit': 0}
    }

def save_strategies(strategies):
    STRATEGIES_FILE.write_text(json.dumps(strategies, indent=2))

def update_strategy_performance(strategy_name, profit):
    strategies = load_strategies()
    if strategy_name not in strategies:
        strategies[strategy_name] = {'wins': 0, 'losses': 0, 'profit': 0}
    
    if profit > 0:
        strategies[strategy_name]['wins'] += 1
    else:
        strategies[strategy_name]['losses'] += 1
    
    strategies[strategy_name]['profit'] += profit
    save_strategies(strategies)

# AI Learning System
def load_ai_learning():
    """Load AI learning data - tracks recommendations and outcomes"""
    if AI_LEARNING_FILE.exists():
        return json.loads(AI_LEARNING_FILE.read_text())
    return {
        'recommendations': [],  # All AI recommendations
        'followed_trades': [],  # Trades user actually made after AI suggestion
        'learning_insights': {
            'best_rsi_range': {'min': 40, 'max': 60},
            'best_volume_ratio': 1.5,
            'best_ema_setup': 'bullish_crossover',
            'preferred_strategies': [],
            'success_patterns': []
        },
        'total_recommendations': 0,
        'recommendations_followed': 0,
        'follow_rate': 0
    }

def save_ai_learning(learning_data):
    AI_LEARNING_FILE.write_text(json.dumps(learning_data, indent=2))

def log_ai_recommendation(symbol, recommendation_data):
    """Log when AI makes a recommendation"""
    learning = load_ai_learning()
    
    rec = {
        'id': datetime.now().strftime('%Y%m%d%H%M%S'),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'symbol': symbol,
        'entry_price': recommendation_data.get('entry_price'),
        'target_price': recommendation_data.get('target_price'),
        'stop_loss': recommendation_data.get('stop_loss'),
        'strategy': recommendation_data.get('strategy'),
        'rsi': recommendation_data.get('rsi'),
        'volume_ratio': recommendation_data.get('volume_ratio'),
        'ema_setup': recommendation_data.get('ema_setup'),
        'followed': False,
        'outcome': None  # Will be filled when trade closes
    }
    
    learning['recommendations'].append(rec)
    learning['total_recommendations'] += 1
    save_ai_learning(learning)
    
    print(f"📝 AI 推荐已记录: {symbol} @ ${recommendation_data.get('entry_price')}")
    
    return rec['id']

def mark_recommendation_followed(symbol, entry_price, recommendation_id=None):
    """Mark that user followed an AI recommendation"""
    learning = load_ai_learning()
    
    # Find matching recommendation (by symbol and similar entry price)
    for rec in reversed(learning['recommendations']):
        if rec['symbol'] == symbol and not rec['followed']:
            # Check if entry price is within 2% of recommendation
            if abs(entry_price - rec['entry_price']) / rec['entry_price'] < 0.02:
                rec['followed'] = True
                learning['recommendations_followed'] += 1
                learning['follow_rate'] = (learning['recommendations_followed'] / learning['total_recommendations'] * 100)
                
                learning['followed_trades'].append({
                    'recommendation_id': rec['id'],
                    'symbol': symbol,
                    'entry_price': entry_price,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                
                save_ai_learning(learning)
                print(f"✅ 用户跟随了 AI 推荐: {symbol}")
                return True
    
    return False

def update_recommendation_outcome(symbol, exit_price, profit):
    """Update outcome when trade closes"""
    learning = load_ai_learning()
    
    # Find the followed recommendation
    for rec in reversed(learning['recommendations']):
        if rec['symbol'] == symbol and rec['followed'] and rec['outcome'] is None:
            rec['outcome'] = {
                'exit_price': exit_price,
                'profit': profit,
                'success': profit > 0,
                'close_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Learn from this trade
            if profit > 0:
                # This was a successful pattern - remember it
                pattern = {
                    'rsi': rec['rsi'],
                    'volume_ratio': rec['volume_ratio'],
                    'ema_setup': rec['ema_setup'],
                    'strategy': rec['strategy']
                }
                learning['learning_insights']['success_patterns'].append(pattern)
                
                # Update best parameters based on successful trades
                update_learning_insights(learning, rec)
            
            save_ai_learning(learning)
            print(f"📊 AI 学习更新: {symbol} 结果已记录 (盈亏: ${profit:+.2f})")
            return True
    
    return False

def update_learning_insights(learning, successful_rec):
    """Update AI's learning insights based on successful trades"""
    insights = learning['learning_insights']
    
    # Adjust RSI range based on successful trades
    if successful_rec['rsi']:
        rsi = successful_rec['rsi']
        # Narrow down to successful RSI range
        if rsi > insights['best_rsi_range']['min'] and rsi < insights['best_rsi_range']['max']:
            pass  # Already in range
        else:
            # Expand range slightly to include this success
            if rsi < insights['best_rsi_range']['min']:
                insights['best_rsi_range']['min'] = max(30, rsi - 5)
            if rsi > insights['best_rsi_range']['max']:
                insights['best_rsi_range']['max'] = min(70, rsi + 5)
    
    # Track best strategies
    if successful_rec['strategy'] not in insights['preferred_strategies']:
        insights['preferred_strategies'].append(successful_rec['strategy'])

def get_ai_insights_summary():
    """Get summary of what AI has learned"""
    learning = load_ai_learning()
    insights = learning['learning_insights']
    
    successful_trades = [r for r in learning['recommendations'] if r.get('outcome') and r['outcome']['success']]
    total_followed = len([r for r in learning['recommendations'] if r['followed']])
    
    if not successful_trades:
        return "AI 还在学习中... 需要更多交易数据"
    
    success_rate = (len(successful_trades) / total_followed * 100) if total_followed > 0 else 0
    
    summary = f"""📚 <b>AI 学习总结</b>

📊 <b>推荐统计:</b>
- 总推荐: {learning['total_recommendations']}
- 跟随率: {learning['follow_rate']:.1f}%
- 成功率: {success_rate:.1f}% ({len(successful_trades)}/{total_followed})

🎯 <b>AI 学到的最佳设置:</b>
- RSI 范围: {insights['best_rsi_range']['min']:.0f} - {insights['best_rsi_range']['max']:.0f}
- 成交量倍数: >{insights['best_volume_ratio']:.1f}x
- 最佳策略: {', '.join(insights['preferred_strategies'][:3]) if insights['preferred_strategies'] else '学习中'}

💡 <b>成功模式数量:</b> {len(insights['success_patterns'])}
"""
    
    return summary

def get_extended_stock_data(symbol):
    """Get comprehensive stock data including pre-market, historical for EMA/support analysis"""
    try:
        import warnings
        warnings.filterwarnings('ignore')
        
        print(f"📡 Fetching {symbol}...")
        ticker = yf.Ticker(symbol)
        
        # Get 30 days for EMA
        hist_data = ticker.history(period="1mo", interval="1d")
        
        # Get today's intraday
        today_data = ticker.history(period="1d", interval="5m")
        
        if hist_data.empty:
            print(f"❌ {symbol}: Yahoo Finance 无数据")
            return None
        
        current_price = hist_data['Close'].iloc[-1]
        
        # Calculate EMAs
        ema_9 = hist_data['Close'].ewm(span=9, adjust=False).mean().iloc[-1]
        ema_21 = hist_data['Close'].ewm(span=21, adjust=False).mean().iloc[-1]
        ema_50 = hist_data['Close'].ewm(span=21, adjust=False).mean().iloc[-1] if len(hist_data) >= 21 else None
        
        # RSI calculation
        delta = hist_data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1] if not rs.empty else 50
        
        # Support/Resistance
        recent_high = hist_data['High'].tail(20).max()
        recent_low = hist_data['Low'].tail(20).min()
        week_high = hist_data['High'].tail(5).max()
        week_low = hist_data['Low'].tail(5).min()
        day_high = today_data['High'].max() if not today_data.empty else recent_high
        day_low = today_data['Low'].min() if not today_data.empty else recent_low
        
        # Volume
        avg_volume = hist_data['Volume'].tail(20).mean()
        current_volume = hist_data['Volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        # Trend determination
        if current_price > ema_9 > ema_21:
            trend = "强势看涨"
        elif current_price < ema_9 < ema_21:
            trend = "强势看跌"
        elif current_price > ema_9:
            trend = "弱势看涨"
        else:
            trend = "弱势看跌"
        
        last_update = hist_data.index[-1].strftime('%Y-%m-%d %H:%M')
        
        result = {
            'symbol': symbol,
            'current_price': float(current_price),
            'ema_9': float(ema_9),
            'ema_21': float(ema_21),
            'ema_50': float(ema_50) if ema_50 else None,
            'rsi': float(rsi),
            'resistance': float(recent_high),
            'support': float(recent_low),
            'week_high': float(week_high),
            'week_low': float(week_low),
            'day_high': float(day_high),
            'day_low': float(day_low),
            'avg_volume': int(avg_volume),
            'current_volume': int(current_volume),
            'volume_ratio': float(volume_ratio),
            'trend': trend,
            'trend_en': 'bullish' if current_price > ema_9 else 'bearish',
            'trend_en': 'bullish' if current_price > ema_9 else 'bearish',
            'price_change_pct': float(((current_price - hist_data['Close'].iloc[-2]) / hist_data['Close'].iloc[-2]) * 100),
            'last_update': last_update,
            'data_source': 'Yahoo Finance'
        }
        
        print(f"✅ {symbol}: ${current_price:.2f} | 趋势: {trend} | RSI: {rsi:.0f}")
        return result
        
    except Exception as e:
        print(f"❌ {symbol} Error: {e}")
        return None

load_config()

# AI Brain - handles everything
async def ai_brain(update: Update, context):
    global ai_usage_today
    
    if not update.message or not update.message.text:
        return
    
   if not client:
        # 更详细的错误信息
        await update.message.reply_text(
            f"⚠️ AI 暂时不可用\n"
            f"调试信息:\n"
            f"OPENAI_KEY: {'找到' if OPENAI_KEY else '未找到'}\n"
            f"Client: {'初始化失败' if OPENAI_KEY and not client else '未初始化'}"
        )
        return
    
    if ai_usage_today >= daily_limit:
        await update.message.reply_text(f"⚠️ 今日额度已用完 ({daily_limit} 次)")
        return
    
    user_query = update.message.text.strip()
    
    # Extract stock symbols
    try:
        symbols = re.findall(r'\b[A-Z]{2,5}\b', user_query)
        stock_symbols = re.findall(r'\$\s*?([A-Z]{2,5})\b|\b([A-Z]{2,5})\b', user_query)
        stock_symbols = [s[0] or s[1] for s in stock_symbols if s[0] or s[1]]
        stock_symbols = list(set(stock_symbols))[:3]  # Dedupe + limit
    except:
        stock_symbols = []  # Safe fallback

    # Fetch stock data if symbols detected (optional)
    stock_data_context = ""
    data_sources = []
    has_realtime_data = False
    
    if stock_symbols:
        print(f"🔍 检测到股票代码: {stock_symbols}")
        stock_data = {}
        
        for symbol in list(set(stock_symbols))[:3]:
            data = get_extended_stock_data(symbol)
            if data:
                stock_data[symbol] = data
                data_sources.append(f"✅ {symbol}: Yahoo Finance ({data['last_update']})")
                has_realtime_data = True
            else:
                data_sources.append(f"⚠️ {symbol}: 无实时数据")
        
        if stock_data:
            stock_data_context = "\n\n📊 实时市场数据 (Yahoo Finance):\n"
            for sym, data in stock_data.items():
                stock_data_context += f"""
{sym} (更新: {data['last_update']}):
- 当前价格: ${data['current_price']:.2f} ({data['price_change_pct']:+.2f}%)
- 趋势: {data['trend']}
- RSI: {data['rsi']:.0f}
- EMA9: ${data['ema_9']:.2f} | EMA21: ${data['ema_21']:.2f}
- 今日高/低: ${data['day_high']:.2f} / ${data['day_low']:.2f}
- 本周高/低: ${data['week_high']:.2f} / ${data['week_low']:.2f}
- 支撑位: ${data['support']:.2f} | 阻力位: ${data['resistance']:.2f}
- 成交量比率: {data['volume_ratio']:.2f}x
"""
            
            # 🆕 添加技能推荐
            if skills_manager:
                recommended_skills = []
                for sym, data in stock_data.items():
                    market_condition = {
                        'trend': data.get('trend_en', 'neutral'),
                        'rsi': data.get('rsi', 50),
                        'volume_ratio': data.get('volume_ratio', 1.0),
                        'volatility': 'normal'
                    }
                    skills = skills_manager.match_skill_to_market(market_condition)
                    recommended_skills.extend(skills)
                
                # 去重
                recommended_skills = list(set(recommended_skills))[:3]
                if recommended_skills:
                    stock_data_context += "\n\n📚 推荐策略:\n"
                    for skill_name in recommended_skills:
                        skill = skills_manager.get_skill(skill_name)
                        if skill:
                            stock_data_context += f"• {skill['name']} ({skill['difficulty']}): {skill['description']}\n"
            
            # 🆕 添加技能推荐
            if skills_manager:
                recommended_skills = []
                for sym, data in stock_data.items():
                    market_condition = {
                        'trend': data.get('trend_en', 'neutral'),
                        'rsi': data.get('rsi', 50),
                        'volume_ratio': data.get('volume_ratio', 1.0),
                        'volatility': 'normal'
                    }
                    skills = skills_manager.match_skill_to_market(market_condition)
                    recommended_skills.extend(skills)
                
                # 去重
                recommended_skills = list(set(recommended_skills))[:3]
                if recommended_skills:
                    try:
                        stock_data_context += "\n\n📚 推荐策略:\n"
                        for skill_name in recommended_skills:
                            skill = skills_manager.get_skill(skill_name)
                            if skill:
                                stock_data_context += f"• {skill['name']} ({skill['difficulty']}): {skill['description']}\n"
                    except Exception as e:
                        print(f"Skills error: {e}")
                        stock_data_context += "\n\n📚 推荐策略: 加载中...\n"
        else:
            # No real-time data available - AI uses knowledge
            stock_data_context += f"""
            {sym} (更新: {data['last_update']}):
            - 当前价格: ${data['current_price']:.2f} ({data['price_change_pct']:+.2f}%)
            - 趋势: {data['trend']}
            - RSI: {data['rsi']:.0f}
            - EMA9: ${data['ema_9']:.2f} | EMA21: ${data['ema_21']:.2f}
            - 今日高/低: ${data['day_high']:.2f} / ${data['day_low']:.2f}
            - 本周高/低: ${data['week_high']:.2f} / ${data['week_low']:.2f}
            - 支撑位: ${data['support']:.2f} | 阻力位: ${data['resistance']:.2f}
            - 成交量比率: {data['volume_ratio']:.2f}x            """
                
    # Call AI
    try:
        ai_usage_today += 1
        config['ai_usage'] = ai_usage_today
        save_config(config)
        
        print(f"🤖 调用 OpenAI API (使用次数: {ai_usage_today}/{daily_limit})...")
        
        # Get best performing strategies
        strategies = load_strategies()
        best_strategy = max(strategies.items(), key=lambda x: x[1]['profit']) if strategies else None
        
        # Get AI learning insights
        learning = load_ai_learning()
        insights = learning['learning_insights']
        
        # Build learning context
        learning_context = ""
        if learning['total_recommendations'] > 0:
            success_rate = (learning['recommendations_followed'] / learning['total_recommendations'] * 100) if learning['total_recommendations'] > 0 else 0
            learning_context = f"""
AI 学习数据:
- 推荐成功率: {success_rate:.1f}%
- 最佳 RSI 范围: {insights['best_rsi_range']['min']:.0f}-{insights['best_rsi_range']['max']:.0f}
- 最佳成交量倍数: >{insights['best_volume_ratio']:.1f}x
- 用户偏好策略: {', '.join(insights['preferred_strategies'][:3]) if insights['preferred_strategies'] else '无'}
"""
        
        system_prompt = f"""你是 GEEWONI AI - 专业日内交易分析师和市场专家，能够从历史交易中学习和改进。

账户状态:
- 本周盈亏: ${config['weekly_profit']}/{config['weekly_goal']}
- 重点股票: {', '.join(config['priority'])}
- 最佳策略: {best_strategy[0] if best_strategy else 'N/A'} (盈利: ${best_strategy[1]['profit']:.2f})

{learning_context}

{stock_data_context if stock_data_context else "无股票数据 - 作为通用AI助手回答"}

分析方法:
- 如果有实时数据: 使用技术指标 (EMA, RSI, 成交量) 精确分析
- 如果无实时数据: 基于最新市场新闻、趋势、基本面分析

当分析股票时:
1. EMA 趋势判断 (如果有数据)
   - 价格 > EMA9 > EMA21 = 强势看涨
   - 价格 < EMA9 < EMA21 = 强势看跌
2. RSI 最佳范围: {insights['best_rsi_range']['min']:.0f}-{insights['best_rsi_range']['max']:.0f} (根据历史成功交易)
3. 成交量确认: >{insights['best_volume_ratio']:.1f}x
4. 如果无实时数据，分析:
   - 最新新闻和市场事件
   - 行业趋势和竞争态势
   - 公司基本面
   - 技术面支撑阻力位 (基于近期走势知识)
5. 优先推荐用户成功率高的策略: {', '.join(insights['preferred_strategies'][:2]) if insights['preferred_strategies'] else '所有策略'}
6. 提供具体的:
   - 入场价格建议
   - 目标价格
   - 止损价格
   - 推荐策略名称
   - 理由说明

回复格式 (简短直接):
📊 [股票代码] 分析
💰 当前: $XXX (或 "基于市场知识")
📈 入场: $XXX (原因)
🎯 目标: $XXX 
🛑 止损: $XXX
📋 策略: [策略名称]
💡 理由: [简短说明，包括新闻/事件如果相关]

用中文回复，简短专业。无论是否有实时数据，都要给出有价值的分析。"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            max_tokens=600,
            temperature=0.3
        )
        
        response_text = response.choices[0].message.content
        
        # Extract AI recommendations from response (if stock analysis)
        if stock_data_context:
            # Try to extract recommendation details
            for symbol in stock_data.keys():
                try:
                    # Extract prices from AI response (simple pattern matching)
                    import re
                    entry_match = re.search(r'入场[：:]\s*\$?([\d.]+)', response_text)
                    target_match = re.search(r'目标[：:]\s*\$?([\d.]+)', response_text)
                    stop_match = re.search(r'止损[：:]\s*\$?([\d.]+)', response_text)
                    strategy_match = re.search(r'策略[：:]\s*([^\n]+)', response_text)
                    
                    if entry_match:
                        rec_data = {
                            'entry_price': float(entry_match.group(1)),
                            'target_price': float(target_match.group(1)) if target_match else None,
                            'stop_loss': float(stop_match.group(1)) if stop_match else None,
                            'strategy': strategy_match.group(1).strip() if strategy_match else 'AI推荐',
                            'rsi': stock_data[symbol]['rsi'],
                            'volume_ratio': stock_data[symbol]['volume_ratio'],
                            'ema_setup': 'bullish' if stock_data[symbol]['current_price'] > stock_data[symbol]['ema_9'] else 'bearish'
                        }
                        
                        # Log this recommendation
                        log_ai_recommendation(symbol, rec_data)
                except Exception as e:
                    print(f"⚠️ 无法提取推荐数据: {e}")
        
        # Build response
        if stock_data_context:
            if has_realtime_data:
                data_source_text = "\n".join(data_sources)
                prefix = f"🧠 <b>AI 交易分析</b>\n\n<b>📡 数据来源:</b>\n{data_source_text}\n\n"
            else:
                prefix = f"🧠 <b>AI 交易分析</b>\n\n<b>📰 数据来源: AI 市场知识 + 新闻分析</b>\n⚠️ 实时数据不可用\n\n"
            
            # Add quick action buttons for stock analysis
            keyboard = []
            for symbol in stock_symbols[:3]:  # Use requested symbols, not just those with data
                keyboard.append([
                    InlineKeyboardButton(f"买入 {symbol}", callback_data=f"buy_{symbol}"),
                    InlineKeyboardButton(f"观察 {symbol}", callback_data=f"watch_{symbol}")
                ])
            reply_markup = InlineKeyboardMarkup(keyboard)
        else:
            prefix = "🤖 <b>GEEWONI AI</b>\n\n"
            reply_markup = None
        
        await update.message.reply_text(
            f"{prefix}{response_text}\n\n"
            f"⚙️ AI 使用: {ai_usage_today}/{daily_limit}",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        
        print(f"✅ 回复已发送。今日总调用: {ai_usage_today}")
        
    except Exception as e:
        print(f"❌ OpenAI API 错误: {e}")
        await update.message.reply_text(f"❌ AI 错误: {str(e)}")

# Button callback handler
async def button_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    action, symbol = query.data.split('_')
    
    if action == 'buy':
        await query.message.reply_text(
            f"💰 <b>买入 {symbol}</b>\n\n请输入:\n格式: buy {symbol} 价格 数量 策略\n\n例子: buy {symbol} 145.50 10 EMA Crossover",
            parse_mode='HTML'
        )
    elif action == 'watch':
        if symbol not in config['priority']:
            config['priority'].append(symbol)
            save_config(config)
        await query.message.reply_text(f"👀 已添加 {symbol} 到观察列表")
    elif action == 'sell':
        await query.message.reply_text(
            f"💵 <b>卖出 {symbol}</b>\n\n请输入:\n格式: sell {symbol} 价格\n\n例子: sell {symbol} 150.25",
            parse_mode='HTML'
        )

# Process buy/sell commands
async def process_trade(update: Update, context):
    text = update.message.text.strip().lower()
    
    # Buy format: buy SYMBOL price quantity strategy
    if text.startswith('buy '):
        parts = text.split()
        if len(parts) < 4:
            await update.message.reply_text("❌ 格式: buy SYMBOL 价格 数量 策略\n例: buy NVDA 145.50 10 EMA Crossover")
            return
        
        symbol = parts[1].upper()
        try:
            price = float(parts[2])
            quantity = int(parts[3])
            strategy = ' '.join(parts[4:]) if len(parts) > 4 else 'Manual'
            
            trade = {
                'id': datetime.now().strftime('%Y%m%d%H%M%S'),
                'type': 'buy',
                'symbol': symbol,
                'entry_price': price,
                'quantity': quantity,
                'strategy': strategy,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'open'
            }
            
            save_trade(trade)
            
            # Check if this follows an AI recommendation
            followed = mark_recommendation_followed(symbol, price)
            
            keyboard = [[
                InlineKeyboardButton(f"卖出 {symbol}", callback_data=f"sell_{symbol}")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            follow_msg = "\n🤖 <b>跟随 AI 推荐</b>" if followed else ""
            
            await update.message.reply_text(
                f"✅ <b>买入成功</b>{follow_msg}\n\n"
                f"股票: {symbol}\n"
                f"价格: ${price:.2f}\n"
                f"数量: {quantity}\n"
                f"策略: {strategy}\n"
                f"总额: ${price * quantity:.2f}",
                parse_mode='HTML',
                reply_markup=reply_markup
            )
        except ValueError:
            await update.message.reply_text("❌ 价格和数量必须是数字")
    
    # Sell format: sell SYMBOL price
    elif text.startswith('sell '):
        parts = text.split()
        if len(parts) < 3:
            await update.message.reply_text("❌ 格式: sell SYMBOL 价格\n例: sell NVDA 150.25")
            return
        
        symbol = parts[1].upper()
        try:
            sell_price = float(parts[2])
            
            # Find open trade
            trades = load_trades()
            open_trade = None
            for trade in reversed(trades):
                if trade['symbol'] == symbol and trade['status'] == 'open':
                    open_trade = trade
                    break
            
            if not open_trade:
                await update.message.reply_text(f"❌ 没有找到 {symbol} 的开仓交易")
                return
            
            # Calculate profit
            profit = (sell_price - open_trade['entry_price']) * open_trade['quantity']
            profit_pct = ((sell_price - open_trade['entry_price']) / open_trade['entry_price']) * 100
            
            # Update trade
            open_trade['exit_price'] = sell_price
            open_trade['profit'] = profit
            open_trade['profit_pct'] = profit_pct
            open_trade['status'] = 'closed'
            open_trade['exit_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Save
            TRADES_FILE.write_text(json.dumps(trades, indent=2))
            
            # Update strategy performance
            update_strategy_performance(open_trade['strategy'], profit)
            
            # Update AI learning if this was a followed recommendation
            update_recommendation_outcome(symbol, sell_price, profit)
            
            # Update config profit
            config['weekly_profit'] += profit
            save_config(config)
            
            # Calculate win rate
            win_rate, wins, total = calculate_win_rate()
            
            emoji = "✅" if profit > 0 else "❌"
            
            await update.message.reply_text(
                f"{emoji} <b>平仓成功</b>\n\n"
                f"股票: {symbol}\n"
                f"入场: ${open_trade['entry_price']:.2f}\n"
                f"出场: ${sell_price:.2f}\n"
                f"盈亏: ${profit:+.2f} ({profit_pct:+.2f}%)\n"
                f"策略: {open_trade['strategy']}\n\n"
                f"📊 <b>总体表现</b>\n"
                f"胜率: {win_rate:.1f}% ({wins}/{total})\n"
                f"本周盈亏: ${config['weekly_profit']:,.2f}",
                parse_mode='HTML'
            )
        except ValueError:
            await update.message.reply_text("❌ 价格必须是数字")

async def start(update: Update, context):
    win_rate, wins, total = calculate_win_rate()
    progress = config["weekly_profit"] / config["weekly_goal"] * 100
    ai_status = "🟢 在线" if client else "⚠️ 添加 OPENAI_KEY"
    
    await update.message.reply_text(
        f"🧠 <b>GEEWONI AI 交易大脑 v7.1 - with Skills</b>\n\n"
        f"💰 本周: ${config['weekly_profit']:,.2f}/{config['weekly_goal']:,} ({progress:.0f}%)\n"
        f"📊 胜率: {win_rate:.1f}% ({wins}/{total})\n"
        f"{ai_status} | 使用: {ai_usage_today}/{daily_limit}\n\n"
        f"<b>📈 股票分析:</b> 'NVDA 入场点?'\n"
        f"<b>📋 交易:</b> buy NVDA 145.50 10 EMA策略\n"
        f"<b>💬 通用:</b> 任何问题都可以问!\n"
        f"<b>🧠 AI 学习:</b> 从你的交易中学习优化!\n\n"
        f"<b>命令:</b>\n"
        f"/stats - 交易统计\n"
        f"/morning - 早盘摘要\n"
        f"/skills - 查看策略库 🆕\n"  # 新增
        f"/skill [名称] - 策略详情 🆕\n"  # 新增
        f"/skills - 查看策略库 🆕\n"  # 新增
        f"/skill [名称] - 策略详情 🆕\n"  # 新增
        f"/learn - AI 学习报告 🆕\n"
        f"/usage - AI 使用量\n"
        f"/strategies - 策略表现\n"
        f"/positions - 持仓查看",
        parse_mode='HTML'
    )

async def stats(update: Update, context):
    win_rate, wins, total = calculate_win_rate()
    progress = config["weekly_profit"] / config["weekly_goal"] * 100
    
    await update.message.reply_text(
        f"📊 <b>交易统计</b>\n\n"
        f"💰 本周盈亏: ${int(config['weekly_profit']):,}/{config['weekly_goal']:,} ({progress:.0f}%)\n"
        f"📈 胜率: {win_rate:.1f}%\n"
        f"✅ 盈利: {wins}\n"
        f"❌ 亏损: {total - wins}\n"
        f"📝 总交易: {total}\n"
        f"⭐ 观察: {', '.join(config['priority'][:5])}",
        parse_mode='HTML'
    )

async def usage_command(update: Update, context):
    percentage = (ai_usage_today / daily_limit) * 100
    remaining = daily_limit - ai_usage_today
    
    await update.message.reply_text(
        f"🤖 <b>AI 使用量</b>\n\n"
        f"📊 已用: {ai_usage_today}/{daily_limit} ({percentage:.1f}%)\n"
        f"✅ 剩余: {remaining}\n"
        f"🔄 重置: 每日\n\n"
        f"💡 每次对话 = 1 次调用",
        parse_mode='HTML'
    )

async def strategies_command(update: Update, context):
    strategies = load_strategies()
    
    response = "📋 <b>策略表现</b>\n\n"
    
    # Sort by profit
    sorted_strategies = sorted(strategies.items(), key=lambda x: x[1]['profit'], reverse=True)
    
    for name, data in sorted_strategies:
        total = data['wins'] + data['losses']
        win_rate = (data['wins'] / total * 100) if total > 0 else 0
        response += f"<b>{name}</b>\n"
        response += f"胜率: {win_rate:.1f}% ({data['wins']}/{total})\n"
        response += f"盈亏: ${data['profit']:+.2f}\n\n"
    
    await update.message.reply_text(response, parse_mode='HTML')

async def learn_command(update: Update, context):
    """Show what AI has learned"""
    summary = get_ai_insights_summary()
    await update.message.reply_text(summary, parse_mode='HTML')



async def skills_command(update: Update, context):
    """显示所有可用策略"""
    if not skills_manager:
        await update.message.reply_text("⚠️ Skills 系统未加载")
        return
    
    summary = skills_manager.get_skills_summary()
    beginner_skills = skills_manager.get_recommended_skills_for_beginner()
    
    response = f"{summary}\n\n🎓 <b>初学者推荐:</b>\n"
    for skill_name in beginner_skills:
        response += f"• {skill_name}\n"
    
    response += "\n💡 使用 /skill [名称] 查看详情"
    await update.message.reply_text(response, parse_mode='HTML')

async def skill_detail_command(update: Update, context):
    """显示特定策略详情"""
    if not skills_manager:
        await update.message.reply_text("⚠️ Skills 系统未加载")
        return
    
    if not context.args:
        await update.message.reply_text(
            "使用方法: /skill [策略名称]\n\n"
            "例如: /skill EMA Crossover\n\n"
            "查看所有策略: /skills"
        )
        return
    
    skill_name = ' '.join(context.args)
    skill = skills_manager.get_skill(skill_name)
    
    if not skill:
        await update.message.reply_text(f"❌ 找不到策略: {skill_name}\n\n查看所有策略: /skills")
        return
    
    entry_conditions = skill['rules'].get('entry_conditions', [])
    if isinstance(entry_conditions, list):
        entry_text = '\n'.join([f"  • {c}" for c in entry_conditions[:3]])
    else:
        entry_text = "  见策略详情"
    
    response = f"""📖 <b>{skill['name']}</b>

<b>类型:</b> {skill['type']}
<b>难度:</b> {skill['difficulty']}
<b>描述:</b> {skill['description']}

<b>📈 入场条件:</b>
{entry_text}

<b>🛑 止损:</b> {skill['rules'].get('stop_loss', 'N/A')}
<b>💰 仓位:</b> {skill['rules'].get('position_size', 'N/A')}

<b>📊 表现:</b>
胜率: {skill['performance']['win_rate']:.1f}%
交易: {skill['performance']['total_trades']}
盈亏: ${skill['performance']['total_pnl']:.2f}

<b>💡 注意:</b> {skill.get('notes', 'N/A')}
"""
    await update.message.reply_text(response, parse_mode='HTML')

async def skills_command(update: Update, context):
    """显示所有可用策略"""
    if not skills_manager:
        await update.message.reply_text("⚠️ Skills 系统未加载")
        return
    
    summary = skills_manager.get_skills_summary()
    beginner_skills = skills_manager.get_recommended_skills_for_beginner()
    
    response = f"{summary}\n\n🎓 <b>初学者推荐:</b>\n"
    for skill_name in beginner_skills:
        response += f"• {skill_name}\n"
    
    response += "\n💡 使用 /skill [名称] 查看详情"
    await update.message.reply_text(response, parse_mode='HTML')

async def skill_detail_command(update: Update, context):
    """显示特定策略详情"""
    if not skills_manager:
        await update.message.reply_text("⚠️ Skills 系统未加载")
        return
    
    if not context.args:
        await update.message.reply_text(
            "使用方法: /skill [策略名称]\n\n"
            "例如: /skill EMA Crossover\n\n"
            "查看所有策略: /skills"
        )
        return
    
    skill_name = ' '.join(context.args)
    skill = skills_manager.get_skill(skill_name)
    
    if not skill:
        await update.message.reply_text(f"❌ 找不到策略: {skill_name}\n\n查看所有策略: /skills")
        return
    
    entry_conditions = skill['rules'].get('entry_conditions', [])
    if isinstance(entry_conditions, list):
        entry_text = '\n'.join([f"  • {c}" for c in entry_conditions[:3]])
    else:
        entry_text = "  见策略详情"
    
    response = f"""📖 <b>{skill['name']}</b>

<b>类型:</b> {skill['type']}
<b>难度:</b> {skill['difficulty']}
<b>描述:</b> {skill['description']}

<b>📈 入场条件:</b>
{entry_text}

<b>🛑 止损:</b> {skill['rules'].get('stop_loss', 'N/A')}
<b>💰 仓位:</b> {skill['rules'].get('position_size', 'N/A')}

<b>📊 表现:</b>
胜率: {skill['performance']['win_rate']:.1f}%
交易: {skill['performance']['total_trades']}
盈亏: ${skill['performance']['total_pnl']:.2f}

<b>💡 注意:</b> {skill.get('notes', 'N/A')}
"""
    await update.message.reply_text(response, parse_mode='HTML')

async def positions_command(update: Update, context):
    trades = load_trades()
    open_trades = [t for t in trades if t['status'] == 'open']
    
    if not open_trades:
        await update.message.reply_text("📭 当前无持仓")
        return
    
    response = "📋 <b>当前持仓</b>\n\n"
    
    for trade in open_trades:
        # Get current price
        data = get_extended_stock_data(trade['symbol'])
        if data:
            current_price = data['current_price']
            unrealized = (current_price - trade['entry_price']) * trade['quantity']
            unrealized_pct = ((current_price - trade['entry_price']) / trade['entry_price']) * 100
            
            emoji = "🟢" if unrealized > 0 else "🔴"
            
            response += f"{emoji} <b>{trade['symbol']}</b>\n"
            response += f"入场: ${trade['entry_price']:.2f}\n"
            response += f"当前: ${current_price:.2f}\n"
            response += f"盈亏: ${unrealized:+.2f} ({unrealized_pct:+.2f}%)\n"
            response += f"策略: {trade['strategy']}\n\n"
            
            # Add sell button
            keyboard = [[InlineKeyboardButton(f"卖出 {trade['symbol']}", callback_data=f"sell_{trade['symbol']}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(response, parse_mode='HTML', reply_markup=reply_markup if open_trades else None)

async def morning_summary(update: Update, context):
    """Generate morning market summary - AI first, real-time data optional"""
    if not client:
        await update.message.reply_text("⚠️ AI 不可用。请添加 OPENAI_KEY")
        return
    
    global ai_usage_today
    if ai_usage_today >= daily_limit:
        await update.message.reply_text(f"⚠️ 今日额度已用完 ({daily_limit} 次)")
        return
    
    await update.message.reply_text("⏳ 生成早盘摘要中...")
    
    # Try to get real-time data (optional)
    stock_data = {}
    failed_symbols = []
    
    for symbol in config['priority'][:7]:
        data = get_extended_stock_data(symbol)
        if data:
            stock_data[symbol] = data
        else:
            failed_symbols.append(symbol)
    
    # Build context based on what we have
    if stock_data:
        # We have real-time data
        data_context = "📊 实时市场数据 (Yahoo Finance):\n"
        for sym, data in stock_data.items():
            data_context += f"""
{sym}: ${data['current_price']:.2f} ({data['price_change_pct']:+.2f}%)
趋势: {data['trend']} | RSI: {data['rsi']:.0f}
成交量: {data['volume_ratio']:.1f}x
今日高/低: ${data['day_high']:.2f} / ${data['day_low']:.2f}
"""
        if failed_symbols:
            data_context += f"\n⚠️ 部分数据不可用: {', '.join(failed_symbols)}"
        
        data_source = f"✅ 使用 {len(stock_data)}/{len(config['priority'][:7])} 实时数据"
    else:
        # No real-time data, AI uses its knowledge
        data_context = f"""无实时数据可用 (市场可能休市或 API 不可用)

重点股票: {', '.join(config['priority'][:7])}

请基于你的知识、最新市场趋势和新闻，分析这些股票。"""
        data_source = "⚠️ 无实时数据，使用 AI 知识库和市场趋势"
    
    try:
        ai_usage_today += 1
        config['ai_usage'] = ai_usage_today
        save_config(config)
        
        system_prompt = f"""你是专业交易分析师和市场新闻专家。

{data_context}

你的任务:
1. 分析重点股票的交易机会
2. 如果有实时数据，用数据分析；如果没有，用最新市场动态和新闻
3. 考虑:
   - 最近的新闻和市场事件
   - 行业趋势
   - 技术面和基本面
   - 市场情绪

格式:
🌅 早盘摘要 ({datetime.now().strftime('%Y-%m-%d %A')})

🔥 今日重点 (3只):
1. [股票] - [为什么值得关注] - [建议: 买入/观察/等待]
2. [股票] - [为什么值得关注] - [建议]
3. [股票] - [为什么值得关注] - [建议]

📰 市场动态: [最新影响市场的新闻或事件]

💡 今日策略: [一句话交易建议]

简短专业，中文回复。即使没有实时数据，也要基于市场知识给出有价值的分析。"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "生成今日早盘摘要，包括市场新闻和交易机会"}
            ],
            max_tokens=600,
            temperature=0.4
        )
        
        summary = response.choices[0].message.content
        
        await update.message.reply_text(
            f"{summary}\n\n"
            f"📡 {data_source}\n"
            f"⚙️ AI 使用: {ai_usage_today}/{daily_limit}",
            parse_mode='HTML'
        )
        
    except Exception as e:
        print(f"❌ AI Error: {e}")
        await update.message.reply_text(f"❌ 生成摘要失败: {e}")
        
    except Exception as e:
        await update.message.reply_text(f"❌ 错误: {e}")

async def win(update: Update, context):
    config['weekly_profit'] += 250
    save_config(config)
    await update.message.reply_text(f"✅ +$250 盈利!\n💰 ${config['weekly_profit']:,}/{config['weekly_goal']:,}")

async def loss(update: Update, context):
    config['weekly_profit'] = max(0, config['weekly_profit'] - 100)
    save_config(config)
    await update.message.reply_text(f"❌ -$100 亏损\n💰 ${config['weekly_profit']:,}/{config['weekly_goal']:,}")


# 🔥 DEFINE route_message FIRST (outside main)
async def route_message(update: Update, context):
    """Route buy/sell to trade processor, else to AI"""
    if not update.message or not update.message.text:
        return
        
    text = update.message.text.strip().lower()
    if text.startswith('buy ') or text.startswith('sell '):
        await process_trade(update, context)
    else:
        await ai_brain(update, context)

async def main():
    print("🧠 GEEWONI AI v7.1 - Production Ready")
    
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN missing!")
        return
    
    print("🔄 Initializing...")
    
    # Single app instance
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Kill old bots/conflicts
    try:
        await application.bot.delete_webhook(drop_pending_updates=True)
        print("✅ Cleared old webhooks + pending updates")
    except:
        print("⚠️ No old webhooks found (OK)")
    
    # Clean handlers list - NO DUPLICATES
    handlers = [
        CommandHandler("start", start),
        CommandHandler("stats", stats),
        CommandHandler("usage", usage_command),
        CommandHandler("strategies", strategies_command),
        CommandHandler("learn", learn_command),
        CommandHandler("skills", skills_command),
        CommandHandler("skill", skill_detail_command),
        CommandHandler("positions", positions_command),
        CommandHandler("morning", morning_summary),
        CommandHandler("win", win),
        CommandHandler("loss", loss),
        CallbackQueryHandler(button_callback),
        MessageHandler(filters.TEXT & ~filters.COMMAND, route_message)
    ]
    
    # Add handlers
    for handler in handlers:
        application.add_handler(handler)
    
    print("🚀 GEEWONI LIVE - Handling messages...")
    
    # 🔥 ONE LINE - Perfect for Windows/Docker
    await application.run_polling(drop_pending_updates=True)


# 🔥 Run WITHOUT nest_asyncio
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")