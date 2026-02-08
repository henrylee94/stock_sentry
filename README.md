# 📚 GEEWONI Trading Skills Library

完整的交易策略技能库 - 12个专业级交易策略

## 📁 文件结构

```
skills/
├── technical_analysis/      # 技术分析策略
│   ├── ema_crossover.json          # EMA 交叉 (初级)
│   ├── rsi_divergence.json         # RSI 背离 (中级)
│   ├── volume_breakout.json        # 成交量突破 (初级)
│   └── support_resistance.json     # 支撑阻力 (中级)
│
├── fundamental/              # 基本面策略
│   ├── earnings_play.json          # 财报交易 (高级)
│   ├── sector_rotation.json        # 板块轮动 (高级)
│   └── catalyst_trading.json       # 催化剂交易 (中级)
│
├── risk_management/          # 风险管理
│   ├── position_sizing.json        # 仓位管理 (初级) ⭐
│   ├── stop_loss_rules.json        # 止损规则 (初级) ⭐
│   └── portfolio_balance.json      # 组合平衡 (中级)
│
└── market_conditions/        # 市场环境策略
    ├── trend_following.json        # 趋势跟随 (初级)
    ├── mean_reversion.json         # 均值回归 (中级)
    └── volatility_trading.json     # 波动率交易 (高级)
```

## 🎯 技能分类

### 技术分析 (4个策略)

1. **EMA Crossover** ⭐ 初级
   - 使用 EMA 9/21 交叉判断趋势
   - 适合趋势市场
   - 胜率目标: 55-60%

2. **RSI Divergence** 中级
   - 价格与 RSI 背离寻找反转
   - 适合震荡市场
   - 胜率目标: 60-65%

3. **Volume Breakout** ⭐ 初级
   - 放量突破关键价位
   - 适合有催化剂时
   - 胜率目标: 50-55%

4. **Support Resistance** 中级
   - 在关键位反弹/反转
   - 适合区间市场
   - 胜率目标: 60-65%

### 基本面 (3个策略)

5. **Earnings Play** 高级
   - 利用财报波动
   - 高风险高回报
   - 需要深入研究

6. **Sector Rotation** 高级
   - 根据经济周期轮动
   - 中长期策略
   - 需要宏观知识

7. **Catalyst Trading** 中级
   - 事件驱动交易
   - 需要新闻嗅觉
   - 快进快出

### 风险管理 (3个策略) ⭐ 必学

8. **Position Sizing** ⭐⭐⭐ 初级
   - 科学计算仓位大小
   - 风险百分比法
   - 凯利公式

9. **Stop Loss Rules** ⭐⭐⭐ 初级
   - 永远设置止损
   - 多种止损方法
   - 保护资本

10. **Portfolio Balance** 中级
    - 分散投资
    - 组合优化
    - 降低系统风险

### 市场环境 (3个策略)

11. **Trend Following** ⭐ 初级
    - 顺势而为
    - 让利润奔跑
    - 趋势市最佳

12. **Mean Reversion** 中级
    - 价格回归均值
    - 震荡市最佳
    - 避免强趋势

13. **Volatility Trading** 高级
    - 波动率交易
    - 根据 VIX 调整
    - 需要期权知识

## 📊 每个技能包含什么

每个 JSON 文件都包含:

```json
{
  "name": "策略名称",
  "type": "类型",
  "category": "类别",
  "description": "描述",
  "difficulty": "难度",
  "timeframe": ["时间周期"],
  "best_for": ["最佳使用场景"],

  "rules": {
    "entry_conditions": ["入场条件"],
    "exit_conditions": ["出场条件"],
    "stop_loss": "止损规则",
    "take_profit": "止盈规则",
    "position_size": "仓位大小",
    "max_positions": "最大持仓数"
  },

  "parameters": {
    // 可调参数
  },

  "performance": {
    // 实战表现追踪
    "total_trades": 0,
    "wins": 0,
    "losses": 0,
    "win_rate": 0.0,
    "profit_factor": 0.0,
    "total_pnl": 0.0
  },

  "learned_optimizations": {
    // AI 学习到的最佳参数
  },

  "notes": "使用注意事项"
}
```

## 🎓 学习路径建议

### 第1周: 基础 (必学 ⭐⭐⭐)

1. Position Sizing
2. Stop Loss Rules
3. Trend Following

### 第2-3周: 技术分析

4. EMA Crossover
5. Volume Breakout
6. Support Resistance

### 第4-5周: 进阶

7. Mean Reversion
8. RSI Divergence
9. Portfolio Balance

### 第6周+: 高级

10. Catalyst Trading
11. Earnings Play
12. Sector Rotation
13. Volatility Trading

## 🚀 如何使用

### 1. 选择适合市场的策略

```python
# 趋势市场
trend_following.json
ema_crossover.json
volume_breakout.json

# 震荡市场
mean_reversion.json
support_resistance.json
rsi_divergence.json

# 高波动
volatility_trading.json
gap_trading (in volatility_trading)

# 催化剂事件
earnings_play.json
catalyst_trading.json
```

### 2. 组合策略使用

**推荐组合:**

- EMA Crossover + Position Sizing + Stop Loss
- Support Resistance + Mean Reversion + Portfolio Balance
- Catalyst Trading + Volatility Trading + Tight Stops

### 3. 根据账户大小选择

**小账户 (<$10k):**

- 专注 2-3 个策略
- 使用技术分析策略
- 避免复杂的期权策略

**中账户 ($10k-$50k):**

- 5-6 个策略
- 加入基本面分析
- 开始组合管理

**大账户 (>$50k):**

- 全部 12 个策略
- 多策略组合
- 包括期权和高级策略

## 📈 策略表现追踪

AI 会自动追踪每个策略的表现:

```json
{
  "performance": {
    "total_trades": 45,
    "wins": 28,
    "losses": 17,
    "win_rate": 62.2,
    "avg_profit_pct": 3.5,
    "avg_loss_pct": 1.8,
    "profit_factor": 2.14,
    "sharpe_ratio": 1.8,
    "total_pnl": 2450.0
  }
}
```

## 🧠 AI 学习优化

AI 会学习并优化每个策略:

```json
{
  "learned_optimizations": {
    "best_rsi_range": [45, 58],
    "best_volume_ratio": 2.1,
    "optimal_timeframe": "15min",
    "best_market_conditions": "trending_up",
    "success_patterns": [...]
  }
}
```

## ⚠️ 重要提示

1. **风险管理优先** - 先学 Position Sizing 和 Stop Loss
2. **不要全用** - 选择 2-3 个专精，不要贪多
3. **适应市场** - 趋势市用趋势策略，震荡市用回归策略
4. **记录一切** - AI 需要数据才能学习优化
5. **耐心测试** - 每个策略至少 20-30 笔交易才能评估

## 🔄 策略进化

随着交易数据积累:

1. AI 自动优化参数
2. 淘汰表现差的策略
3. 发现新的成功模式
4. 组合最佳策略

## 📚 进一步学习

每个策略 JSON 文件里都有:

- 详细规则说明
- 实战例子
- 常见错误
- 最佳实践

**建议:** 每次只专注学习一个策略，实战测试 2-3 周后再学下一个。

---

**Created:** 2025-02-07  
**Version:** 1.0  
**Total Skills:** 12

## py -3.12 telegram_bot.py
