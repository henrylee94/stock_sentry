# New Strategies Summary

Based on your requirements, we're adding 3 sophisticated strategies with professional technical indicators.

---

## New Technical Indicators (to be calculated)

### 1. Bollinger Bands (20-period SMA ± 2 std dev)
- **Upper Band:** SMA(20) + 2 × StdDev(20)
- **Middle Band:** SMA(20)
- **Lower Band:** SMA(20) - 2 × StdDev(20)
- **Use:** Identify overbought/oversold conditions and mean reversion opportunities

### 2. Donchian Channels (high/low over N periods)
- **Upper Channel (20):** 20-period high
- **Lower Channel (20):** 20-period low
- **Upper Channel (40):** 40-period high
- **Lower Channel (40):** 40-period low
- **Use:** Breakout detection and momentum confirmation

### 3. ATR (Average True Range, 14-period)
- **Calculation:** Rolling 14-period average of True Range
- **True Range:** max(High-Low, |High-PrevClose|, |Low-PrevClose|)
- **Use:** Trailing stop loss (e.g., stop = entry - 2×ATR)

### 4. 52-week High/Low
- **High:** 252-trading-day (1 year) maximum
- **Low:** 252-trading-day minimum
- **Use:** Identify breakouts to new highs (strong momentum signal)

### 5. EMA5 (5-period exponential moving average)
- **Use:** Fast-moving trend indicator for Sigma Series strategy

---

## New Strategies

### 1. Mean Reversion (Bollinger Bands + RSI)

**Category:** Reversal / Contrarian

**Entry rules:**
- **BUY:** Price < Lower Bollinger Band AND RSI(14) < 30
  - Confidence: 60-85% (higher when RSI very low)
  - Reasoning: "Price < lower BB AND RSI oversold, mean reversion setup"

**Exit rules:**
- **SELL:** Price > Middle Bollinger Band OR RSI > 70
  - If both: Confidence 75% "Price > middle BB AND RSI overbought, taking profit"
  - If price only: Confidence 60% "Price > middle BB, reverting to mean"
  - If RSI only: Confidence 55% "RSI overbought, expecting pullback"

**HOLD:** Price within Bollinger Bands, no extreme

**Why this works:**
- Combines price deviation (Bollinger Bands) with momentum (RSI) for high-probability reversions
- Lower BB + RSI < 30 = double confirmation of oversold condition
- Middle BB exit captures mean reversion move without waiting for upper BB

**Best for:** Range-bound markets, stocks with established support/resistance

---

### 2. Momentum Breakout (Donchian Channels)

**Category:** Trend / Momentum

**Entry rules:**
- **BUY:** Close > Upper Donchian(20) AND near 52-week high (within 2%)
  - Confidence: 90% "Breakout above Donchian + new 52w high, strong momentum"
- **BUY:** Close > Upper Donchian(20) (without 52w high)
  - Confidence: 70% "Breakout above Donchian(20), momentum confirmed"
- **BUY:** Close > Upper Donchian(40) AND near 52-week high
  - Confidence: 85% "Breakout above Donchian(40) + 52w high, very strong"
- **BUY:** Close > Upper Donchian(40) (without 52w high)
  - Confidence: 65% "Breakout above Donchian(40)"

**Exit rules:**
- **SELL:** Close < Lower Donchian(20)
  - Confidence: 65% "Below Donchian(20) lower, momentum fading"
- **Alternative exit (for implementation):** Trailing stop at entry - 2×ATR

**HOLD:** No Donchian breakout yet

**Why this works:**
- Donchian breakout = new 20/40-period high = strong momentum
- 52-week high confirmation = institutional breakout level
- Lower Donchian exit catches momentum reversals early
- ATR trailing stop locks in profits dynamically

**Best for:** Trending markets, breakout stocks, momentum plays

---

### 3. Sigma Series (StockHero-inspired)

**Category:** Bull-optimized adaptive momentum

**Entry rules:**
- **BUY (optimal):** EMA5 > EMA9 > EMA21 + Trend bullish + RSI 40-65 + Volume ≥ 1.5x
  - Confidence: 70-95% (increases with volume and RSI near 50)
  - Reasoning: "Sigma: EMA5>9>21, RSI optimal, volume strong, bullish"
- **BUY (good):** EMA5 > EMA9 > EMA21 + RSI 40-65
  - Confidence: 75% "Sigma: EMA alignment, RSI optimal, volume moderate"
- **BUY (moderate):** EMA5 > EMA9 > EMA21 + Volume ≥ 1.5x
  - Confidence: 70% "Sigma: EMA alignment, volume strong"

**HOLD conditions:**
- EMA5 > EMA9 > EMA21 but RSI/volume not ideal: Confidence 55%
- EMA5 > EMA9 > EMA21 but trend not confirmed: Confidence 50%
- No EMA alignment: Confidence 40%

**Why this works:**
- **Triple EMA alignment** (5>9>21) = strong uptrend with accelerating momentum
- **RSI 40-65** = not overbought, still has room to run
- **Volume ≥ 1.5x** = institutional participation
- **Trend filter** = only trades with the major trend direction
- **Bull-optimized:** Only looks for BUY setups in uptrends (high win rate by avoiding chop)

**Mimics StockHero's approach:**
- Adaptive momentum (EMA5 adapts faster than EMA9/21)
- High win rate focus (only high-confidence setups)
- Minimal drawdown (no trades in downtrends)
- EMA/RSI hybrid (combines trend + momentum)

**Best for:** Bull markets, trending stocks, swing trades

---

## Updated Strategy List (9 total)

### Keep (6 existing):
1. **EMA Crossover** (9/21) - Golden/death cross
2. **Volume Breakout** - 2x volume + resistance break
3. **Support/Resistance** - 20-day S/R + RSI confirmation
4. **RSI Divergence** - Oversold < 30, overbought > 70
5. **Trend Following** - Follow bullish/bearish trend
6. **Mean Reversion (Simple)** - RSI < 35 / > 65

### Add (3 new):
7. **Mean Reversion (Bollinger+RSI)** - BB + RSI combo
8. **Momentum Breakout (Donchian)** - Donchian + 52w high
9. **Sigma Series** - EMA5/9/21 + RSI + volume bull-optimized

### Remove (6 placeholders):
- ❌ Volatility Trading
- ❌ Earnings Play
- ❌ Catalyst Trading
- ❌ Sector Rotation
- ❌ Position Sizing
- ❌ Stop Loss Rules

---

## Expected Button Layout (Telegram)

When you ask "NVDA 要買嗎?", bot shows:

```
📊 NVDA $190.05 (+0.80%)
RSI 50 | Trend Neutral

選擇策略 (pick 1-3):

[EMA Crossover]      [Volume Breakout]
[Support/Resistance] [RSI Divergence]
[Trend Following]    [Mean Reversion]
[BB Mean Reversion]  [Donchian Breakout]
[Sigma Series]

[🔍 比較所有策略]
```

You click e.g. "Sigma Series" → bot shows:

```
📊 NVDA $190.05 | Strategy: Sigma Series

⚪ 建議: HOLD
💰 入場: Wait for trigger
🔔 Trigger: Wait for EMA5>9>21 alignment or price > $193.26

💡 Why: Sigma: EMA5 not above EMA9 yet, no alignment

📈 60d Backtest (Sigma Series only):
   BUY 15d | SELL 2d | HOLD 43d (total 60d)

🎯 Confidence: 40%
```

Then you can click "BB Mean Reversion" or "Donchian Breakout" to compare.

---

## Implementation Order

1. **Add indicators** to `core/data_manager.py` and `backtester.py` (Bollinger, Donchian, ATR, 52w high, EMA5)
2. **Add strategy logic** to `strategy_agents/base_agent.py` (3 new strategies)
3. **Update `strategies.json`** (9 strategies, remove 6 placeholders)
4. **Add orchestrator methods** (`get_signal_by_strategy`, `list_all_strategies`)
5. **Add per-strategy backtest** function
6. **Add Telegram UI** (strategy buttons, callback handler, result formatter)
7. **Format improvements** (timestamp, triggers, 建議/入場/目標/止損)

---

## Ready to implement?

Review the strategies and let me know:
- ✅ Are these 3 new strategies what you want?
- ✅ Any modifications to the entry/exit rules?
- ✅ Button layout preference (all 9 buttons or categorize)?
- ✅ Should we proceed with implementation?
