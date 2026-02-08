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

# Unset proxy env vars so OpenAI client does not get proxies= (avoids TypeError in some envs)
for _k in list(os.environ.keys()):
    if "proxy" in _k.lower():
        os.environ.pop(_k, None)

from openai import OpenAI
from datetime import datetime, timedelta
import asyncio
import pytz
import nest_asyncio
nest_asyncio.apply()  # 🔥 FIXES EVENT LOOP IN DOCKER

# Load .env first via python-dotenv (from script directory)
_script_dir = Path(__file__).resolve().parent
try:
    from dotenv import load_dotenv
    loaded = load_dotenv(_script_dir / ".env") or load_dotenv(Path(".env"))
    if loaded:
        print("✅ .env loaded (dotenv)")
except Exception:
    pass

# 🆕 Import SkillsetManager
try:
    from skillset_manager import SkillsetManager
    SKILLS_ENABLED = True
except ImportError:
    print("⚠️ skillset_manager not found - Skills disabled")
    SKILLS_ENABLED = False

# 🆕 Phase 1: Intent Detector + Rules Engine + Data Manager
try:
    from intent_detector import IntentDetector
    from rules_engine import RulesEngine
    from core.data_manager import get_extended_stock_data as data_manager_get_stock
    RULES_SYSTEM_ENABLED = True
except ImportError as e:
    print(f"⚠️ Rules/Data system not fully available: {e}")
    RULES_SYSTEM_ENABLED = False
    IntentDetector = None
    RulesEngine = None
    data_manager_get_stock = None

# 🆕 Phase 2: Strategy Orchestrator (multi-agent consensus)
try:
    from strategy_orchestrator import StrategyOrchestrator
    ORCHESTRATOR_ENABLED = True
except ImportError as e:
    print(f"⚠️ Strategy orchestrator not available: {e}")
    ORCHESTRATOR_ENABLED = False
    StrategyOrchestrator = None


# READ .env FILE DIRECTLY
def load_env_file():
    """Load .env: try script dir (where telegram_bot.py lives), then cwd, then parent."""
    script_dir = Path(__file__).resolve().parent
    for candidate in [script_dir / '.env', Path('.env'), script_dir.parent / '.env']:
        if candidate.exists():
            raw = candidate.read_text(encoding='utf-8', errors='ignore').lstrip('\ufeff')
            for line in raw.splitlines():
                line = line.strip().strip('\r')
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    key = key.strip().lstrip('\ufeff')
                    value = value.strip().strip('\r').strip('"').strip("'")
                    if key:
                        os.environ[key] = value
            print(f"✅ .env loaded from {candidate}")
            return
    print("ℹ️ No .env file (using system environment variables)")

load_env_file()

# 直接从环境变量读取（无论是 .env 还是系统变量）
# Prefer TELEGRAM_TOKEN_LOCAL when set (e.g. local dev) so prod (Zeabur) and local use different bots
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN_LOCAL") or os.getenv("TELEGRAM_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY") or os.getenv("OPENAI_API_KEY")

# Fallback: read OPENAI_KEY directly from .env next to this script (if still missing)
if not OPENAI_KEY and (_script_dir / ".env").exists():
    raw = (_script_dir / ".env").read_text(encoding="utf-8", errors="ignore").lstrip("\ufeff")
    for line in raw.splitlines():
        line = line.strip().strip("\r")
        if "=" not in line or line.startswith("#"):
            continue
        key, _, val = line.partition("=")
        key = key.strip().lstrip("\ufeff")
        if key in ("OPENAI_KEY", "OPENAI_API_KEY"):
            OPENAI_KEY = val.strip().strip('"').strip("'").strip("\r")
            if OPENAI_KEY:
                os.environ["OPENAI_KEY"] = OPENAI_KEY
                print("✅ OPENAI_KEY loaded from .env file (fallback)")
            break

# 调试输出（移除实际的 key 值）
_using_local = bool(os.getenv("TELEGRAM_TOKEN_LOCAL"))
print(f"DEBUG - TELEGRAM_TOKEN: {'✅ Found' if TELEGRAM_TOKEN else '❌ Missing'}")
if OPENAI_KEY:
    print(f"DEBUG - OPENAI_KEY: ✅ Found (len={len(OPENAI_KEY)}, starts with {OPENAI_KEY[:12]}...)")
else:
    print(f"DEBUG - OPENAI_KEY: ❌ Missing (no OPENAI_KEY or OPENAI_API_KEY in .env)")

from core import (
    CONFIG_FILE,
    TRADES_FILE,
    STRATEGIES_FILE,
    load_config,
    save_config,
    load_trades,
    save_trades,
    save_trade,
    load_strategies,
    save_strategies,
    calculate_win_rate,
    update_strategy_performance,
)
AI_LEARNING_FILE = Path("ai_learning.json")

ai_usage_today = 0
daily_limit = 1000

# Initialize OpenAI client with DETAILED error handling
client = None

print("\n" + "="*60)
print("🔍 OpenAI Client 初始化")
print("="*60)

if OPENAI_KEY:
    print(f"✅ OPENAI_KEY 已找到")
    print(f"   长度: {len(OPENAI_KEY)}")
    print(f"   开头: {OPENAI_KEY[:15]}...")
    
    try:
        # 清理 API key
        api_key_clean = OPENAI_KEY.strip().strip('"').strip("'").strip()
        print(f"   清理后长度: {len(api_key_clean)}")
        
        # 检查格式
        if not api_key_clean.startswith('sk-'):
            print(f"❌ 错误: API key 格式不正确（不是以 sk- 开头）")
            client = None
        else:
            print(f"✅ API key 格式正确")
            
            # 尝试初始化（确保无 proxy 传入）
            print(f"🔄 初始化 OpenAI client...")
            for _k in list(os.environ.keys()):
                if "proxy" in _k.lower():
                    os.environ.pop(_k, None)
            try:
                http_client = httpx.Client(trust_env=False)  
                client = OpenAI(api_key=api_key_clean, http_client=http_client)
            except TypeError as te:
                if "proxies" in str(te):
                    os.environ.pop("HTTP_PROXY", None)
                    os.environ.pop("HTTPS_PROXY", None)
                    os.environ.pop("http_proxy", None)
                    os.environ.pop("https_proxy", None)
                    http_client = httpx.Client(trust_env=False)  # ✅ Ignore all env vars including proxies
                    client = OpenAI(api_key=api_key_clean, http_client=http_client)
                else:
                    raise
            print(f"✅ Client 创建成功")
            
            # 测试 API（可选，但会消耗 1 次调用）
            # print(f"🧪 测试 API 连接...")
            # models = client.models.list()
            # print(f"✅ API 连接成功！")
            
    except Exception as e:
        print(f"❌ 初始化失败!")
        print(f"   错误类型: {type(e).__name__}")
        print(f"   错误信息: {str(e)}")
        import traceback
        print(f"   详细堆栈:")
        traceback.print_exc()
        client = None
else:
    print(f"❌ OPENAI_KEY 环境变量未找到")

print(f"\n最终状态: {'✅ client 可用' if client else '❌ client = None'}")
print("="*60 + "\n")

# 最后的状态提示
if client:
    print(f"✅ gpt-4o-mini LIVE")
else:
    if not OPENAI_KEY:
        print(f"⚠️ OPENAI_KEY 未设置 - 在 .env 中设置 OPENAI_KEY=sk-...")
    else:
        print(f"⚠️ OpenAI 未连接 - 请向上滚动查看「❌ 初始化失败」或「格式不正确」的具体错误")
print("")

# 🆕 Initialize SkillsetManager
skills_manager = None
if SKILLS_ENABLED:
    try:
        skills_manager = SkillsetManager("skills", verbose=False)
    except Exception as e:
        print(f"⚠️ Skills 加载失败: {e}")
        skills_manager = None

# 🆕 Phase 1: Intent Detector + Rules Engine (token optimization)
intent_detector = None
rules_engine = None
if RULES_SYSTEM_ENABLED and IntentDetector and RulesEngine:
    try:
        intent_detector = IntentDetector()
        rules_engine = RulesEngine('ai_rules', verbose=False)
    except Exception as e:
        print(f"⚠️ Rules system init failed: {e}")
        intent_detector = None
        rules_engine = None

# 🆕 Phase 2: Strategy Orchestrator
strategy_orchestrator = None
if ORCHESTRATOR_ENABLED and StrategyOrchestrator:
    try:
        strategy_orchestrator = StrategyOrchestrator("skills")
    except Exception as e:
        print(f"⚠️ Orchestrator init failed: {e}")
        strategy_orchestrator = None

print(f"🧠 GEEWONI AI 交易大脑 v7.1 - with Skills")
print(f"{'✅ gpt-4o-mini LIVE' if client else '⚠️ OpenAI 未连接 (检查 .env 中 OPENAI_KEY 或上方错误)'}")

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

def _get_extended_stock_data_yahoo(symbol):
    """Fallback: Yahoo Finance only (used when data_manager not available)"""
    try:
        import warnings
        warnings.filterwarnings('ignore')
        print(f"📡 Fetching {symbol} (Yahoo)...")
        ticker = yf.Ticker(symbol)
        hist_data = ticker.history(period="1mo", interval="1d")
        today_data = ticker.history(period="1d", interval="5m")
        if hist_data.empty or len(hist_data) < 2:
            return None
        current_price = float(hist_data['Close'].iloc[-1])
        ema_9 = float(hist_data['Close'].ewm(span=9, adjust=False).mean().iloc[-1])
        ema_21 = float(hist_data['Close'].ewm(span=21, adjust=False).mean().iloc[-1])
        ema_50 = float(hist_data['Close'].ewm(span=min(50, len(hist_data)), adjust=False).mean().iloc[-1]) if len(hist_data) >= 21 else None
        delta = hist_data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = float(100 - (100 / (1 + rs)).iloc[-1]) if not rs.empty else 50.0
        recent_high = float(hist_data['High'].tail(20).max())
        recent_low = float(hist_data['Low'].tail(20).min())
        week_high = float(hist_data['High'].tail(5).max())
        week_low = float(hist_data['Low'].tail(5).min())
        day_high = float(today_data['High'].max()) if not today_data.empty else recent_high
        day_low = float(today_data['Low'].min()) if not today_data.empty else recent_low
        avg_volume = float(hist_data['Volume'].tail(20).mean()) or 1.0
        current_volume = int(hist_data['Volume'].iloc[-1])
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        if current_price > ema_9 > ema_21:
            trend, trend_en = "强势看涨", "bullish"
        elif current_price < ema_9 < ema_21:
            trend, trend_en = "强势看跌", "bearish"
        elif current_price > ema_9:
            trend, trend_en = "弱势看涨", "bullish"
        else:
            trend, trend_en = "弱势看跌", "bearish"
        last_update = hist_data.index[-1].strftime('%Y-%m-%d %H:%M') if hasattr(hist_data.index[-1], 'strftime') else str(hist_data.index[-1])
        price_change_pct = float(((current_price - hist_data['Close'].iloc[-2]) / hist_data['Close'].iloc[-2]) * 100)
        result = {
            'symbol': symbol.upper(), 'current_price': current_price, 'ema_9': ema_9, 'ema_21': ema_21,
            'ema_50': ema_50, 'rsi': rsi, 'resistance': recent_high, 'support': recent_low,
            'week_high': week_high, 'week_low': week_low, 'day_high': day_high, 'day_low': day_low,
            'avg_volume': int(avg_volume), 'current_volume': current_volume, 'volume_ratio': volume_ratio,
            'trend': trend, 'trend_en': trend_en, 'price_change_pct': price_change_pct,
            'last_update': last_update, 'data_source': 'Yahoo Finance'
        }
        print(f"✅ {symbol}: ${current_price:.2f} | {trend} | RSI: {rsi:.0f}")
        return result
    except Exception as e:
        print(f"❌ {symbol} Error: {e}")
        return None


def get_extended_stock_data(symbol):
    """Get comprehensive stock data. Uses Data Manager (Finnhub + Yahoo) when available, else Yahoo only."""
    if RULES_SYSTEM_ENABLED and data_manager_get_stock:
        out = data_manager_get_stock(symbol.upper(), use_cache=True)
        if out:
            print(f"✅ {symbol}: ${out['current_price']:.2f} | {out['trend']} | RSI: {out['rsi']:.0f} | {out['data_source']}")
        return out
    return _get_extended_stock_data_yahoo(symbol)

config = load_config()

# AI Brain - handles everything
async def ai_brain(update: Update, context):
    global ai_usage_today
    
    if not update.message or not update.message.text:
        return
    
    if not client:  # 4 spaces
        # 更详细的错误信息
        await update.message.reply_text(  # 8 spaces
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
    
    # Phase 1: Intent detection (free, no API)
    if intent_detector:
        intent_data = intent_detector.detect(user_query)
        stock_symbols = intent_data.get('symbols', [])
        detected_intent = intent_data.get('intent', 'general')
        print(f"🎯 Intent: {detected_intent} | Symbols: {stock_symbols}")
    else:
        try:
            stock_symbols = list(set(re.findall(r'\b[A-Z]{2,5}\b', user_query)))[:3]
        except Exception:
            stock_symbols = []
        detected_intent = 'stock_analysis' if stock_symbols else 'general'

    # Fetch stock data when needed
    stock_data = {}
    stock_data_context = ""
    data_sources = []
    has_realtime_data = False
    
    if (detected_intent == 'stock_analysis' or stock_symbols) and stock_symbols:
        for symbol in list(set(stock_symbols))[:3]:
            data = get_extended_stock_data(symbol)
            if data:
                stock_data[symbol] = data
                data_sources.append(f"✅ {symbol}: {data.get('data_source', 'Yahoo')} ({data['last_update']})")
                has_realtime_data = True
            else:
                data_sources.append(f"⚠️ {symbol}: 无实时数据")
        
        if stock_data:
            stock_data_context = "\n\n📊 Market data (for analysis - explain in words, do not dump raw):\n"
            for sym, data in stock_data.items():
                stock_data_context += f"{sym}: ${data['current_price']:.2f} ({data['price_change_pct']:+.2f}%) | {data['trend']} | RSI {data['rsi']:.0f} | EMA9 ${data['ema_9']:.2f} EMA21 ${data['ema_21']:.2f} | support ${data['support']:.2f} resist ${data['resistance']:.2f} | vol {data['volume_ratio']:.2f}x\n"
            # Phase 2: Agent consensus
            if strategy_orchestrator:
                try:
                    first_sym = next(iter(stock_data))
                    consensus = strategy_orchestrator.get_consensus_signal(stock_data[first_sym], first_sym)
                    stock_data_context += f"\n🤖 Agent consensus: {consensus['summary']}\n"
                    if consensus.get('top_signals'):
                        stock_data_context += "Top strategies: " + ", ".join([f"{s['strategy']}({s['confidence']}%)" for s in consensus['top_signals']]) + "\n"
                except Exception as e:
                    print(f"Orchestrator consensus error: {e}")
            if skills_manager:
                try:
                    recommended_skills = []
                    for sym, data in stock_data.items():
                        skills = skills_manager.match_skill_to_market({
                            'trend': data.get('trend_en', 'neutral'),
                            'rsi': data.get('rsi', 50),
                            'volume_ratio': data.get('volume_ratio', 1.0),
                            'volatility': 'normal'
                        })
                        recommended_skills.extend(skills)
                    recommended_skills = list(set(recommended_skills))[:3]
                    if recommended_skills:
                        stock_data_context += "\nRecommended strategies: " + ", ".join(recommended_skills) + "\n"
                except Exception as e:
                    print(f"Skills error: {e}")
        else:
            stock_data_context = "\n\n⚠️ No real-time data - use your market knowledge and news.\n"
    
    # Build compact context for other intents
    if rules_engine and detected_intent == 'positions':
        trades = load_trades()
        open_pos = [t for t in trades if t.get('status') == 'open']
        stock_data_context = "\nOpen positions: " + json.dumps(open_pos, ensure_ascii=False, default=str) + "\n"
    elif rules_engine and detected_intent == 'performance':
        win_rate, wins, total = calculate_win_rate()
        stock_data_context = f"\nPerformance: {wins}/{total} wins ({win_rate:.1f}%), Weekly P&L: ${config['weekly_profit']}\n"
                
    # Call AI with rules-optimized prompt
    try:
        ai_usage_today += 1
        config['ai_usage'] = ai_usage_today
        save_config(config)
        
        print(f"🤖 OpenAI API (usage: {ai_usage_today}/{daily_limit})...")
        
        strategies = load_strategies()
        best_strategy = max(strategies.items(), key=lambda x: x[1]['profit']) if strategies else None
        learning = load_ai_learning()
        insights = learning['learning_insights']
        learning_context = ""
        if learning.get('total_recommendations', 0) > 0:
            tr = learning['total_recommendations']
            success_rate = (learning.get('recommendations_followed', 0) / tr * 100) if tr else 0
            learning_context = f"AI learning: success rate {success_rate:.1f}%, best RSI {insights['best_rsi_range']['min']:.0f}-{insights['best_rsi_range']['max']:.0f}, preferred strategies: {', '.join(insights.get('preferred_strategies', [])[:2]) or 'any'}\n"
        
        if rules_engine:
            relevant_rules = rules_engine.get_relevant_rules(detected_intent)
            watchlist_hint = ', '.join(config.get('priority', [])[:5]) if config.get('priority') else 'none'
            system_prompt = f"""{relevant_rules}

Account: weekly P&L ${config['weekly_profit']}/{config['weekly_goal']}. User may ask about any symbol; only fetch data for symbols mentioned in this message. Watchlist (context only): {watchlist_hint}.
Best strategy: {best_strategy[0] if best_strategy else 'N/A'} (profit ${best_strategy[1]['profit']:.2f}).
{learning_context}

Respond in user's language (Chinese/English). Max 150 words. Be conversational. Never dump raw numbers - explain what they mean."""
        else:
            system_prompt = f"""You are GEEWONI AI - day trading analyst. Account: ${config['weekly_profit']}/{config['weekly_goal']}. Best strategy: {best_strategy[0] if best_strategy else 'N/A'}.
{learning_context}
{stock_data_context if stock_data_context else "No stock data - answer from market knowledge."}
Reply: concise, conversational, in user language. Include entry/target/stop when analyzing stocks. Max 200 words."""

        user_prompt = user_query + (stock_data_context if stock_data_context else "")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=300,
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
        if stock_data_context and detected_intent == 'stock_analysis' and stock_symbols:
            if has_realtime_data:
                data_source_text = "\n".join(data_sources)
                prefix = f"🧠 <b>AI 交易分析</b>\n\n<b>📡 数据来源:</b>\n{data_source_text}\n\n"
            else:
                prefix = f"🧠 <b>AI 交易分析</b>\n\n<b>📰 数据来源: AI 市场知识 + 新闻分析</b>\n⚠️ 实时数据不可用\n\n"
            keyboard = []
            for symbol in stock_symbols[:3]:
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
            save_trades(trades)

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
        f"/news - 新闻摘要 (抓取+AI筛选)\n"
        f"/skills - 查看策略库 🆕\n"
        f"/skill [名称] - 策略详情 🆕\n"
        f"/learn - AI 学习报告 🆕\n"
        f"/usage - AI 使用量\n"
        f"/strategies - 策略表现\n"
        f"/strategy_report - 多策略代理排名 🆕\n"
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
        f"⭐ 观察: {', '.join(config.get('priority', [])[:5])}",
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

async def strategy_report_command(update: Update, context):
    """Phase 2: Show multi-agent strategy rankings and consensus summary."""
    if not strategy_orchestrator:
        await update.message.reply_text("⚠️ Strategy orchestrator not loaded. Check skills folder.")
        return
    try:
        rankings = strategy_orchestrator.get_rankings()
        lines = ["📊 <b>Strategy Agent Rankings</b>\n"]
        for i, r in enumerate(rankings[:12], 1):
            lines.append(f"{i}. <b>{r['name']}</b> | Win rate: {r['win_rate']:.1f}% | Trades: {r['total_trades']} | P&L: ${r['total_pnl']:.2f}")
        lines.append("\n💡 Use /strategies for trade-based strategy stats. Agents use skill rules + live data.")
        await update.message.reply_text("\n".join(lines), parse_mode='HTML')
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


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

async def news_command(update: Update, context):
    """Fetch and send news digest (same as 9 AM digest, on-demand)."""
    await update.message.reply_text("⏳ 抓取并筛选新闻中...")
    try:
        from news.news_scheduler import get_news_now
        msg, ok = await get_news_now(client)
        await update.message.reply_text(msg, parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"⚠️ 获取新闻失败: {e}")

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
    
    # No bulk fetch: /morning uses AI knowledge only (Option A). User can ask for a symbol later for details.
    watchlist_preview = ', '.join(config.get('priority', [])[:5]) or '无'
    data_context = f"""User's watchlist (for context only): {watchlist_preview}. No real-time data for this morning summary.

请基于你的知识、最新市场趋势和新闻，给出今日早盘摘要。用户如需某只股票详情可稍后单独询问。"""
    data_source = "早盘摘要基于 AI 知识库与市场趋势（未请求实时行情）"
    
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
        CommandHandler("strategy_report", strategy_report_command),
        CommandHandler("learn", learn_command),
        CommandHandler("skills", skills_command),
        CommandHandler("skill", skill_detail_command),
        CommandHandler("positions", positions_command),
        CommandHandler("morning", morning_summary),
        CommandHandler("news", news_command),
        CommandHandler("win", win),
        CommandHandler("loss", loss),
        CallbackQueryHandler(button_callback),
        MessageHandler(filters.TEXT & ~filters.COMMAND, route_message)
    ]
    
    # Add handlers
    for handler in handlers:
        application.add_handler(handler)
    
    # Phase 5: 9 AM Malaysia news digest
    try:
        from news.news_scheduler import start_news_scheduler
        start_news_scheduler(client)
    except Exception as e:
        print(f"⚠️ News scheduler not started: {e}")
    
    print("🚀 GEEWONI LIVE - Handling messages...")
    
    # 🔥 ONE LINE - Perfect for Windows/Docker
    await application.run_polling(drop_pending_updates=True)


# 🔥 Run WITHOUT nest_asyncio
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")