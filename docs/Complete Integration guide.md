# 🚀 完整系统集成指南

## 📦 新增的3个核心功能

### 1️⃣ 定时推送系统 (`scheduled_push_system.py`)

**自动在关键时间点推送信息**

时间表（马来西亚时间）:

- 09:00 AM - 今日新闻摘要
- 09:15 PM - 美股开盘前交易计划
- 11:00 PM - 盘中持仓更新
- 04:00 AM - 收盘总结
- 每小时 - 重大新闻检查

### 2️⃣ 新闻系统 (`news_system.py`)

**自动抓取、过滤、分析新闻**

功能:

- 从多个 RSS 源抓取新闻
- AI 过滤重要新闻（只推送真正重要的）
- 情绪分析（利好/利空）
- 避免重复推送

### 3️⃣ 价格监控 (`price_monitor.py`)

**实时监控并提醒**

监控内容:

- 大涨大跌 (>3%)
- 成交量异常 (>2x)
- RSI 超买超卖
- 突破阻力/支撑
- 策略信号

---

## 📋 安装步骤

### 1. 更新 requirements.txt

```txt
# 原有依赖
streamlit==1.38.0
yfinance==0.2.40
python-telegram-bot==21.4
python-dotenv==1.0.1
requests==2.31.0
pandas==2.2.2
numpy==1.26.4
openai==1.51.2
pytz==2024.1

# 🆕 新增依赖
apscheduler==3.10.4      # 定时任务
feedparser==6.0.10       # RSS 抓取
beautifulsoup4==4.12.3   # HTML 解析（可选）
```

### 2. 安装新依赖

```bash
py -3.12 -m pip install apscheduler feedparser beautifulsoup4 --break-system-packages
```

### 3. 获取你的 Telegram Chat ID

运行这个脚本获取你的 Chat ID:

```python
# get_chat_id.py
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
import os

async def get_id(update: Update, context):
    await update.message.reply_text(f"你的 Chat ID: {update.effective_chat.id}")

app = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()
app.add_handler(MessageHandler(filters.TEXT, get_id))

print("发送任何消息到 bot 获取 Chat ID...")
app.run_polling()
```

把获取到的 Chat ID 添加到 `.env`:

```
TELEGRAM_CHAT_ID=你的chat_id
```

---

## 🔧 集成到主 Bot

### 方案 A: 全新启动脚本（推荐）

创建 `start_full_system.py`:

```python
"""
完整系统启动脚本
同时运行: Bot + 定时推送 + 新闻 + 监控
"""

import asyncio
import os
from telegram.ext import Application
from openai import OpenAI

# 导入所有系统
from telegram_bot import main as bot_main
from scheduled_push_system import ScheduledPushSystem
from news_system import NewsSystem
from price_monitor import PriceMonitor
from skillset_manager import SkillsetManager

async def start_all_systems():
    """启动所有系统"""

    print("=" * 60)
    print("🚀 GEEWONI 完整交易系统启动中...")
    print("=" * 60)

    # 配置
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    openai_key = os.getenv("OPENAI_KEY")

    if not all([telegram_token, chat_id, openai_key]):
        print("❌ 缺少环境变量！")
        print("需要: TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, OPENAI_KEY")
        return

    # 初始化
    client = OpenAI(api_key=openai_key)
    skills_manager = SkillsetManager("skills")
    watchlist = ['NVDA', 'PLTR', 'RKLB', 'SOFI', 'OKLO', 'MP']

    # 1. 启动主 Bot
    print("\n1️⃣ 启动 Telegram Bot...")
    bot_task = asyncio.create_task(bot_main())

    # 2. 启动定时推送系统
    print("2️⃣ 启动定时推送系统...")
    push_system = ScheduledPushSystem(
        telegram_token=telegram_token,
        chat_id=chat_id,
        skills_manager=skills_manager,
        client=client
    )
    await push_system.start()

    # 3. 启动新闻系统（每小时检查）
    print("3️⃣ 启动新闻系统...")
    news_system = NewsSystem(client, watchlist)

    async def news_loop():
        while True:
            try:
                important_news = await news_system.fetch_and_filter()
                if important_news:
                    message = news_system.format_news_for_telegram(important_news)
                    from telegram import Bot
                    bot = Bot(token=telegram_token)
                    await bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
                    print(f"📰 推送 {len(important_news)} 条重要新闻")
            except Exception as e:
                print(f"❌ 新闻系统错误: {e}")

            await asyncio.sleep(3600)  # 1小时

    news_task = asyncio.create_task(news_loop())

    # 4. 启动价格监控
    print("4️⃣ 启动价格监控系统...")
    from telegram import Bot
    bot = Bot(token=telegram_token)
    monitor = PriceMonitor(bot, chat_id, watchlist, skills_manager)
    monitor_task = asyncio.create_task(monitor.start(interval=300))  # 5分钟

    print("\n" + "=" * 60)
    print("✅ 所有系统已启动!")
    print("=" * 60)
    print("\n📋 运行中的系统:")
    print("   • Telegram Bot - 对话式 AI 助手")
    print("   • 定时推送 - 早/晚自动摘要")
    print("   • 新闻系统 - 每小时抓取重要新闻")
    print("   • 价格监控 - 每5分钟检查异常")
    print("\n💡 按 Ctrl+C 停止所有系统\n")

    # 等待所有任务
    await asyncio.gather(bot_task, news_task, monitor_task)

if __name__ == "__main__":
    try:
        asyncio.run(start_all_systems())
    except KeyboardInterrupt:
        print("\n\n🛑 系统已停止")
```

### 方案 B: 单独运行

分别运行每个系统:

```bash
# Terminal 1: 主 Bot
py -3.12 telegram_bot.py

# Terminal 2: 定时推送
py -3.12 scheduled_push_system.py

# Terminal 3: 价格监控
py -3.12 price_monitor.py
```

---

## 🎯 达成你的目标：每周 $1,000

### 系统如何帮助你:

1. **定时推送** → 不会错过交易机会
   - 每天早上9:15PM 给你交易计划
   - 开盘前15分钟就知道今晚做什么

2. **新闻过滤** → 只看重要的
   - AI 帮你筛选真正影响股价的新闻
   - 不用浪费时间看无关新闻

3. **实时监控** → 抓住每个机会
   - 价格突破立即通知
   - 止损触发自动提醒
   - 不用一直盯盘

4. **12个策略** → 科学交易
   - 不是瞎猜，有策略支撑
   - 回测验证有效性
   - AI 学习优化

### 建议的交易节奏:

```
周一-周五:
09:00 AM - 收到新闻摘要
09:15 PM - 收到交易计划
09:30 PM - 美股开盘，执行计划
11:00 PM - 检查持仓
04:00 AM - 收盘总结

目标: 每天 $200 × 5天 = $1,000/周
```

---

## 📊 下一步：Web Dashboard 集成

你的 `tradesniper.py` 和网站可以：

### 1. 显示实时数据

- 当前持仓
- 今日盈亏
- 策略表现

### 2. 配置管理

- 设置 watchlist
- 调整监控规则
- 配置推送时间

### 3. 历史回测

- 测试策略
- 优化参数
- 查看图表

**我可以帮你把这些系统集成到 Web Dashboard！**

---

## 🆘 常见问题

### Q: Chat ID 在哪里？

A: 运行 `get_chat_id.py`，然后发消息给 bot

### Q: 可以自定义推送时间吗？

A: 可以！编辑 `scheduled_push_system.py` 的 CronTrigger

### Q: 如何添加更多新闻源？

A: 编辑 `news_system.py` 的 `rss_feeds` 列表

### Q: 监控太频繁怎么办？

A: 调整 `monitor.start(interval=300)` 的 interval

### Q: 如何部署到服务器24/7运行？

A: 推荐用 Zeabur / Railway / Heroku

---

## 🎉 完成！

现在你有一个**完整的智能交易助手**:

- ✅ AI 对话分析
- ✅ 12个专业策略
- ✅ 自动定时推送
- ✅ 智能新闻过滤
- ✅ 实时价格监控

**下载所有文件，开始测试！** 🚀

有问题随时问我！
