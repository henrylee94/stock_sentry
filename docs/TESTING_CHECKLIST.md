# Testing Checklist - New Strategy Selection System

## ✅ Code Changes Verified

All new features have been implemented successfully:

### Files Modified
- ✅ `core/data_manager.py` - Added 5 new indicators (BB, Donchian, ATR, 52w, EMA5)
- ✅ `backtester.py` - Added same indicators + `run_backtest_single_strategy()`
- ✅ `strategy_agents/base_agent.py` - Added 3 new strategies (BB Mean Reversion, Donchian, Sigma)
- ✅ `strategy_orchestrator.py` - Added `get_signal_by_strategy()`, `list_all_strategies()`
- ✅ `telegram_bot.py` - Added strategy buttons, callbacks, parameter tuning
- ✅ `strategies.json` - Updated to 9 strategies
- ✅ `strategy_params.json` - Created for parameter tuning

### No Linter Errors
All files passed linting ✅

---

## 🧪 Manual Testing Steps

### Test 1: Start the Bot
```bash
cd /Users/user/Documents/stock_sentry
python telegram_bot.py
```

**Expected:** Bot starts without errors

---

### Test 2: Basic Stock Query (NEW FLOW)

**In Telegram, send:**
```
AAPL 要買嗎?
```

**Expected result:**
```
📊 AAPL $180.50 (+1.2%)
RSI 55 | 弱势看涨

選擇策略 (pick 1-3 to see results):

[EMA Crossover]               [Volume Breakout]
[Support/Resistance]          [RSI Divergence]
[Trend Following]             [Mean Reversion]
[Mean Reversion (Bollinger+RSI)] [Momentum Breakout (Donchian)]
[Sigma Series]

[🔍 比較所有策略]
```

✅ **PASS if:** All 9 strategy buttons appear
❌ **FAIL if:** No buttons or error message

---

### Test 3: Single Strategy Selection

**Click:** `Sigma Series` button

**Expected result:**
```
📊 AAPL $180.50 | Strategy: Sigma Series

🟢 建議: BUY (or HOLD or SELL)
💰 入場: $180.50
🎯 目標: $185.00
🛑 止損: $178.00

💡 Why: Sigma: EMA5>9>21, RSI optimal, volume strong, bullish

📈 60d Backtest (Sigma Series only):
   BUY 15d | SELL 2d | HOLD 43d (total 60d)

🎯 Confidence: 88%
```

✅ **PASS if:** Shows per-strategy result with 建議/入場/目標/止損/backtest
❌ **FAIL if:** Error or empty response

---

### Test 4: Try Different Strategies

**Click each strategy button:**
- `EMA Crossover`
- `Mean Reversion (Bollinger+RSI)`
- `Momentum Breakout (Donchian)`

**Expected:** Each shows different analysis based on its rules

✅ **PASS if:** Different strategies give different results/reasons
❌ **FAIL if:** All strategies give same result

---

### Test 5: Compare All Strategies

**Click:** `🔍 比較所有策略` button

**Expected result:**
```
🔍 Running all strategies... (this may take a few seconds)

📊 AAPL $180.50 - All strategies comparison

EMA Crossover
  建議: HOLD | Entry: wait | 60d BUY: 18/60d
  Target: N/A | Stop: N/A | Conf: 30%
  Why: No clear EMA crossover

Volume Breakout
  建議: HOLD | Entry: wait | 60d BUY: 5/60d
  ...

(all 9 strategies shown)
```

✅ **PASS if:** All 9 strategies shown with individual results
❌ **FAIL if:** Error or incomplete list

---

### Test 6: Parameter Tuning

**In Telegram, send:**
```
/tune
```

**Expected result:**
```
⚙️ 調整策略參數

選擇要調整的策略:
[EMA Crossover]               [Volume Breakout]
[Support/Resistance]          [RSI Divergence]
...
```

**Click:** `Sigma Series`

**Expected result:**
```
⚙️ Sigma Series

Current Parameters:

• rsi_min: 40
  [rsi_min -5] [rsi_min +5]

• rsi_max: 65
  [rsi_max -5] [rsi_max +5]

• volume_ratio: 1.5
  [volume_ratio -5] [volume_ratio +5]

[« Back to strategies]
```

**Click:** `rsi_min +5`

**Expected:** Value changes from 40 to 45 and display refreshes

✅ **PASS if:** Parameters adjust and save correctly
❌ **FAIL if:** Buttons don't work or values don't change

---

### Test 7: Verify New Indicators

**Test with a volatile stock (e.g., NVDA, TSLA):**
```
TSLA 要買嗎?
```

**Then click:** `Mean Reversion (Bollinger+RSI)`

**Expected:** Should reference Bollinger Bands in the result
```
💡 Why: Price < lower BB AND RSI oversold, mean reversion setup
```

**Click:** `Momentum Breakout (Donchian)`

**Expected:** Should reference Donchian Channel
```
💡 Why: Breakout above Donchian + new 52w high, strong momentum
```

✅ **PASS if:** New strategies use their specific indicators
❌ **FAIL if:** Generic reasons or errors

---

### Test 8: Backtest Per Strategy

**After clicking any strategy**, verify the backtest line shows:
```
📈 60d Backtest (Strategy Name only):
   BUY 15d | SELL 2d | HOLD 43d (total 60d)
```

✅ **PASS if:** Backtest shows strategy-specific counts (different for each strategy)
❌ **FAIL if:** All strategies show same backtest counts

---

### Test 9: HOLD Triggers

**Find a stock with HOLD recommendation**, verify it shows concrete trigger:
```
⚪ 建議: HOLD
💰 入場: Wait for trigger
🔔 Trigger: Wait for EMA5>9>21 alignment + RSI 40-65
```

✅ **PASS if:** HOLD recommendations have specific triggers
❌ **FAIL if:** No trigger or generic "wait"

---

### Test 10: Multiple Symbols

**Test with:**
```
AAPL NVDA TSLA 要買嗎?
```

**Expected:** Should show strategy buttons for first symbol (AAPL)

✅ **PASS if:** Works with first symbol
❌ **FAIL if:** Error with multiple symbols

---

## 🐛 Common Issues & Fixes

### Issue 1: "Strategy orchestrator not available"
**Fix:** Check that `strategy_orchestrator.py` loaded successfully. Run:
```bash
python3 -c "from strategy_orchestrator import StrategyOrchestrator; print('OK')"
```

### Issue 2: Strategy buttons don't appear
**Fix:** Check `telegram_bot.py` line 550-584 (strategy button code). Ensure `strategy_orchestrator` is not None.

### Issue 3: Backtest returns 0 days for all strategies
**Fix:** Yahoo Finance may be slow. Wait 30s and try again. Check internet connection.

### Issue 4: New indicators show 0
**Fix:** Stock may not have enough historical data (need 40+ days for Donchian). Try AAPL, MSFT, NVDA instead.

### Issue 5: "/tune command not found"
**Fix:** Check `telegram_bot.py` around line 1691 - ensure `/tune` command is registered in handlers list.

---

## 📊 Success Criteria

✅ **System is working if:**
- Strategy buttons appear after stock query
- Each strategy shows different analysis
- Backtest shows per-strategy counts (not consensus)
- `/tune` command allows parameter adjustment
- HOLD recommendations have concrete triggers
- Compare all shows all 9 strategies side-by-side

---

## 🎯 What to Test First

**Priority order:**
1. ✅ Test 1 (bot starts)
2. ✅ Test 2 (strategy buttons appear)
3. ✅ Test 3 (single strategy works)
4. ✅ Test 5 (compare all works)
5. ✅ Test 6 (parameter tuning works)
6. ⚠️ Tests 7-9 (verify details)

---

## 📝 Known Limitations

- **No order placement yet** - IB integration pending (see `PENDING_IB_INTEGRATION.md`)
- **Backtest is count-only** - doesn't calculate P&L, just signal distribution
- **First symbol only** - if you ask about multiple symbols, only first gets strategy UI
- **60-day backtest only** - hardcoded to 60 days (can change in code if needed)

---

## 🚀 Ready to Test!

Start the bot and go through Tests 1-6 above. Report any failures with:
- Which test failed
- Error message (if any)
- What you expected vs what happened

Good luck! 🎉
