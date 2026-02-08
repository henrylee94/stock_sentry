# Trading Strategy Rules

## When to Use Each Strategy

### Trending Market (Strong Directional Movement)

**EMA Crossover** - Best for established trends
- Use when: Price > EMA9 > EMA21 (uptrend) or Price < EMA9 < EMA21 (downtrend)
- Confidence: HIGH when all 3 EMAs aligned
- Entry: On pullback to EMA9, or breakout above recent high
- Exit: When EMA9 crosses opposite direction

**Volume Breakout** - Best for momentum plays
- Use when: Price breaking key level + volume > 2x average
- Confidence: HIGH when breakout + volume confirms
- Entry: On breakout candle close above resistance
- Exit: Volume dries up or reversal pattern forms

**Trend Following** - Best for riding established trends
- Use when: Clear series of higher highs/higher lows (or inverse)
- Confidence: HIGH when trend is > 3 days old
- Entry: Buy dips in uptrend, sell rallies in downtrend
- Exit: Trend structure breaks (lower low in uptrend)

### Ranging/Choppy Market (No Clear Direction)

**Support/Resistance** - Best for range-bound conditions
- Use when: Price bouncing between clear levels 3+ times
- Confidence: MEDIUM-HIGH when levels well established
- Entry: Near support (buy) or resistance (sell)
- Exit: Opposite level reached, or level breaks

**Mean Reversion** - Best when price stretched
- Use when: RSI < 30 (oversold) or > 70 (overbought)
- Confidence: MEDIUM when no strong trend present
- Entry: RSI extreme + reversal candle pattern
- Exit: RSI returns to 45-55 range

**RSI Divergence** - Best for early reversal detection
- Use when: Price makes new high/low but RSI doesn't confirm
- Confidence: MEDIUM-HIGH when divergence clear on 2+ timeframes
- Entry: After confirmation candle (reversal pattern)
- Exit: Target is previous swing point

### High Volatility Market

**Volatility Trading** - Best when VIX > 20
- Use when: Large daily ranges (>5%), increased uncertainty
- Confidence: MEDIUM due to unpredictable swings
- Entry: Smaller position size, wait for stabilization
- Exit: Tighter stops (1.5% instead of 2%)

**Gap Trading** - Best for overnight gaps
- Use when: Gap > 3% at open
- Confidence: MEDIUM (50/50 fade vs follow)
- Gap up: If volume weak → fade, if strong → follow
- Gap down: If fear selling → fade, if news-driven → follow

### News-Driven Market

**Catalyst Trading** - Best for event-driven moves
- Use when: Known catalyst within 24 hours (earnings, FDA, M&A)
- Confidence: MEDIUM-HIGH if historical pattern clear
- Entry: Before event (risky) or after event on confirmation
- Exit: Same day or next day (don't overstay)

**Earnings Play** - Best for quarterly earnings
- Use when: Earnings announcement today/tomorrow
- Confidence: MEDIUM (high risk, high reward)
- Entry: Before close (risky) or at open next day
- Exit: Usually within 1-2 hours of open (volatility spike)

**Sector Rotation** - Best for macro trends
- Use when: Economic cycle changes favor certain sectors
- Confidence: LOW-MEDIUM (longer-term, not day trading)
- Entry: Start of quarter when rotation typically happens
- Exit: End of quarter or when cycle changes

## Strategy Confidence Levels

### High Confidence (>80%) - Green Light 🟢
- 3+ strategies agree on same direction
- Volume confirms move (>1.5x average)
- Clean technical setup (no conflicting signals)
- Clear market condition match
→ **Action**: Full position size (up to 5% of account)

### Medium Confidence (50-80%) - Yellow Light 🟡  
- 2 strategies agree
- Volume normal (0.8-1.5x average)
- Some contradicting indicators but overall bullish/bearish
→ **Action**: Half position size (2-3% of account)

### Low Confidence (<50%) - Red Light 🔴
- Only 1 strategy or strategies conflict
- Low volume (<0.8x average)
- Mixed/choppy price action
→ **Action**: WAIT or paper trade only

## Quick Strategy Selection Algorithm

When user asks for analysis without specifying strategy:

1. **Check market condition**:
   - Trending up → Use EMA Crossover + Volume Breakout + Trend Following
   - Trending down → Use EMA Crossover + Trend Following (short bias)
   - Ranging → Use Support/Resistance + Mean Reversion
   - High volatility → Use Volatility Trading + tighter stops

2. **Check recent performance**:
   - Use top 3 performing strategies from last 7 days
   - Weight recommendations by win rate

3. **Default recommendation**:
   - If unsure: EMA Crossover + Volume Breakout + Support/Resistance
   - These 3 work in most conditions

## Risk Management Integration

Every strategy recommendation MUST include:
- **Entry price range** (not single price - give 5-10 cent range)
- **Target price** (where to take profit)
- **Stop loss** (where to cut losses - NON-NEGOTIABLE)
- **Position size** (% of account to risk)
- **Time frame** (how long to hold - day trade vs swing)

## Combining Strategies

Can combine 2-3 strategies for higher confidence:

**Power Combo 1**: EMA Crossover + Volume Breakout
- Wait for EMA9 > EMA21 cross + volume spike
- Very high confidence when both align
- Win rate: 65-70%

**Power Combo 2**: Support + Mean Reversion
- Price at support + RSI oversold
- Classic bounce setup
- Win rate: 60-65%

**Power Combo 3**: Catalyst + Volatility Trading
- News event + increased volatility
- High risk but high reward
- Win rate: 55-60% but larger moves

## Strategy Performance Tracking

Always mention recent performance when recommending:
- "EMA Crossover: 8-2 last 10 trades (80% win rate)"
- "Volume Breakout: Currently top performer this week"
- "Mean Reversion: 5-5 recently (be cautious, mixed results)"

## What NOT to Do

❌ Don't use complex strategies for simple setups
❌ Don't combine too many strategies (max 3)
❌ Don't recommend high-risk strategies to conservative traders
❌ Don't ignore market condition (don't trend-follow in range)
❌ Don't recommend strategies that conflict with each other
