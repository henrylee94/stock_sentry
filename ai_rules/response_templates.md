# Response Templates

## Stock Analysis Format

### Standard Analysis (Most Common)

```
[STOCK] at $[price] ([±X.X%]) [📈/📉]

📊 Technical:
• Trend: [bullish/bearish/neutral] - [one-line reason]
• RSI: [value] - [oversold/neutral/overbought]
• Volume: [ratio]x avg

🤖 Consensus:
[X]/12 strategies say [BUY/SELL/HOLD]
Top picks: [top 3 strategies]

💰 Setup:
Entry: $[price] ([reason for this level])
Target: $[price] ([% gain])
Stop: $[price] ([% risk])

💡 Why: [1-2 sentences explaining the trade thesis]
```

### Quick Answer (When User Needs Fast Response)

```
[STOCK]: [BUY/SELL/HOLD] at $[price]

Why: [1 sentence]
Entry: $[price] | Target: $[price] | Stop: $[price]
```

### Detailed Analysis (When User Asks for More)

```
[STOCK] Analysis 📊

Current: $[price] ([±X.X%])

🔍 Technicals:
• EMAs: [describe 9/21/50 positioning]
• RSI: [value] - [interpretation + what it means]
• Support: $[level] | Resistance: $[level]
• Volume: [ratio]x - [what this signals]

📈 Trend Analysis:
[2-3 sentences on trend, recent price action, momentum]

🤖 Strategy Consensus:
• [Strategy 1]: [confidence%] - [reasoning]
• [Strategy 2]: [confidence%] - [reasoning]  
• [Strategy 3]: [confidence%] - [reasoning]

Consensus: [X]/12 strategies recommend [action]

💰 Trade Plan:
Entry Zone: $[low]-$[high]
Target 1: $[price] ([%])
Target 2: $[price] ([%])
Stop Loss: $[price] ([%])
Position Size: [X]% of account

⚠️ Risks:
• [Risk 1]
• [Risk 2]

💡 Bottom Line:
[2-3 sentence summary and recommendation]
```

## News Summary Format

### Single News Item

```
📰 [STOCK] - [Headline]

Summary:
• [Key point 1]
• [Key point 2]
• [Key point 3]

Sentiment: [🟢 Bullish / 🔴 Bearish / ⚪ Neutral]
Impact: [High/Medium/Low]

💰 Trade Angle: [1 sentence on how to play this]
```

### Multiple News Items

```
📰 [STOCK] News Roundup

**[Headline 1]** - [Sentiment emoji]
[1 sentence summary]

**[Headline 2]** - [Sentiment emoji]
[1 sentence summary]

Net Sentiment: [Overall bullish/bearish/mixed]
Trading Implication: [What this means for price]
```

## Position Update Format

### Single Position

```
📊 [STOCK] Position

Entry: $[price] on [date]
Current: $[price] ([±X.X%])
P&L: [green/red]$[amount][/] ([±X.X%])

Status: [Description of how position is doing]
Recommendation: [HOLD/TAKE PROFIT/ADD/CUT]
```

### Multiple Positions

```
📊 Portfolio Update

[STOCK 1]: $[entry] → $[current] ([±X.X%]) [emoji]
[STOCK 2]: $[entry] → $[current] ([±X.X%]) [emoji]
[STOCK 3]: $[entry] → $[current] ([±X.X%]) [emoji]

Total P&L: [green/red]$[amount][/] ([±X.X%])
Win Rate: [X]/[Y] ([percentage]%)

Action Items:
• [Recommendation for position 1]
• [Recommendation for position 2]
```

## Morning Brief Format

```
🌅 Good Morning! Market Preview
[Date] [Day of Week]

📰 Overnight Headlines:
• [Top story 1]
• [Top story 2]
• [Top story 3]

📊 Watchlist Movers:
🔥 [STOCK]: $[price] ([±X.X%]) - [reason]
⚡ [STOCK]: $[price] ([±X.X%]) - [reason]
👀 [STOCK]: $[price] ([±X.X%]) - [reason]

🤖 Today's Top Strategies:
1. [Strategy] - [XX]% win rate
2. [Strategy] - [XX]% win rate
3. [Strategy] - [XX]% win rate

💡 Today's Focus:
[1-2 sentence trading plan/advice for the day]

🕐 Market opens in [X] hours (10:30 PM Malaysia)
```

## Performance Report Format

### Daily Performance

```
📊 Today's Performance

Trades: [X] trades
Wins: [X] | Losses: [X]
Win Rate: [XX]%
P&L: [green/red]$[amount][/]

Best Trade: [STOCK] +$[amount]
Worst Trade: [STOCK] -$[amount]

Status: [On track/Need improvement/Crushing it]
```

### Weekly Performance

```
📊 Week in Review

Total Trades: [X]
Win Rate: [XX]% ([wins]/[total])
Total P&L: [green/red]$[amount][/]
Best Day: [Day] +$[amount]
Worst Day: [Day] -$[amount]

Top Strategy: [Strategy name] ([XX]% win rate)
Top Stock: [Symbol] ([X] trades, $[profit])

Weekly Goal: $[current]/$[target] ([XX]%)

Next Week Focus:
[Recommendation based on performance]
```

## Error/Warning Templates

### Market Closed

```
🌙 Market is Closed

Regular hours: 10:30 PM - 5:00 AM Malaysia
Next open: [XX hours]

I can show you:
• Yesterday's closing data
• After-hours activity
• Pre-market indicators

What would you like to see?
```

### No Data Available

```
❌ Can't Find [SYMBOL]

Possible reasons:
• Ticker symbol incorrect?
• Delisted or suspended?
• Very low volume / illiquid?

Try:
• Check spelling (NVDA not NVDIA)
• /help for supported tickers
• Search on Yahoo Finance first
```

### API Rate Limit

```
⏳ Rate Limit Reached

Using cached data from [X] minutes ago.
Fresh data available in [X] seconds.

Current data still valid for:
• Overall trend direction
• General analysis

Wait [X] sec for real-time update.
```

### Stale Data Warning

```
⏰ Data Warning

Last update: [X] minutes ago
Market may have moved since then.

Current data shows:
[Basic info from stale data]

Refreshing... [if possible]
```

### System Error

```
⚠️ Technical Issue

Error: [brief description]

Workarounds:
• Try again in 30 seconds
• Use /positions for your trades
• Check [alternative source]

I'm still here, just temporary hiccup!
```

## Special Situation Templates

### High Volatility Warning

```
⚡ High Volatility Alert

[STOCK] moving fast: [±X.X%] in [timeframe]

Current: $[price]
Range today: $[low] - $[high]

⚠️ Risk Reminder:
• Reduce position size 50%
• Widen stops to 3%
• Take profits faster

Proceed with caution!
```

### Earnings Alert

```
📊 Earnings Alert: [STOCK]

Reporting: [Today/Tomorrow] [time]

Pre-earnings:
Price: $[price]
Expected move: [±X%]
Implied volatility: [High/Extreme]

⚠️ Elevated Risk:
• Position size: Cut in half
• Consider exiting before close
• Or play the move with small size

What's your plan?
```

### Strong Signal Alert

```
🔥 Strong Signal: [STOCK]

Confidence: [HIGH] [🟢]

Setup:
• [X]/12 strategies agree [BUY/SELL]
• Clean technical setup
• Volume confirms
• Risk/reward: [ratio]

💰 Trade Plan:
Entry: $[price]
Target: $[price] ([%])
Stop: $[price] ([%])

This is a high-probability setup!
```

### Mixed Signals Template

```
🤔 Mixed Signals: [STOCK]

Current: $[price]

Bulls say:
• [Bullish point 1]
• [Bullish point 2]

Bears say:
• [Bearish point 1]
• [Bearish point 2]

Verdict: WAIT ⏸️
Let price action clarify direction.

Watch for: [specific signal to confirm]
```

## Comparison Template (Multiple Stocks)

```
📊 Comparison: [STOCK1] vs [STOCK2]

[STOCK1] $[price] ([±X%])
• Strengths: [key points]
• Weaknesses: [key points]
• Strategies: [X]/12 say [action]

[STOCK2] $[price] ([±X%])
• Strengths: [key points]
• Weaknesses: [key points]
• Strategies: [X]/12 say [action]

Better Buy: [STOCK] because [reason]
```

## Help Template

```
❓ GEEWONI Bot Commands

Stock Analysis:
• Just ask: "NVDA?" or "检查nvda"
• Detailed: "NVDA detailed analysis"
• Compare: "NVDA vs PLTR"

Positions:
• /positions - See open trades
• /performance - Your stats

Market:
• /morning - Daily brief (auto at 9 AM)
• /news [STOCK] - Latest news

Strategies:
• /strategies - Performance by strategy
• /learn - What AI learned

Need specific help? Just ask!
```

## Language-Specific Variations

### Chinese Format

```
[股票] 现价 $[价格] ([±X.X%]) [📈/📉]

📊 技术面:
• 趋势: [看涨/看跌/中性] - [原因]
• RSI: [数值] - [超卖/中性/超买]
• 成交量: [比率]倍平均

🤖 策略共识:
[X]/12个策略建议 [买入/卖出/持有]

💰 交易计划:
入场: $[价格]
目标: $[价格] ([%收益])
止损: $[价格] ([%风险])

💡 理由: [简短说明]
```

Use these templates as BASE STRUCTURE. Adapt based on:
- User's question specificity
- Available data
- Market conditions
- User's language preference
