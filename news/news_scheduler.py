"""
News scheduler: 9 AM Malaysia time daily digest via Telegram.
Uses NewsSystem to fetch/filter/summarize, then sends to TELEGRAM_CHAT_ID.
"""

import os
import asyncio
from datetime import datetime

try:
    import pytz
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from telegram import Bot
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False

MY_TZ = "Asia/Kuala_Lumpur"
_scheduler = None


async def _run_morning_digest():
    """Job: fetch news, summarize, send to Telegram."""
    token = os.getenv("TELEGRAM_TOKEN_LOCAL") or os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("⚠️ News scheduler: TELEGRAM_TOKEN or TELEGRAM_CHAT_ID missing")
        return
    try:
        from core import load_config
        from openai import OpenAI
        from news.news_system import NewsSystem

        config = load_config()
        watchlist = config.get("priority") or config.get("watchlist") or ["NVDA", "PLTR", "RKLB"]
        client = OpenAI(api_key=os.getenv("OPENAI_KEY"))
        if not os.getenv("OPENAI_KEY"):
            print("⚠️ News scheduler: OPENAI_KEY missing")
            return

        news_system = NewsSystem(client, watchlist[:8])
        important = await news_system.fetch_and_filter()
        if important:
            summary = await news_system.get_daily_summary_paragraph(important)
            header = f"🌅 <b>早安！今日市场摘要</b>\n{datetime.now().strftime('%Y-%m-%d %H:%M')} (MY)\n\n"
            body = summary + "\n\n"
            body += news_system.format_news_for_telegram(important)
            text = header + body
        else:
            text = f"🌅 <b>早安！今日市场摘要</b>\n{datetime.now().strftime('%Y-%m-%d %H:%M')} (MY)\n\n📭 今日暂无重要新闻。"

        bot = Bot(token=token)
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
        print("✅ 9 AM news digest sent")
    except Exception as e:
        print(f"❌ Morning digest failed: {e}")


def start_news_scheduler(client=None):
    """Start the 9 AM Malaysia news job. Call from telegram_bot main()."""
    global _scheduler
    if not SCHEDULER_AVAILABLE:
        print("⚠️ apscheduler/pytz/telegram not installed - news scheduler disabled")
        return
    if _scheduler is not None:
        return
    token = os.getenv("TELEGRAM_TOKEN_LOCAL") or os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not chat_id:
        print("⚠️ TELEGRAM_CHAT_ID not set - news scheduler disabled")
        return
    _scheduler = AsyncIOScheduler(timezone=pytz.timezone(MY_TZ))
    _scheduler.add_job(
        _run_morning_digest,
        CronTrigger(hour=9, minute=0, timezone=MY_TZ),
        id="morning_news_digest",
    )
    _scheduler.start()
    print("✅ News scheduler started (9:00 AM Malaysia)")


async def get_news_now(client, watchlist=None):
    """
    On-demand: fetch, filter, summarize. Returns (message_text, success).
    For /news command.
    """
    if not client:
        return "⚠️ AI 不可用。请设置 OPENAI_KEY。", False
    try:
        from core import load_config
        from news.news_system import NewsSystem

        if not watchlist:
            config = load_config()
            watchlist = config.get("priority") or config.get("watchlist") or ["NVDA", "PLTR", "RKLB"]
        news_system = NewsSystem(client, watchlist[:8])
        important = await news_system.fetch_and_filter()
        if important:
            summary = await news_system.get_daily_summary_paragraph(important)
            header = "📰 <b>新闻摘要</b>\n\n"
            header += summary + "\n\n"
            msg = header + news_system.format_news_for_telegram(important)
        else:
            msg = "📭 暂无重要新闻。"
        return msg, True
    except Exception as e:
        print(f"❌ get_news_now: {e}")
        return f"⚠️ 获取新闻失败: {e}", False
