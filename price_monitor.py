"""
实时价格监控系统
监控 watchlist 并在重要事件发生时提醒
"""

import asyncio
from datetime import datetime
import yfinance as yf
from typing import Dict, List
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

class PriceMonitor:
    """实时价格监控器"""
    
    def __init__(self, bot, chat_id, watchlist, skills_manager=None):
        self.bot = bot
        self.chat_id = chat_id
        self.watchlist = watchlist
        self.skills_manager = skills_manager
        
        # 监控状态
        self.price_history = {}  # 价格历史
        self.alert_thresholds = {}  # 提醒阈值
        self.last_alerts = {}  # 上次提醒时间（防止频繁提醒）
        
        # 默认监控规则
        self.rules = {
            'price_change': 3.0,  # 涨跌超过 3%
            'volume_spike': 2.0,  # 成交量超过 2x
            'rsi_oversold': 30,   # RSI < 30
            'rsi_overbought': 70,  # RSI > 70
            'breakout': True,     # 突破阻力/跌破支撑
        }
    
    def set_price_alert(self, symbol: str, target_price: float, direction: str = 'above'):
        """设置价格提醒"""
        self.alert_thresholds[symbol] = {
            'price': target_price,
            'direction': direction  # 'above' or 'below'
        }
        print(f"✅ 设置提醒: {symbol} {'突破' if direction == 'above' else '跌破'} ${target_price}")
    
    async def check_price_change(self, symbol: str, data: Dict) -> List[str]:
        """检查价格变化"""
        alerts = []
        
        price_change = data.get('price_change_pct', 0)
        current_price = data['current_price']
        
        # 1. 大涨大跌提醒
        if abs(price_change) >= self.rules['price_change']:
            emoji = "🚀" if price_change > 0 else "📉"
            alerts.append(f"{emoji} <b>{symbol} 大幅波动!</b>\n"
                         f"涨跌: {price_change:+.2f}%\n"
                         f"当前: ${current_price:.2f}")
        
        # 2. 价格目标提醒
        if symbol in self.alert_thresholds:
            threshold = self.alert_thresholds[symbol]
            target = threshold['price']
            direction = threshold['direction']
            
            if (direction == 'above' and current_price >= target) or \
               (direction == 'below' and current_price <= target):
                emoji = "✅" if direction == 'above' else "⚠️"
                alerts.append(f"{emoji} <b>{symbol} {'突破' if direction == 'above' else '跌破'}目标价!</b>\n"
                             f"目标: ${target:.2f}\n"
                             f"当前: ${current_price:.2f}")
                # 移除已触发的提醒
                del self.alert_thresholds[symbol]
        
        return alerts
    
    async def check_volume_spike(self, symbol: str, data: Dict) -> List[str]:
        """检查成交量异常"""
        alerts = []
        
        volume_ratio = data.get('volume_ratio', 1.0)
        
        if volume_ratio >= self.rules['volume_spike']:
            alerts.append(f"📊 <b>{symbol} 成交量激增!</b>\n"
                         f"成交量: {volume_ratio:.1f}x 平均\n"
                         f"当前: ${data['current_price']:.2f}")
        
        return alerts
    
    async def check_technical_signals(self, symbol: str, data: Dict) -> List[str]:
        """检查技术指标信号"""
        alerts = []
        
        rsi = data.get('rsi', 50)
        current_price = data['current_price']
        
        # 1. RSI 超买超卖
        if rsi <= self.rules['rsi_oversold']:
            alerts.append(f"⚠️ <b>{symbol} RSI 超卖!</b>\n"
                         f"RSI: {rsi:.0f}\n"
                         f"当前: ${current_price:.2f}\n"
                         f"💡 可能反弹机会")
        
        elif rsi >= self.rules['rsi_overbought']:
            alerts.append(f"🔥 <b>{symbol} RSI 超买!</b>\n"
                         f"RSI: {rsi:.0f}\n"
                         f"当前: ${current_price:.2f}\n"
                         f"⚠️ 注意回调风险")
        
        # 2. 突破阻力/支撑
        if self.rules['breakout']:
            resistance = data.get('resistance')
            support = data.get('support')
            
            if resistance and current_price >= resistance * 0.99:  # 接近阻力位
                alerts.append(f"🎯 <b>{symbol} 接近阻力位!</b>\n"
                             f"当前: ${current_price:.2f}\n"
                             f"阻力: ${resistance:.2f}\n"
                             f"💡 突破后看涨")
            
            elif support and current_price <= support * 1.01:  # 接近支撑位
                alerts.append(f"🛡️ <b>{symbol} 接近支撑位!</b>\n"
                             f"当前: ${current_price:.2f}\n"
                             f"支撑: ${support:.2f}\n"
                             f"⚠️ 守住支撑或下跌")
        
        return alerts
    
    async def check_strategy_signals(self, symbol: str, data: Dict) -> List[str]:
        """检查策略信号"""
        alerts = []
        
        if not self.skills_manager:
            return alerts
        
        # 匹配适合的策略
        market_condition = {
            'trend': data.get('trend_en', 'neutral'),
            'rsi': data.get('rsi', 50),
            'volume_ratio': data.get('volume_ratio', 1.0),
            'volatility': 'normal'
        }
        
        recommended_skills = self.skills_manager.match_skill_to_market(market_condition)
        
        if recommended_skills:
            skill_name = recommended_skills[0]
            skill = self.skills_manager.get_skill(skill_name)
            
            if skill:
                alerts.append(f"💡 <b>{symbol} 策略信号</b>\n"
                             f"推荐策略: {skill['name']}\n"
                             f"难度: {skill['difficulty']}\n"
                             f"描述: {skill['description'][:50]}...")
        
        return alerts
    
    async def monitor_stock(self, symbol: str):
        """监控单个股票"""
        try:
            # 获取最新数据
            from get_extended_stock_data import get_extended_stock_data
            data = get_extended_stock_data(symbol)
            
            if not data:
                return
            
            # 检查各种条件
            all_alerts = []
            all_alerts.extend(await self.check_price_change(symbol, data))
            all_alerts.extend(await self.check_volume_spike(symbol, data))
            all_alerts.extend(await self.check_technical_signals(symbol, data))
            all_alerts.extend(await self.check_strategy_signals(symbol, data))
            
            # 发送提醒
            if all_alerts:
                # 防止频繁提醒（同一股票30分钟内只提醒一次）
                last_alert_time = self.last_alerts.get(symbol, datetime.min)
                if (datetime.now() - last_alert_time).seconds < 1800:  # 30分钟
                    return
                
                # 构建消息
                message = f"🚨 <b>{symbol} 实时提醒</b>\n\n"
                message += "\n\n".join(all_alerts)
                message += f"\n\n⏰ {datetime.now().strftime('%H:%M')}"
                
                # 添加快速操作按钮
                keyboard = [
                    [
                        InlineKeyboardButton(f"买入 {symbol}", callback_data=f"buy_{symbol}"),
                        InlineKeyboardButton(f"分析 {symbol}", callback_data=f"analyze_{symbol}")
                    ],
                    [
                        InlineKeyboardButton("取消提醒", callback_data=f"mute_{symbol}")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
                
                self.last_alerts[symbol] = datetime.now()
                print(f"🔔 {symbol} 提醒已发送")
        
        except Exception as e:
            print(f"❌ 监控 {symbol} 失败: {e}")
    
    async def monitor_loop(self, interval: int = 300):
        """监控循环（每5分钟）"""
        print(f"👀 开始监控 {len(self.watchlist)} 只股票...")
        print(f"⏱️ 检查间隔: {interval} 秒")
        
        while True:
            try:
                # 检查市场是否开盘
                import pytz
                ny_tz = pytz.timezone('America/New_York')
                now_ny = datetime.now(ny_tz)
                
                # 周末不监控
                if now_ny.weekday() >= 5:
                    print("📅 周末休市，暂停监控")
                    await asyncio.sleep(3600)  # 1小时后再检查
                    continue
                
                # 只在美股交易时间监控（9:30 AM - 4:00 PM EST）
                market_open = now_ny.hour >= 9 and (now_ny.hour < 16 or (now_ny.hour == 9 and now_ny.minute >= 30))
                
                if not market_open:
                    print(f"🌙 美股休市中 ({now_ny.strftime('%H:%M EST')})")
                    await asyncio.sleep(1800)  # 30分钟后再检查
                    continue
                
                print(f"\n🔍 扫描中... ({now_ny.strftime('%H:%M EST')})")
                
                # 监控每只股票
                for symbol in self.watchlist:
                    await self.monitor_stock(symbol)
                    await asyncio.sleep(2)  # 避免 API 限制
                
                print(f"✅ 扫描完成，{interval}秒后继续")
                
            except Exception as e:
                print(f"❌ 监控循环错误: {e}")
            
            await asyncio.sleep(interval)
    
    async def start(self, interval: int = 300):
        """启动监控"""
        print("=" * 60)
        print("👀 实时价格监控系统")
        print("=" * 60)
        print(f"📊 监控股票: {', '.join(self.watchlist)}")
        print(f"⏱️ 检查间隔: {interval} 秒")
        print(f"📋 监控规则:")
        print(f"   • 价格变化: ±{self.rules['price_change']}%")
        print(f"   • 成交量: {self.rules['volume_spike']}x")
        print(f"   • RSI: <{self.rules['rsi_oversold']} 或 >{self.rules['rsi_overbought']}")
        print(f"   • 突破检测: {'开启' if self.rules['breakout'] else '关闭'}")
        print("=" * 60)
        
        await self.monitor_loop(interval)


# 使用示例
async def main():
    import os
    from telegram import Bot
    
    bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    watchlist = ['NVDA', 'PLTR', 'RKLB', 'SOFI', 'OKLO', 'MP']
    
    from skillset_manager import SkillsetManager
    skills_manager = SkillsetManager("skills")
    
    monitor = PriceMonitor(bot, chat_id, watchlist, skills_manager)
    
    # 可选：设置价格提醒
    monitor.set_price_alert('NVDA', 150.00, 'above')
    monitor.set_price_alert('PLTR', 80.00, 'below')
    
    # 启动监控（每5分钟检查一次）
    await monitor.start(interval=300)


if __name__ == "__main__":
    asyncio.run(main())