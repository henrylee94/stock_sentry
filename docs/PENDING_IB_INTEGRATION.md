# PENDING: Interactive Brokers Integration

**Status:** Under consideration - deployment strategy TBD

---

## What IB Would Provide

### Real-time Data
- ✅ Live quotes (price, bid/ask, volume) - faster than Finnhub
- ✅ Real-time news from IB news providers
- ✅ Options data & Greeks (if needed)

### Portfolio Management
- ✅ Current positions & quantities
- ✅ Unrealized P&L per position
- ✅ Account balance & buying power

### Order Execution
- ✅ Place market/limit/stop orders
- ✅ Track order status (filled, pending, cancelled)
- ✅ Real-time execution confirmation

### Historical Data
- ✅ Accurate historical bars (more reliable than Yahoo)
- ✅ Multiple timeframes (1min, 5min, 1hour, 1day)
- ✅ Better for backtesting

---

## Deployment Options (To Decide)

### Option A: Bot on Zeabur + IB Gateway on VPS (RECOMMENDED)
- **Cost:** $12/month (VPS only, Zeabur free tier)
- **Setup:** Medium complexity
- **Pros:** Stable IB connection, easy bot deployment
- **Cons:** Need to manage VPS

### Option B: Bot on Zeabur + IB Gateway on Local Mac
- **Cost:** $0 (use existing Mac)
- **Setup:** Easy
- **Pros:** No VPS cost, easy to monitor
- **Cons:** Mac must run 24/7, security risk

### Option C: Everything on VPS
- **Cost:** $12/month (VPS)
- **Setup:** Medium complexity
- **Pros:** Lowest latency, most secure
- **Cons:** No auto-deploy like Zeabur

### Option D: IBKR Web API (No IB Gateway)
- **Cost:** $0 (no extra infrastructure)
- **Setup:** Easy
- **Pros:** Works on any platform (Zeabur, etc.)
- **Cons:** More limited features, higher latency

---

## Technical Requirements

### Dependencies
```
ib_insync>=0.9.86
```

### Environment Variables
```env
IB_HOST=127.0.0.1  # or VPS IP or home IP
IB_PORT=7496       # 7496 for live, 7497 for paper
IB_READONLY=true   # true = quotes only, false = allow orders
```

### Files to Create
- `core/ib_manager.py` - Connection manager
- Update `core/data_manager.py` - Add IB as priority #1
- Update `backtester.py` - Use IB historical data
- Update `telegram_bot.py` - Add /portfolio command, IB news

---

## Priority Level

**Current:** Use Finnhub (priority 1) + Yahoo (priority 2) - works fine

**With IB:** IB (priority 1) → Finnhub (priority 2) → Yahoo (priority 3)

**When to implement:**
- [ ] After deciding deployment strategy (VPS vs local vs Web API)
- [ ] After testing current strategy selection system
- [ ] When ready to manage portfolio via bot

---

## Next Steps (When Ready)

1. **Decide deployment option** (A/B/C/D above)
2. **Set up IB Gateway** (if using Option A/B/C)
   - Download IB Gateway
   - Configure API access
   - Test connection
3. **Implement integration** (1-2 days)
4. **Test on paper account first** (weeks)
5. **Enable live trading** (if desired)

---

## Alternative: Keep Current Setup

**Current setup works well:**
- Finnhub provides fast real-time quotes
- Yahoo provides reliable technical indicators
- No need for 24/7 infrastructure

**Consider IB only if:**
- You want portfolio tracking in bot
- You want to place orders via bot
- Finnhub rate limits are a problem
- You need options data

---

## Reference

Full implementation plan: `/Users/user/.cursor/plans/ib_integration_plan_5a7e6392.plan.md`
