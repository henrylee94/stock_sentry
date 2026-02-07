# 🚀 GeewoniStockSentry v6.0 升级指南

## ✨ 新功能总览

### 🎯 核心升级：
1. **📊 Dashboard** - 周盈亏追踪 + AI Top 3 推荐
2. **🤖 AI Strategy Center** - 实时分析 + 策略实验室 + 性能对比
3. **📈 Live Stocks** - 实时价格监控
4. **📋 Trade Journal** - 交易记录系统
5. **⚙️ Control Center** - 完整配置管理（5个子页面）
6. **📊 Analytics** - 数据分析和图表

### 🎨 设计升级：
- ✅ 现代科技风格（渐变 + 动画）
- ✅ 手机优先设计（响应式）
- ✅ 视觉友好界面
- ✅ 一键操作按钮

---

## 📦 安装步骤

### 1. 备份旧版本
```bash
cd C:\Users\User\OneDrive\Desktop\Geewoni-Sentry
copy tradesniper.py tradesniper_v5_backup.py
```

### 2. 替换文件
下载 `tradesniper_v6_complete.py` 并重命名为 `tradesniper.py`

### 3. 更新环境变量
在 `.env` 文件中添加（如果还没有）:
```
TELEGRAM_CHAT_ID=923799250
```

### 4. 运行
```bash
streamlit run tradesniper.py
```

---

## 🎯 主要功能使用指南

### 📊 Dashboard 页面

**你的早上 9:00 AM 流程：**
1. 打开 Dashboard
2. 查看 Weekly P&L 进度
3. 查看 AI Top 3 Picks
4. 点击 "🔄 Refresh" 获取最新推荐
5. 点击 "📱 Send to Telegram" 发送到手机

**盘中使用（9:30 PM - 4:00 AM）：**
- 查看 Current Positions
- 快速 WIN/LOSS 记录
- 实时监控持仓盈亏

---

### 🤖 AI Strategy Center

#### Tab 1: Real-time Analysis
**步骤：**
1. 选择股票（NVDA, PLTR等）
2. 点击 "🔍 Analyze Now"
3. 查看 AI 推荐：
   - 入场价区间
   - 目标价
   - 止损价
   - 推荐策略
   - 信心度
4. 点击 "📱 Send to Telegram" 或 "✅ Record Entry"

#### Tab 2: Strategy Lab
**每周流程：**
1. **周一早上创建本周策略：**
   - 选择 Base Strategy（例如：Volume Breakout）
   - 调整参数（RSI, EMA, Volume等）
   - 设置 Daily Target（$200）
   - 点击 "💾 Save"

2. **周二-周五监控：**
   - 查看 Progress（信号次数、交易次数、胜率）
   - 根据实际情况调整

3. **周日复盘：**
   - 点击 "📊 Generate Report"
   - 查看本周表现
   - 决定下周策略

#### Tab 3: Performance
- 查看所有 12 个策略的表现
- 按 P&L 排序
- 启用/禁用策略

---

### 📈 Live Stocks

**快速查股票：**
1. 在顶部输入框输入 symbol（例如：TSLA）
2. 立即显示价格和涨跌

**监控 Watchlist：**
- 自动显示所有 watchlist 股票
- 4列网格布局
- 手机端自动适应

---

### 📋 Trade Journal

**记录买入：**
1. 选择 "Buy"
2. 选择 Symbol
3. 输入 Price 和 Quantity
4. 选择 Strategy
5. 点击 "💾 Save Trade"

**记录卖出：**
1. 选择 "Sell"
2. 其他步骤相同
3. 自动计算盈亏

**查看历史：**
- 右侧显示最近 5 笔交易
- 完整历史在 `trades_history.json`

---

### ⚙️ Control Center

#### Tab 1: Basic Settings
- Watchlist（监控的股票列表）
- Priority（优先提醒的股票）
- Alert %（涨跌多少发提醒）
- Win/Loss 金额
- Weekly Goal

#### Tab 2: Push Times ⭐ 新功能
**设置推送时间（马来西亚时间）：**
- Morning: 09:00 （早安新闻）
- Premarket: 21:00 （开盘前计划）
- Close: 04:00 （收盘总结）

#### Tab 3: Monitor Rules ⭐ 新功能
**监控触发条件：**
- Price Change %: 涨跌超过多少
- Volume Mult: 成交量超过几倍
- RSI Low/High: RSI 阈值

#### Tab 4: Strategies ⭐ 新功能
**管理策略：**
- 勾选启用的策略
- 只有启用的策略会被 AI 推荐

#### Tab 5: Risk Management ⭐ 新功能
**风险控制：**
- Max Position %: 单笔最大仓位
- Stop Loss %: 默认止损
- Max Daily Loss: 单日最大亏损

**💾 修改后记得点击 "SAVE ALL SETTINGS"！**

---

### 📊 Analytics

**查看数据：**
- Weekly Progress 进度条
- Strategy Win Rates 柱状图
- 可视化你的表现

---

## 📱 手机端使用

### 访问方式：
1. **局域网：** http://192.168.50.55:8501
2. **Zeabur部署：** https://stock-sentry.zeabur.app

### 手机优化特性：
- ✅ 自动适应屏幕
- ✅ 大按钮（易点击）
- ✅ 简化布局
- ✅ 快速加载

### 推荐使用场景：
- 📱 在外查看持仓
- 📱 快速记录交易
- 📱 查看 AI 推荐
- 📱 WIN/LOSS 按钮

---

## 🔄 与其他系统集成

### 与 Telegram Bot 配合：

**早上 9:00 AM：**
1. Telegram Bot 自动发送新闻摘要
2. 打开 Web Dashboard 查看 AI 推荐
3. 选择今日交易计划

**晚上 9:15 PM（开盘前）：**
1. Telegram Bot 发送交易计划
2. Web Dashboard 实时分析
3. 记录交易到 Journal

**盘中（9:30 PM - 4:00 AM）：**
1. 价格监控系统自动提醒
2. Web Dashboard 查看持仓
3. 快速 WIN/LOSS 记录

**凌晨 4:00 AM（收盘）：**
1. Telegram Bot 发送收盘总结
2. Web Dashboard 记录最终交易
3. 查看 Analytics

---

## 🆕 新增配置项说明

### push_times (推送时间)
```json
{
  "morning": "09:00",    // 早安新闻
  "premarket": "21:00",  // 开盘前计划
  "close": "04:00"       // 收盘总结
}
```

### monitor_rules (监控规则)
```json
{
  "price_change": 3.0,   // 涨跌 >3% 提醒
  "volume_mult": 2.0,    // 成交量 >2x 提醒
  "rsi_low": 30,         // RSI <30 提醒
  "rsi_high": 70         // RSI >70 提醒
}
```

### enabled_strategies (启用的策略)
```json
[
  "EMA Crossover",
  "Volume Breakout",
  "Support/Resistance"
]
```

### risk (风险管理)
```json
{
  "max_position_pct": 5,    // 单笔最大 5%
  "stop_loss_pct": 2,       // 默认止损 2%
  "max_daily_loss": 500     // 单日最多亏 $500
}
```

---

## 💡 最佳实践

### 每日流程建议：

**早上 9:00 AM：**
1. 查看 Dashboard
2. 阅读 AI Top 3
3. 制定今日计划

**晚上 9:00 PM：**
1. 打开 Web Dashboard
2. 查看 AI Analysis
3. 准备入场

**晚上 9:30 PM（开盘）：**
1. 执行交易计划
2. 记录到 Journal
3. 设置止损

**盘中：**
1. 监控 Positions
2. 快速记录 WIN/LOSS
3. 查看实时价格

**凌晨 4:00 AM（收盘）：**
1. 查看 Analytics
2. 总结今日
3. 计划明日

### 周末流程：

**周日：**
1. 打开 Strategy Lab
2. 查看上周 Report
3. 创建下周策略
4. 调整 Settings

---

## 🔧 故障排除

### 问题1: "TELEGRAM_TOKEN not found"
**解决：** 
```python
# 在 tradesniper.py 顶部直接设置
TELEGRAM_TOKEN = "你的token"
CHAT_ID = "923799250"
```

### 问题2: 股价不更新
**解决：** 点击 "🔄 Refresh" 按钮手动刷新

### 问题3: 配置不保存
**解决：** 确保点击了 "💾 SAVE ALL SETTINGS"

### 问题4: 手机端显示异常
**解决：** 
- 清除浏览器缓存
- 使用 Chrome/Safari
- 检查网络连接

---

## 📈 达成周目标 $1,000 的使用策略

### 系统化流程：

**目标分解：**
- 每周 $1,000 = 每天 $200
- 每天 2-3 笔交易
- 每笔平均 $100 利润

**使用 Dashboard：**
1. 早上看 AI Top 3
2. 选择信心度 >80% 的
3. 按推荐入场/止损/目标

**使用 Strategy Lab：**
1. 每周测试一个策略
2. 周末复盘
3. 保留好的，淘汰差的

**使用 Risk Management：**
1. 严格止损 2%
2. 单笔最多 5% 仓位
3. 单日亏损 >$500 停止

---

## 🚀 下一步

### 已完成：
- ✅ Web Dashboard v6.0
- ✅ Telegram Bot
- ✅ 12个策略库
- ✅ 定时推送系统
- ✅ 新闻系统
- ✅ 价格监控

### 明天要做：
- 🔜 IBKR 自动交易集成
- 🔜 回测系统
- 🔜 图表可视化

---

## 💬 需要帮助？

有问题或建议？
- 直接修改代码
- 查看 `geewoni_config.json` 配置文件
- 检查 `trades_history.json` 交易记录

---

**🎉 恭喜！你现在有一个专业级交易控制中心了！**

开始使用，祝你每周 $1,000！🚀💰