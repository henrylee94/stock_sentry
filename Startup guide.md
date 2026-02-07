# 🚀 GEEWONI 系统启动指南

## 📦 你需要的文件清单

### 核心文件（必须）：
```
Geewoni-Sentry/
├── telegram_bot.py          ✅ 主 Bot
├── skillset_manager.py      ✅ 策略管理
├── token_tracker.py         🆕 Token 追踪
├── skills/                  ✅ 策略文件夹
│   ├── technical_analysis/
│   ├── fundamental/
│   ├── risk_management/
│   └── market_conditions/
├── requirements.txt         ✅ 依赖
├── .env                     ✅ 环境变量
└── tradesniper.py          ✅ Web Dashboard（可选）
```

---

## ⚡ 3步启动系统

### Step 1: 更新 requirements.txt

确保包含：
```txt
python-telegram-bot==21.4
yfinance==0.2.40
openai==1.51.2
pandas==2.2.2
numpy==1.26.4
requests==2.31.0
python-dotenv==1.0.1
pytz==2024.1
streamlit==1.38.0
tiktoken==0.5.1
```

---

### Step 2: 集成 Token 追踪到 Bot

在 `telegram_bot.py` 顶部添加：

```python
# 在导入部分添加
from token_tracker import token_tracker

# 在 ai_brain 函数中，调用 OpenAI API 后添加：
# （找到这一行）
response = client.chat.completions.create(...)
response_text = response.choices[0].message.content

# 添加这两行：
token_tracker.log_request(user_query, response_text)
print(token_tracker.format_usage_display())  # 在控制台显示
```

完整示例：
```python
async def ai_brain(update: Update, context):
    # ... 现有代码 ...
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[...],
        max_tokens=600,
        temperature=0.3
    )
    
    response_text = response.choices[0].message.content
    
    # 🆕 记录 Token 使用
    usage_info = token_tracker.log_request(user_query, response_text)
    
    # 在回复中添加 Token 信息
    await update.message.reply_text(
        f"{response_text}\n\n"
        f"⚙️ AI 使用: {ai_usage_today}/{daily_limit}\n"
        f"📊 本次: {usage_info['total_tokens']} tokens (${usage_info['cost']:.6f})",
        parse_mode='HTML'
    )
```

---

### Step 3: 添加 /tokens 命令

在 `telegram_bot.py` 添加新命令：

```python
async def tokens_command(update: Update, context):
    """显示 Token 使用情况"""
    stats = token_tracker.get_statistics()
    
    message = f"""📊 <b>Token 使用统计</b>

<b>📅 今日</b>
• Tokens: {stats['today']['total_tokens']:,}
• 请求数: {stats['today']['requests']}
• 成本: ${stats['today']['cost']:.4f}

<b>📆 本周</b>
• Tokens: {stats['weekly']['total_tokens']:,}
• 成本: ${stats['weekly']['cost']:.4f}

<b>💰 总计</b>
• Tokens: {stats['total']['total_tokens']:,}
• 成本: ${stats['total']['total_cost']:.2f}

<b>📈 平均</b>
• 每次请求: {stats['avg_tokens_per_request']:.0f} tokens
• 每次成本: ${stats['avg_cost_per_request']:.6f}
"""
    
    await update.message.reply_text(message, parse_mode='HTML')

# 在 main() 中注册命令
application.add_handler(CommandHandler("tokens", tokens_command))
```

---

## 🌐 Web Dashboard Token 显示

### 方案 A: 使用完整新版本

```bash
# 替换你的 tradesniper.py
copy tradesniper_complete_with_tokens.py tradesniper.py
```

特点：
- ✅ 右上角实时显示 Token 使用
- ✅ 专门的 Token Usage 标签页
- ✅ 自动记录每次 AI 调用
- ✅ 每日/每周/每月统计

### 方案 B: 只添加 Token 显示到现有版本

在你现有的 `tradesniper.py` 顶部添加：

```python
from token_tracker import token_tracker

# 在页面顶部显示
st.sidebar.markdown("## 📊 Token Usage")
stats = token_tracker.get_statistics()

st.sidebar.metric("Today Tokens", f"{stats['today']['total_tokens']:,}")
st.sidebar.metric("Today Cost", f"${stats['today']['cost']:.4f}")
st.sidebar.metric("Week Cost", f"${stats['weekly']['cost']:.4f}")
```

---

## 🚀 部署到 Zeabur

### 本地测试：
```bash
# 测试 Bot
py -3.12 telegram_bot.py

# 测试 Dashboard
streamlit run tradesniper.py
```

### 推送到 GitHub：
```bash
git add .
git commit -m "Add Token tracking system"
git push
```

### Zeabur 自动部署：
- ✅ 检测到更新
- ✅ 自动重新部署
- ✅ 新功能上线

---

## 💰 Zeabur 成本优化

### 当前设置：
```
Bot (24/7 运行):
- 内存: ~150MB
- CPU: ~5%
- 预计: $3-4/月

Dashboard (按需):
- 只在访问时运行
- 15分钟无活动自动休眠
- 预计: $1-2/月

总计: $4-6/月（在 $5 免费额度内）
```

### 优化技巧：
1. **Dashboard 设置自动休眠**
   - Zeabur Dashboard → 你的服务 → Settings
   - 启用 "Auto Sleep"
   - 15分钟无活动自动休眠

2. **Bot 使用轻量级配置**
   - 已经很轻量了
   - 不需要额外优化

3. **监控使用量**
   - Zeabur Dashboard 查看实时使用
   - 接近 $5 时可以手动暂停 Dashboard

---

## 📊 Token 使用建议

### 成本控制：
```
gpt-4o-mini 定价：
- Input: $0.15 / 1M tokens
- Output: $0.60 / 1M tokens

预计使用：
- 平均每次对话: ~500 tokens
- 每次成本: ~$0.0003
- 每天 50 次对话: ~$0.015
- 每月成本: ~$0.45

完全在预算内！✅
```

### 每日限制建议：
```python
# 在 telegram_bot.py 设置
daily_limit = 1000  # 每天最多 1000 次请求

# 或设置 Token 限制
max_daily_tokens = 500_000  # 50万 tokens/天
```

---

## ✅ 启动检查清单

运行前确认：

```
□ requirements.txt 已更新（包含 tiktoken）
□ token_tracker.py 已添加到项目
□ telegram_bot.py 已集成 token_tracker
□ 添加了 /tokens 命令
□ .env 包含所有必需的环境变量
□ 本地测试通过
□ 已推送到 GitHub
□ Zeabur 已检测到更新
```

---

## 🎯 快速命令参考

### Telegram Bot 命令：
```
/start          # 开始
/stats          # 交易统计
/tokens         # Token 使用情况（新！）
/morning        # 早盘摘要
/skills         # 查看策略
/skill [名称]   # 策略详情

直接问: "NVDA 入场点?"
```

### Web Dashboard：
```
http://localhost:8501          # 本地
https://你的域名.zeabur.app     # Zeabur

页面：
- Dashboard    # 总览
- AI Chat      # 对话（显示 Token）
- Stocks       # 实时股价
- Journal      # 交易记录
- Settings     # 配置
- Token Usage  # Token 统计（新！）
```

---

## 🆘 常见问题

### Q: Token 追踪不工作？
A: 确保：
1. `token_tracker.py` 在项目根目录
2. `telegram_bot.py` 正确导入
3. 有写入权限创建 `token_usage.json`

### Q: 成本计算不准？
A: Token 追踪使用估算，实际成本以 OpenAI 账单为准

### Q: Zeabur 超额了怎么办？
A: 
1. 暂时关闭 Dashboard（只保留 Bot）
2. 减少 AI 调用频率
3. 或升级到付费计划（$5/月）

---

## 🎉 完成！

现在你的系统有：
- ✅ Telegram Bot（24/7）
- ✅ Web Dashboard（按需）
- ✅ 12个专业策略
- ✅ Token 使用追踪
- ✅ 实时成本监控

**下一步：** 测试系统，开始交易！💰

有问题随时问！🚀