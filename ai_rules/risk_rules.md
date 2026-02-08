# Risk Management Rules

## Golden Rule
**NEVER risk more than you can afford to lose. Stop loss is MANDATORY, not optional.**

## Position Sizing (MANDATORY FOR EVERY TRADE)

### Account-Based Position Sizing

**Small Account (<$10,000)**
- Max 3% risk per trade
- Example: $5,000 account → Max $150 risk per trade
- If stop loss is 2% away → Position size = $7,500 (150 shares if $50 stock)

**Medium Account ($10,000 - $50,000)**
- Max 5% risk per trade  
- Example: $25,000 account → Max $1,250 risk per trade
- More flexibility for multiple positions

**Large Account (>$50,000)**
- Max 7% risk per trade
- Can diversify across more positions
- Still respect risk limits

### Volatility-Adjusted Position Sizing

**Low Volatility Stock** (daily range <2%)
- Use standard position size
- Example: Stable blue chip moving 1-2% per day

**Medium Volatility Stock** (daily range 2-5%)
- Reduce position size by 25%
- Example: NVDA, PLTR on normal days

**High Volatility Stock** (daily range >5%)  
- Reduce position size by 50%
- Example: RKLB, OKLO, speculative small caps
- Wider stops needed, so smaller size to maintain same $ risk

### Position Size Calculator Formula

```
Position Size = (Account Risk $) / (Entry Price - Stop Price)

Example:
Account: $20,000
Risk tolerance: 5% = $1,000
Entry: $100
Stop: $98 (2% below entry)
Position Size = $1,000 / ($100 - $98) = $1,000 / $2 = 500 shares

Max investment: 500 shares × $100 = $50,000 → TOO LARGE
Need to respect also: Max 20% of account = $4,000
So actual: 40 shares ($4,000) with $2 stop = $80 total risk
```

## Stop Loss Rules (NON-NEGOTIABLE)

Every single trade MUST have a stop loss defined BEFORE entry.

### Types of Stop Loss

**1. Technical Stop** (Best for most trades)
- Below support level for longs
- Above resistance level for shorts  
- Below recent swing low (last local bottom)
- Example: Stock at $100, swing low at $97.50 → Stop at $97

**2. Percentage Stop** (Simple and clear)
- Day trades: 2% max
- Swing trades: 5% max
- Example: Entry $100 → Day trade stop $98, Swing stop $95

**3. Time Stop** (For day trades)
- If no movement in 2 hours → Exit
- Prevents capital being tied up in dead positions
- Example: Entered at 11 PM Malaysia, by 1 AM if flat → Out

**4. Trailing Stop** (Lock in profits)
- Once profitable by 2% → Trail stop 1% below current price
- As stock rises, stop rises too (never lower)
- Example: Entry $100, now $105 (+5%) → Stop at $104 (locked in +4%)

### Stop Loss Psychology

**When stop is hit:**
- EXIT IMMEDIATELY - No "wait and see", no "give it more room"
- Accept the small loss to avoid large loss
- Review what went wrong, adjust strategy
- Move on to next trade

**Common mistakes:**
- ❌ Moving stop further away when losing
- ❌ "It will come back" mentality  
- ❌ Not setting stop at all
- ✅ CORRECT: Set stop, honor stop, cut losses fast

## Daily Loss Limits

### Circuit Breakers (Hard Stops)

**Level 1: -2% on day** ⚠️
- Take a break, review trades
- No new trades for 30 minutes
- Ask yourself: Am I trading emotionally?

**Level 2: -3% on day** 🛑
- STOP trading for the rest of the day
- Close any open positions (if safe to do so)
- This prevents catastrophic losses

**Level 3: -5% on day** 🚨
- STOP trading for rest of week
- Something is seriously wrong with strategy or execution
- Review all trades, adjust approach

### Maximum Exposure Rules

- **Max loss per day**: $500 (configurable based on account size)
- **Max trades per day**: 5 (prevents overtrading/revenge trading)
- **Max open positions**: 3 simultaneous (prevents over-diversification)

### Warning System

Bot should warn user:
- "⚠️ Down $300 today. Approaching $500 daily limit."
- "🛑 3 losses in row. Take a break. Review strategy."
- "⚠️ 4 trades today. 1 left before daily limit (5)."

## Position Exit Rules

### When to Exit (Beyond Stop Loss)

**Hit Target Price** 🎯
- Take 50% profit at first target
- Trail stop on remaining 50%
- Example: Target hit at +5% → Sell half, move stop to breakeven on rest

**End of Day** (For day trades only) 🕐
- Close ALL day trade positions before 4:30 AM Malaysia (market close)
- Don't carry overnight risk unless planned swing trade
- Exception: Position up significantly and want to hold → Convert to swing with wider stop

**News Event Coming** 📰
- If earnings or major news after hours → Close position before market close
- Avoid overnight gap risk
- Exception: Playing the earnings (intentional, higher risk)

**Strategy Invalidated** ❌
- If reason for entry no longer valid → Exit immediately
- Example: Bought breakout, it failed → Don't wait for stop, exit now
- Cut losses fast when wrong

**Better Opportunity** 💡
- If capital is limited and see much better setup → Close current, enter new
- Only if current position is near breakeven or slightly green

## Portfolio-Level Risk Management

### Total Exposure
- **Maximum**: 20% of total account in open positions
- Example: $25,000 account → Max $5,000 deployed at once
- This protects from correlated losses (all positions red at once)

### Sector Concentration
- **Maximum**: 30% of positions in single sector
- Example: 3 positions → Max 1 can be tech if it's dominant
- Prevents sector-wide selloff from crushing account

### Correlated Positions
- **Avoid**: Highly correlated stocks together
- Example: Don't hold NVDA + AMD + AVGO all at once (all move together)
- Diversification should actually diversify

### Position Pyramid

When building positions:
- **1st position**: 50% of planned size
- Wait for confirmation (price moves in your direction)
- **2nd position**: 30% more if working
- **3rd position**: 20% more if strong momentum
- This averages in gradually vs. all-in at once

## Risk-Reward Ratio

Minimum acceptable: **1:2 (Risk $1 to make $2)**

Example:
- Entry: $100
- Stop: $98 (Risk $2)
- Target: $104 (Reward $4)
- Ratio: 4:2 = 2:1 ✅ Good

If risk-reward is 1:1 or worse → **DON'T TAKE TRADE**
- Not enough reward for risk taken
- Need to win >50% just to breakeven
- With 2:1 ratio, only need 33% win rate to profit

## Special Situations

### Gap Opening (Pre-market gap)
- If gap >3%: Reduce position size by 50%
- Gaps can fill quickly (return to previous close)
- Wait 30 minutes after open for volatility to settle

### Low Volume / Wide Spreads
- If bid-ask spread >0.5%: Use limit orders
- If volume <500k daily: Reduce position size
- Hard to exit in emergency if illiquid

### High VIX (Market Fear)
- If VIX >25: Reduce ALL position sizes by 30%
- Wider stops (3% instead of 2%)
- Take profits faster (don't be greedy in volatile markets)

## Emergency Protocols

### Account Down Big
If account down >10% from peak:
- STOP all trading for 1 week
- Review every trade
- Identify what went wrong systematically
- Paper trade until regain confidence

### Streak of Losses
3 losses in row:
- Take break for day
- Review each trade: What was mistake?
- Reduce next position size by 50%

5 losses in row:
- STOP trading for week
- Something fundamentally wrong
- Need to recalibrate or learn new skill

### System Failure  
If can't set stop loss (platform issue):
- Don't enter trade
- If already in trade: Set mental stop and monitor actively
- Use alerts as backup

## Mindset Rules

✅ **DO:**
- Treat trading as business (track P&L, review trades)
- Accept losses as cost of doing business
- Follow plan mechanically (remove emotion)
- Take breaks after big wins or losses
- Keep position sizes consistent

❌ **DON'T:**
- Revenge trade after loss
- Over-leverage trying to "make it back"
- Trade without stop loss
- Risk money you need for bills
- Get emotional (fear, greed, FOMO)

Remember: **Preservation of capital > Making profits**

If you preserve capital, you can always trade tomorrow. Blow up account = game over.
