# Current Strategies Explained

Complete breakdown of all 12 trading strategies in the system, how they analyze market data, and when they trigger BUY/SELL/HOLD.

---

## Overview

**Total strategies:** 12 (from `strategies.json`)

**How they work:**
- Each strategy is a **rule-based evaluator** (not AI/ML)
- Takes technical data as input: price, EMA9, EMA21, RSI, volume ratio, support, resistance, trend
- Returns: BUY/SELL/HOLD + confidence (0-100) + reasoning + entry/target/stop prices

**Source code:** [`strategy_agents/base_agent.py`](../strategy_agents/base_agent.py)

---

## Strategy List

1. EMA Crossover
2. Volume Breakout
3. Support/Resistance
4. RSI Divergence
5. Trend Following
6. Mean Reversion
7. Volatility Trading
8. Earnings Play
9. Catalyst Trading
10. Sector Rotation
11. Position Sizing
12. Stop Loss Rules

---

## 1. EMA Crossover

**Logic:** Detects when EMA9 crosses above/below EMA21 (bullish/bearish signal).

**Input data:**
- EMA9, EMA21 (exponential moving averages)
- Current price
- RSI (14-period)
- Volume ratio (current / 20-day average)

**Rules:**

**BUY signal:**
- EMA9 > EMA21 (golden cross)
- Price > EMA9 (confirms uptrend)
- RSI between 40-70 (not overbought/oversold)
- Volume >= 1.5x average (strong if >= 1.5x, weak if < 1.5x)
- **Confidence:** 65-90% (higher if volume strong)
- **Reason:** "EMA9>EMA21, price above EMA9, RSI and volume OK"

**SELL signal:**
- EMA9 < EMA21 (death cross)
- Price < EMA9 (confirms downtrend)
- **Confidence:** 60%
- **Reason:** "EMA bear cross, price below EMA9"

**HOLD signal:**
- EMA9 ≈ EMA21 (no clear crossover)
- OR price between EMA9 and EMA21 (indecision)
- **Confidence:** 30-40%
- **Reason:** "No clear EMA crossover" or "EMA bull but RSI or volume not ideal"

**Entry/Target/Stop (if BUY):**
- Entry: current price
- Stop: support * 0.98 (2% below 20-day support)
- Target: resistance * 1.02 or price * 1.03 (2-3% above)

**Example:**
- NVDA: price $190, EMA9 $189, EMA21 $191 → **HOLD** (EMA9 < EMA21 but price between them, no clear signal)
- AAPL: price $180, EMA9 $178, EMA21 $175, RSI 55, volume 2x → **BUY** confidence 85%

---

## 2. Volume Breakout

**Logic:** Looks for 2x+ volume surge with price breaking resistance (momentum play).

**Input data:**
- Volume ratio (current / 20-day avg)
- Price, resistance (20-day high)
- EMA9, RSI

**Rules:**

**BUY signal:**
- **Strong breakout:** Volume >= 2x AND price > resistance * 0.99 (at or above resistance)
  - **Confidence:** 85%+ (increases with higher volume)
  - **Reason:** "Volume breakout above resistance"
- **Moderate:** Volume >= 1.5x AND price > EMA9 AND RSI > 50
  - **Confidence:** 60%
  - **Reason:** "Volume confirms, trend up"

**HOLD signal:**
- Volume < 2x OR price not at resistance
- **Confidence:** 35%
- **Reason:** "Volume or price not at breakout"

**Entry/Target/Stop (if BUY):**
- Entry: current price
- Stop: support * 0.98
- Target: resistance * 1.02 or price * 1.03

**Example:**
- TSLA: price $250 (resistance $248), volume 3x avg, RSI 60 → **BUY** confidence 95% (strong breakout)
- META: price $300, volume 1x, resistance $305 → **HOLD** (volume weak, not at resistance)

---

## 3. Support/Resistance Bounce

**Logic:** Buys near support (oversold), sells near resistance (overbought).

**Input data:**
- Support (20-day min Low)
- Resistance (20-day max High)
- Current price
- RSI

**Rules:**

**BUY signal:**
- Price within 2% of support (price - support) / support < 0.02
- RSI < 45 (oversold)
- **Confidence:** 70%
- **Reason:** "Near support, RSI oversold"

**SELL signal:**
- Price within 2% of resistance (resistance - price) / resistance < 0.02
- RSI > 55 (elevated)
- **Confidence:** 65%
- **Reason:** "Near resistance, RSI elevated"

**HOLD signal:**
- Price not at key levels
- **Confidence:** 40%
- **Reason:** "Not at key level"

**Entry/Target/Stop (if BUY):**
- Entry: current price (near support)
- Stop: support * 0.98
- Target: resistance * 1.02

**Example:**
- NVDA: price $188, support $188, resistance $193, RSI 40 → **BUY** confidence 70% (at support, oversold)
- AAPL: price $180, support $175, resistance $185, RSI 58 → **HOLD** (mid-range, not at key level)

---

## 4. RSI Divergence

**Logic:** Uses RSI extremes (oversold < 30, overbought > 70) to spot reversal opportunities.

**Input data:**
- RSI (14-period)

**Rules:**

**BUY signal:**
- RSI < 30 (oversold)
- **Confidence:** 65%
- **Reason:** "RSI oversold"

**SELL signal:**
- RSI > 70 (overbought)
- **Confidence:** 65%
- **Reason:** "RSI overbought"

**HOLD signal:**
- RSI between 30-70 (neutral)
- **Confidence:** 40%
- **Reason:** "RSI neutral"

**Entry/Target/Stop (if BUY):**
- Entry: current price
- Stop: support * 0.98
- Target: resistance * 1.02 or price * 1.03

**Example:**
- COIN: RSI 25 → **BUY** confidence 65% (oversold, likely bounce)
- TSLA: RSI 75 → **SELL** confidence 65% (overbought, likely pullback)
- NVDA: RSI 50 → **HOLD** (neutral, no extreme)

---

## 5. Trend Following

**Logic:** Follow the trend - buy in uptrends, sell in downtrends.

**Input data:**
- Trend (bullish/bearish/neutral)
- Price, EMA9

**Rules:**

**BUY signal:**
- Trend = "bullish" (price > EMA9 > EMA21)
- Price > EMA9 (above support)
- **Confidence:** 70%
- **Reason:** "Trend following: bullish, price above EMA9"

**SELL signal:**
- Trend = "bearish" (price < EMA9 < EMA21)
- Price < EMA9 (below resistance)
- **Confidence:** 65%
- **Reason:** "Trend following: bearish"

**HOLD signal:**
- Trend neutral or price not confirming trend
- **Confidence:** 35%
- **Reason:** "Trend not clear"

**Entry/Target/Stop (if BUY):**
- Entry: current price
- Stop: support * 0.98
- Target: resistance * 1.02 or price * 1.03

**Example:**
- AAPL: trend bullish, price $180 > EMA9 $175 → **BUY** confidence 70%
- TSLA: trend bearish, price $240 < EMA9 $245 → **SELL** confidence 65%

---

## 6. Mean Reversion

**Logic:** Buy when oversold (expecting bounce back to mean), sell when overbought (expecting pullback).

**Input data:**
- RSI (14-period)

**Rules:**

**BUY signal:**
- RSI < 35 (oversold, more conservative than RSI Divergence's 30)
- **Confidence:** 65%
- **Reason:** "Mean reversion: RSI oversold"

**SELL signal:**
- RSI > 65 (overbought, more conservative than RSI Divergence's 70)
- **Confidence:** 60%
- **Reason:** "Mean reversion: RSI overbought"

**HOLD signal:**
- RSI between 35-65 (normal range)
- **Confidence:** 40%
- **Reason:** "No extreme"

**Entry/Target/Stop (if BUY):**
- Entry: current price
- Stop: support * 0.98
- Target: resistance * 1.02 or price * 1.03

**Example:**
- COIN: RSI 32 → **BUY** confidence 65% (oversold)
- NVDA: RSI 50 → **HOLD** (mid-range, no extreme)

**Difference from RSI Divergence:**
- Mean Reversion: RSI < 35 / > 65 (more conservative, expects bounce/pullback to average)
- RSI Divergence: RSI < 30 / > 70 (more aggressive, waits for deeper extremes)

---

## 7-12. Other Strategies (Volatility, Earnings, Catalyst, Sector, Sizing, Stop Loss)

These strategies are **in strategies.json** but **not yet implemented** in the rule logic (they fall through to the default logic).

**Default logic (if strategy name doesn't match any of the above):**
- If trend = "bullish" AND RSI 40-70 AND volume >= 1x → **BUY** confidence 55% ("Bullish trend, RSI and volume OK")
- If trend = "bearish" → **SELL** confidence 50% ("Bearish trend")
- Else → **HOLD** confidence 40% ("No clear signal")

**To implement these strategies,** you would add new `if` blocks in `_evaluate()` in [`strategy_agents/base_agent.py`](../strategy_agents/base_agent.py):

**Example (Volatility Trading):**
```python
if 'volatility' in name:
    # Use Bollinger Bands or ATR (Average True Range)
    # BUY when price touches lower Bollinger Band
    # SELL when price touches upper Bollinger Band
    pass
```

**Example (Earnings Play):**
```python
if 'earnings' in name:
    # Check if earnings date is within 1 week (requires earnings calendar)
    # BUY if positive earnings surprise expected
    # SELL/HOLD before earnings if high IV (implied volatility)
    pass
```

---

## Summary Table

| Strategy | Triggers BUY when | Triggers SELL when | Key data |
|----------|-------------------|--------------------|---------| 
| **EMA Crossover** | EMA9 > EMA21, price > EMA9, RSI 40-70, volume 1.5x+ | EMA9 < EMA21, price < EMA9 | EMA9, EMA21, RSI, volume |
| **Volume Breakout** | Volume 2x+, price > resistance | - | Volume ratio, resistance |
| **Support/Resistance** | Price within 2% of support, RSI < 45 | Price within 2% of resistance, RSI > 55 | Support, resistance, RSI |
| **RSI Divergence** | RSI < 30 | RSI > 70 | RSI |
| **Trend Following** | Trend bullish, price > EMA9 | Trend bearish, price < EMA9 | Trend, EMA9 |
| **Mean Reversion** | RSI < 35 | RSI > 65 | RSI |
| **Others (7-12)** | (not implemented, use default logic) | | |

---

## How strategies set entry/target/stop

All strategies use the same logic for entry/target/stop (from `base_agent.py` lines 58-66):

**If BUY:**
- **Entry:** current price
- **Stop loss:** support * 0.98 (2% below 20-day support)
- **Target:** resistance * 1.02 OR price * 1.03 (whichever is higher)

**If SELL:**
- **Entry:** current price
- **Stop loss:** resistance * 1.02 (2% above 20-day resistance)
- **Target:** support * 0.98 OR price * 0.97 (whichever is lower)

**If HOLD:**
- Entry/target/stop = None (wait for signal)

---

## How consensus works (current flow)

When you ask "NVDA 要買嗎?", the bot:

1. Fetches technical data (price, EMA9, EMA21, RSI, volume, support, resistance, trend)
2. Runs **all 12 strategies** (each returns BUY/SELL/HOLD + confidence)
3. **Aggregates** (from [`strategy_orchestrator.py`](../strategy_orchestrator.py)):
   - Count: BUY signals, SELL signals, HOLD signals
   - If BUY count > SELL count AND BUY >= total/3 → consensus = **BUY**
   - If SELL count > BUY count AND SELL >= total/3 → consensus = **SELL**
   - Else → consensus = **HOLD**
   - Average confidence (weighted by action)
4. Returns: "0/12 BUY, 0/12 SELL, 12/12 HOLD" → consensus **HOLD** confidence 50%

**Example (NVDA):**
- EMA Crossover: HOLD (EMA9 ≈ EMA21)
- Volume Breakout: HOLD (volume 1x)
- Support/Resistance: HOLD (price mid-range)
- RSI Divergence: HOLD (RSI 50)
- Trend Following: HOLD (trend neutral)
- Mean Reversion: HOLD (RSI 50)
- ... (all 12 say HOLD)
- **Result:** 0 BUY, 0 SELL, 12 HOLD → consensus **HOLD**

---

## What the new flow will change

**Current (consensus):** All 12 strategies → one aggregate answer → can't see individual strategy differences.

**New (per-strategy selection):**
1. You pick 1-3 strategies (e.g. EMA, RSI, Volume)
2. Bot runs each **individually** and shows:
   - EMA Crossover: HOLD, no crossover, 60d: 18 BUY days (historical)
   - RSI: HOLD, buy when RSI < 35, 60d: 8 BUY days
   - Volume: HOLD, wait for 2x volume + breakout $193, 60d: 5 BUY days
3. You **compare** and decide which strategy to follow

This lets you see which strategy is more aggressive (EMA gave 18 BUY signals historically) vs conservative (Volume only 5) and which has the clearest trigger for your style.

---

## Next: Which strategies to keep/remove/add?

Now that you see how they work:

**Questions for you:**

1. **Which strategies do you want to keep?** (e.g. EMA, RSI, Volume, S/R are classic and implemented; others are placeholders)
2. **Which to remove?** (e.g. Position Sizing, Stop Loss Rules are not really strategies, more like risk management)
3. **Which to add?** (e.g. MACD, Bollinger Bands, Fibonacci retracement, etc.)
4. **Do you want to implement the 6 unimplemented strategies** (Volatility, Earnings, Catalyst, Sector, Sizing, Stop Loss)? Or remove them?

Let me know and I can adjust the strategy list before building the new flow.
