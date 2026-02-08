# Market Condition Detection Rules

## Market Hours (Malaysia Time - User's Timezone)

### US Stock Market Schedule
- **Pre-market**: 8:00 PM - 10:30 PM Malaysia (4:00 AM - 9:30 AM EST)
- **Regular hours**: 10:30 PM - 5:00 AM next day Malaysia (9:30 AM - 4:00 PM EST)
- **After-hours**: 5:00 AM - 8:00 AM Malaysia (4:00 PM - 8:00 PM EST)
- **Market closed**: 8:00 AM - 8:00 PM Malaysia (weekends and holidays)

### Important Times (Malaysia Time)
- **9:00 AM**: User's preferred news briefing time
- **10:00 PM - 11:00 PM**: Morning work time, user might check markets
- **11:00 PM**: Market opening (most volatile hour)
- **2:00 AM - 3:00 AM**: Mid-session, often calmer
- **4:30 AM - 5:00 AM**: Power hour (volatile close)

## Market Condition Classification

### Strong Uptrend 📈🟢
**Indicators:**
- Price > EMA9 > EMA21 > EMA50 (all aligned)
- RSI: 55-70 (strong but not overbought)
- Volume: Above average (>1.2x)
- Making higher highs and higher lows

**Trading Approach:**
- Look for pullbacks to EMA9 or EMA21 to buy
- Don't chase after big green candles
- Set stops below recent swing low
- Take profits at resistance or when RSI > 75

**Risk Level:** LOW (trend is your friend)

### Strong Downtrend 📉🔴
**Indicators:**
- Price < EMA9 < EMA21 < EMA50 (all aligned down)
- RSI: 30-45 (weak but not oversold)
- Volume: Above average on down moves
- Making lower highs and lower lows

**Trading Approach:**
- Avoid catching falling knives
- Wait for clear reversal signals (hammer candle, RSI divergence)
- If shorting: Rally to EMA9 is entry, stop above recent high
- Best to WAIT for stabilization

**Risk Level:** HIGH (fighting trend is dangerous)

### Range-Bound / Choppy 🔄⚪
**Indicators:**
- Price oscillating between clear support and resistance
- EMAs flat or tangled (no clear order)
- Volume: Normal or below average
- No clear trend, back-and-forth movement

**Trading Approach:**
- Buy near support, sell near resistance
- Quick profits (3-5% targets)
- Tight stops (break of range = exit)
- Reduce position size (chop can whipsaw)

**Risk Level:** MEDIUM (no directional edge)

### High Volatility / Uncertain ⚡🟡
**Indicators:**
- Daily range > 5%
- VIX > 25
- Volume spikes erratically
- Large candles in both directions

**Trading Approach:**
- REDUCE position sizes by 50%
- WIDEN stop losses (2% → 3%)
- Take profits faster (don't be greedy)
- Consider sitting out if too chaotic

**Risk Level:** VERY HIGH (unpredictable swings)

### Consolidation / Coiling 🌀⚪
**Indicators:**
- Tightening price range (lower highs, higher lows)
- Volume declining
- Typically follows large move
- "Calm before storm"

**Trading Approach:**
- WAIT for breakout direction
- When breaks: Enter with high conviction
- Coils often lead to explosive moves
- Set alerts at consolidation boundaries

**Risk Level:** LOW while consolidating, MEDIUM after breakout

## Economic Calendar Impact

### High Impact Events (User should know about)

**Federal Reserve Announcements** (2:00 AM Malaysia / 2:00 PM EST)
- Interest rate decisions
- FOMC meeting minutes
- Powell speeches
→ **Action**: Avoid trading 1 hour before and during
→ **After**: High volatility, wait for direction to clear

**Jobs Report** (1st Friday, 8:30 PM Malaysia / 8:30 AM EST)
- Non-farm payrolls
- Unemployment rate
→ **Action**: Markets very volatile 8:30-10:00 PM Malaysia
→ **Opportunity**: Big moves if positioned correctly

**CPI/Inflation Data** (Usually 8:30 PM Malaysia / 8:30 AM EST)
- Consumer Price Index
- Producer Price Index
→ **Action**: Market sensitive to inflation, expect reaction

**Earnings Season** (Quarterly: Jan, Apr, Jul, Oct)
- Individual stock volatility increases
- Sector rotation common
→ **Action**: Focus on stocks reporting earnings

### Medium Impact Events

- GDP reports
- Retail sales
- Manufacturing PMI
- Housing data

→ **Action**: Watch for surprises, but usually less volatile

### Low Impact Events

- Weekly jobless claims
- Consumer confidence surveys

→ **Action**: Usually can ignore, minor market impact

## Sector-Specific Conditions

### Tech Sector (NVDA, PLTR - User's Focus)
- Follows NASDAQ/QQQ closely
- Sensitive to: Interest rates, chip demand, AI hype
- Often leads market (up first in rally, down first in selloff)
- High beta (moves more than market average)

### Small Cap / Speculative (RKLB, OKLO, MP - User's Focus)
- Higher volatility than large caps
- Sensitive to: Risk appetite, sector-specific news
- Lower liquidity (bigger spreads)
- Needs higher volume to validate moves

### General Market Context

**Bull Market Signs:**
- Most stocks making new highs
- Low VIX (<15)
- Economic data positive
- Fed dovish (supportive)

**Bear Market Signs:**
- Stocks breaking support levels
- High VIX (>25)
- Economic data weak
- Fed hawkish (raising rates)

**Transition Period:**
- Mixed signals
- Sector rotation active
- Choppy price action
- Be more cautious

## Real-Time Condition Detection

When analyzing a stock RIGHT NOW:

1. **Check EMAs** → Determines trend direction
2. **Check RSI** → Determines momentum strength
3. **Check Volume** → Confirms or questions the move
4. **Check time of day** → Early morning more volatile
5. **Check recent news** → Is there a catalyst?

Then classify as:
- Strong Uptrend
- Strong Downtrend  
- Range-Bound
- High Volatility
- Consolidation

And adjust strategy recommendation accordingly!
