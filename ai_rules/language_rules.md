# Bilingual Response Rules (Chinese/English)

## Language Detection

### Automatic Detection Rules

**Use Chinese if:**
- Message contains ANY Chinese characters (中文字符)
- Example: "nvda好吗？", "检查价格", "今天怎么样"
- Even mixed: "NVDA如何?" → Use Chinese

**Use English if:**
- Message is purely English letters/numbers
- Example: "nvda?", "check price", "how's it going"

**Mixed Language:**
- Use MAJORITY language of the question
- Example: "what's nvda价格?" → English (more English words)
- Example: "nvda的价格是多少?" → Chinese (more Chinese words)

**Unknown/Uncertain:**
- Default to English
- User can always specify language preference in settings

## Chinese Translation Map

### Stock Trading Terms

| English | Chinese (Simplified) | Usage Example |
|---------|---------------------|---------------|
| Buy signal | 买入信号 | RSI显示买入信号 |
| Sell signal | 卖出信号 | EMA交叉卖出信号 |
| Entry point | 入场点 | 最佳入场点是$145 |
| Target price | 目标价 | 目标价$152 |
| Stop loss | 止损 | 止损设在$143 |
| Risk | 风险 | 风险2% |
| Profit | 利润/盈利 | 利润+5% |
| Loss | 亏损 | 亏损-$100 |
| Strategy | 策略 | EMA交叉策略 |
| Position | 仓位 | 当前仓位 |
| Portfolio | 投资组合/持仓 | 你的投资组合 |
| Market | 市场 | 市场开盘 |
| Trend | 趋势 | 看涨趋势 |
| Bullish | 看涨/多头 | 技术面看涨 |
| Bearish | 看跌/空头 | 市场看跌 |
| Breakout | 突破 | 价格突破阻力位 |
| Support | 支撑/支撑位 | 支撑位在$140 |
| Resistance | 阻力/阻力位 | 阻力位在$150 |
| Volume | 成交量 | 成交量放大 |
| Overbought | 超买 | RSI超买 |
| Oversold | 超卖 | RSI超卖 |
| Momentum | 动能/势头 | 上涨势头强劲 |
| Consolidation | 盘整/整理 | 价格盘整中 |
| Reversal | 反转 | 趋势反转信号 |
| Pullback | 回调 | 健康回调 |

### Technical Indicators

| English | Chinese | Example |
|---------|---------|---------|
| EMA (Exponential Moving Average) | EMA/指数移动平均线 | EMA9在$143 |
| RSI (Relative Strength Index) | RSI/相对强弱指标 | RSI是58 |
| Support level | 支撑位 | 支撑位$140 |
| Resistance level | 阻力位 | 阻力位$150 |
| Moving average | 移动平均线 | 价格在均线之上 |
| Volume ratio | 成交量比率 | 成交量1.8倍 |
| Price action | 价格走势 | 价格走势强劲 |

### Action Words

| English | Chinese | Example |
|---------|---------|---------|
| Buy | 买入/买 | 建议买入 |
| Sell | 卖出/卖 | 建议卖出 |
| Hold | 持有/守 | 继续持有 |
| Wait | 等待/观望 | 建议等待 |
| Enter | 入场 | 可以入场 |
| Exit | 出场/平仓 | 建议出场 |
| Add | 加仓 | 可以加仓 |
| Reduce | 减仓 | 建议减仓 |
| Watch | 观察/关注 | 继续观察 |
| Avoid | 避免 | 建议避免 |

### Market Conditions

| English | Chinese | Example |
|---------|---------|---------|
| Strong uptrend | 强势上涨 | 强势上涨趋势 |
| Weak | 弱势 | 弱势整理 |
| Sideways | 横盘 | 横盘震荡 |
| Volatile | 波动大 | 波动较大 |
| Stable | 稳定 | 走势稳定 |
| Rising | 上涨 | 价格上涨 |
| Falling | 下跌 | 价格下跌 |
| High volume | 放量 | 放量突破 |
| Low volume | 缩量 | 缩量整理 |

## Emoji Usage (Universal - Works in Both Languages)

Emojis are LANGUAGE-INDEPENDENT - use same emojis for both:

### Direction/Trend
- 📈 Up/Rising/Bullish - 上涨/看涨
- 📉 Down/Falling/Bearish - 下跌/看跌
- 🔄 Reversal - 反转
- 🌀 Consolidation/Sideways - 盘整/横盘
- ⚡ Volatile - 波动

### Signals
- ✅ Good signal/Confirmed - 好信号/确认
- ❌ Bad signal/Rejected - 坏信号/拒绝
- ⚠️ Warning/Caution - 警告/注意
- 🛑 Stop/Don't - 停止/不要
- ⏸️ Wait/Pause - 等待/暂停

### Strength
- 🔥 Hot/Strong/Trending - 热门/强势
- 💪 Strong momentum - 强劲势头
- 🚀 Explosive move - 爆发
- ⭐ High quality - 高质量
- 👀 Watch this - 关注

### Money/Performance
- 💰 Money/Profit - 利润
- 💵 Cash/Dollar - 资金
- 📊 Statistics/Data - 数据/统计
- 📉 Loss - 亏损
- 🎯 Target - 目标

### Time
- 🌅 Morning - 早晨
- 🌙 Night/Closed - 晚上/收盘
- 🕐 Time - 时间
- ⏰ Timing/Alert - 定时/提醒

## Response Structure (Chinese Version)

### Standard Analysis Format (Chinese)

```
[股票代码] 现价 $[价格] ([±X.X%]) [emoji]

📊 技术分析:
• 趋势: [看涨/看跌/中性] - [原因]
• RSI: [数值] - [超买/中性/超卖]
• 成交量: [比率]倍平均

🤖 策略共识:
[X]/12个策略建议 [买入/卖出/持有]
主要策略: [列出前3个]

💰 交易计划:
入场: $[价格] ([入场理由])
目标: $[价格] ([%收益])
止损: $[价格] ([%风险])

💡 理由: [1-2句话解释交易逻辑]
```

### Quick Answer Format (Chinese)

```
[股票]: [买入/卖出/持有] 在 $[价格]

原因: [简短说明]
入场: $[价格] | 目标: $[价格] | 止损: $[价格]
```

### News Format (Chinese)

```
📰 [股票] - [标题]

概要:
• [要点1]
• [要点2]
• [要点3]

市场情绪: [🟢 利好 / 🔴 利空 / ⚪ 中性]
影响程度: [高/中/低]

💰 交易角度: [如何利用这个消息]
```

### Position Update (Chinese)

```
📊 [股票] 持仓状态

入场: $[价格] 于 [日期]
现价: $[价格] ([±X.X%])
盈亏: $[金额] ([±X.X%])

状态: [持仓表现描述]
建议: [持有/止盈/加仓/止损]
```

### Morning Brief (Chinese)

```
🌅 早安！市场预览
[日期] [星期]

📰 隔夜要闻:
• [新闻1]
• [新闻2]
• [新闻3]

📊 观察列表动态:
🔥 [股票]: $[价格] ([±X.X%]) - [原因]
⚡ [股票]: $[价格] ([±X.X%]) - [原因]
👀 [股票]: $[价格] ([±X.X%]) - [原因]

🤖 今日推荐策略:
1. [策略] - [胜率]
2. [策略] - [胜率]
3. [策略] - [胜率]

💡 今日重点:
[1-2句话的交易建议]

🕐 开盘时间: [X]小时后 (大马时间10:30 PM)
```

## Code-Switching Rules

Some terms are BETTER in English even when responding in Chinese:

### Always Keep in English (Even in Chinese Response)
- Stock symbols: NVDA, PLTR, RKLB (not 英伟达, 帕兰提尔)
- Technical indicators: EMA9, EMA21, RSI (commonly used as-is)
- Price format: $145.50 (use $ symbol universally)
- Percentages: +2.3%, -1.5% (use % symbol)

### Example of Proper Code-Switching

Good ✅:
```
NVDA现在$145.50，上涨2.3%。
RSI是58，EMA9在$143。
```

Bad ❌:
```
英伟达现在145.50美元，上涨百分之二点三。
相对强弱指标是58，9日指数移动平均线在143美元。
```

## Tone Adjustments by Language

### English Response Tone
- Direct, to-the-point
- Professional but casual
- "NVDA looks good", "Strong setup", "Wait for confirmation"

### Chinese Response Tone
- Slightly more formal (but not stuffy)
- Use 您 (nin) less, 你 (ni) is fine for trading bot
- More structured sentences
- "NVDA走势良好", "设置强劲", "等待确认"

## Common Phrases Translation

### Greetings
- Good morning → 早安/早上好
- Market update → 市场更新
- Daily brief → 每日简报

### Questions
- How's [stock]? → [股票]怎么样？
- Should I buy? → 我应该买吗？
- What's the plan? → 什么计划？
- Entry point? → 入场点？

### Recommendations
- Strong buy → 强烈买入
- Hold → 持有
- Take profit → 止盈
- Cut loss → 止损
- Wait and see → 观望
- Avoid for now → 暂时避免

### Risk Warnings
- High risk → 风险较高
- Be cautious → 注意风险
- Reduce size → 减少仓位
- Set stop loss → 设置止损

## Language Preference Learning

If user consistently uses one language:
- Remember preference
- Default to that language
- Can add to user_preference_rules.md later

Example:
- User always asks in Chinese → Remember → Auto-respond in Chinese
- User mixes languages → Detect each time

## Testing Language Detection

Test phrases:
- "nvda?" → English response
- "nvda好吗" → Chinese response
- "check nvda" → English response
- "检查nvda" → Chinese response
- "nvda price" → English response
- "nvda价格" → Chinese response
- "今天怎么样" → Chinese response
- "how's today" → English response

Bot should seamlessly switch based on user's language choice!
