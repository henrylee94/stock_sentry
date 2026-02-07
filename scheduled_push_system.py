"""
定时推送系统 - 自动新闻和交易计划
每天在关键时间点自动发送信息到 Telegram
"""

import asyncio
from datetime import datetime, time
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot
import os

class ScheduledPushSystem:
    """定时推送系统"""
    
    def __init__(self, telegram_token, chat_id, skills_manager, client):
        self.bot = Bot(token=telegram_token)
        self.chat_id = chat_id
        self.skills_manager = skills_manager
        self.client = client  # OpenAI client
        self.scheduler = AsyncIOScheduler(timezone=pytz.timezone('Asia/Kuala_Lumpur'))
        
    async def start(self):
        """启动定时任务"""
        
        # 1. 早上 9:00 AM - 今日新闻摘要
        self.scheduler.add_job(
            self.morning_news_digest,
            CronTrigger(hour=9, minute=0, timezone='Asia/Kuala_Lumpur'),
            id='morning_news'
        )
        
        # 2. 晚上 9:15 PM - 美股开盘前交易计划
        self.scheduler.add_job(
            self.pre_market_trading_plan,
            CronTrigger(hour=21, minute=15, timezone='Asia/Kuala_Lumpur'),
            id='pre_market_plan'
        )
        
        # 3. 晚上 11:00 PM - 盘中监控更新（如果有持仓）
        self.scheduler.add_job(
            self.mid_market_update,
            CronTrigger(hour=23, minute=0, timezone='Asia/Kuala_Lumpur'),
            id='mid_market'
        )
        
        # 4. 凌晨 4:00 AM - 收盘总结
        self.scheduler.add_job(
            self.market_close_summary,
            CronTrigger(hour=4, minute=0, timezone='Asia/Kuala_Lumpur'),
            id='market_close'
        )
        
        # 5. 每小时检查重大新闻
        self.scheduler.add_job(
            self.check_breaking_news,
            CronTrigger(minute=0, timezone='Asia/Kuala_Lumpur'),
            id='breaking_news'
        )
        
        self.scheduler.start()
        print("✅ 定时推送系统已启动")
        print("📅 马来西亚时间:")
        print("   • 09:00 AM - 今日新闻摘要")
        print("   • 09:15 PM - 美股开盘前计划")
        print("   • 11:00 PM - 盘中更新")
        print("   • 04:00 AM - 收盘总结")
        print("   • 每小时 - 重大新闻检查")
    
    async def morning_news_digest(self):
        """早上 9:00 - 今日新闻摘要"""
        try:
            print("📰 生成早上新闻摘要...")
            
            # 调用 AI 生成新闻摘要
            prompt = f"""请生成今日（{datetime.now().strftime('%Y年%m月%d日 %A')}）的市场新闻摘要。

关注重点股票: NVDA, PLTR, RKLB, SOFI, OKLO, MP

包括:
1. 📰 隔夜重要新闻（美股收盘后的新闻）
2. 🌏 亚洲市场表现
3. 📊 影响今日美股的关键因素
4. ⚠️ 需要注意的风险事件

格式:
🌅 早安！今日市场摘要

[简短专业的新闻摘要，不超过200字]

💡 今日建议: [一句话]
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.4
            )
            
            news = response.choices[0].message.content
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=f"{news}\n\n⏰ {datetime.now().strftime('%H:%M')} | 自动推送",
                parse_mode='HTML'
            )
            
            print("✅ 早上新闻已发送")
            
        except Exception as e:
            print(f"❌ 早上新闻发送失败: {e}")
    
    async def pre_market_trading_plan(self):
        """晚上 9:15 PM - 美股开盘前交易计划"""
        try:
            print("📋 生成交易计划...")
            
            # 获取 watchlist 股票数据
            from get_extended_stock_data import get_extended_stock_data
            watchlist = ['NVDA', 'PLTR', 'RKLB', 'SOFI', 'OKLO', 'MP']
            
            stock_data_text = ""
            for symbol in watchlist[:5]:
                data = get_extended_stock_data(symbol)
                if data:
                    stock_data_text += f"{symbol}: ${data['current_price']:.2f} | RSI: {data['rsi']:.0f} | {data['trend']}\n"
            
            # AI 生成交易计划
            prompt = f"""美股即将开盘（15分钟后），请基于以下数据生成今晚的交易计划。

实时数据:
{stock_data_text}

要求:
1. 🎯 选出 1-2 只今晚最值得关注的股票
2. 📈 给出具体的入场点、目标位、止损
3. 📋 推荐使用的策略
4. ⚠️ 风险提示

格式:
🌙 今晚交易计划

🎯 重点关注: [股票]
💰 当前: $XXX
📈 入场: $XXX (条件)
🎯 目标: $XXX
🛑 止损: $XXX
📋 策略: [策略名称]

⚠️ 风险: [风险提示]

简短专业，中文回复。
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            
            plan = response.choices[0].message.content
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=f"{plan}\n\n⏰ 距离开盘: 15分钟 | 自动推送",
                parse_mode='HTML'
            )
            
            print("✅ 交易计划已发送")
            
        except Exception as e:
            print(f"❌ 交易计划发送失败: {e}")
    
    async def mid_market_update(self):
        """晚上 11:00 PM - 盘中更新"""
        try:
            # 检查是否有持仓
            # 如果有，发送更新
            # 如果没有，跳过
            
            # TODO: 检查持仓
            has_positions = False  # 从你的 trades.json 读取
            
            if not has_positions:
                print("📭 无持仓，跳过盘中更新")
                return
            
            # 生成持仓更新
            update_text = "💼 盘中持仓更新\n\n[持仓详情]\n\n⏰ 11:00 PM"
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=update_text,
                parse_mode='HTML'
            )
            
            print("✅ 盘中更新已发送")
            
        except Exception as e:
            print(f"❌ 盘中更新失败: {e}")
    
    async def market_close_summary(self):
        """凌晨 4:00 AM - 收盘总结"""
        try:
            print("📊 生成收盘总结...")
            
            # AI 生成收盘总结
            prompt = f"""美股刚刚收盘，请生成今日收盘总结。

要求:
1. 📊 今日大盘表现（SPY, QQQ）
2. 🔥 今日涨跌幅榜
3. 📰 影响市场的重大事件
4. 💡 明日关注点

格式:
🌃 今日收盘总结

[简短专业的总结，不超过150字]

⏰ {datetime.now().strftime('%H:%M')} | 自动推送
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.4
            )
            
            summary = response.choices[0].message.content
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=summary,
                parse_mode='HTML'
            )
            
            print("✅ 收盘总结已发送")
            
        except Exception as e:
            print(f"❌ 收盘总结失败: {e}")
    
    async def check_breaking_news(self):
        """每小时检查重大新闻"""
        try:
            # TODO: 实现新闻抓取和过滤
            # 只有当有重大新闻时才推送
            pass
        except Exception as e:
            print(f"❌ 新闻检查失败: {e}")
    
    def stop(self):
        """停止定时任务"""
        self.scheduler.shutdown()
        print("🛑 定时推送系统已停止")


# 使用示例
async def main():
    # 从环境变量获取
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")  # 你的 Telegram Chat ID
    
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_KEY"))
    
    from skillset_manager import SkillsetManager
    skills_manager = SkillsetManager("skills")
    
    # 创建推送系统
    push_system = ScheduledPushSystem(
        telegram_token=telegram_token,
        chat_id=chat_id,
        skills_manager=skills_manager,
        client=client
    )
    
    # 启动
    await push_system.start()
    
    # 保持运行
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        push_system.stop()


if __name__ == "__main__":
    asyncio.run(main())