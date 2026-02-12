# Tesla Day Trade Telegram Bot - 完整需求、架構與實現藍圖

**作者**：Junheng Lee  
**地點**：Petaling Jaya, Selangor, Malaysia  
**日期**：2026 年 2 月  
**目前狀態**：已有 Python + python-telegram-bot + Finnhub 拉 realtime 數據的簡單 bot，已部署在 Zeabur  
**目標**：把簡單 bot 升級成智能、會自我學習的 day trade 助手，全程只透過 Telegram 操作

## 1. 核心目標與使用者體驗

- 使用者（我）全程只用 Telegram 跟 bot 聊天
- bot 記得我的 preference（風險偏好、資金規模、喜歡/討厭的策略類型等）
- 問「[任何 US stock, e.g. TSLA / AAPL / NVDA] 現在多少錢？要買嗎？」 → bot 拉 **realtime** 數據（Finnhub），分析技術指標，給買入/賣出建議 + 價格 + 理由
- bot 能主動生成多種 strategy，列出來給我看
- 對每種 strategy 先做 backtest（歷史數據模擬），算勝率、盈虧比、max drawdown 等
- 根據 backtest 結果 + 我的 preference，推薦最佳 strategy
- bot 能自我優化：如果勝率不理想，自動調整參數或生成新變體，迭代幾輪直到改善（有限次數）
- 長期學習：把每次 backtest 結果、我的反饋、有效/無效策略記下來，下次生成時優先參考
- 額外功能：拉重要新聞、簡單情緒分析、產生 K 線 + 指標圖表發到 Telegram
- **新需求：支援任意 US stock** - 不限 Tesla，所有工具/代理人/agent 需泛化到任意 symbol（e.g. 輸入 AAPL，就自動切換分析該股）
- **新需求：Stock Scanner 功能** - bot 能掃描高勝率股票（適合 day trade：快速進出），基於 realtime 數據 + 策略模板，找出「現在勝率較高、可馬上進場、快速出場」的機會股（e.g. 問「今天哪隻 US stock 適合 day trade？」 → 掃描 S&P 500 或自訂清單，列出 top 3-5 隻 + 理由 + 預期進出價）

**重要提醒**：這是分析工具，不是自動交易系統。所有建議僅供參考，day trade 風險極高，不構成財務建議。

## 2. 技術架構總覽（2026 年主流 Python + Zeabur 友好）
Telegram (入口)
↓ (Webhook / polling)
Bot Handler (python-telegram-bot)
↓
LangGraph Workflow (Stateful Graph + Multi-Agent)
├── Shared: RAG (FAISS / Pinecone) – 長期記憶 (preference、過去策略、backtest 結果)
├── Tools / Skillset (LangChain @tool)
│   ├── Finnhub realtime quote + volume (支援任意 symbol)
│   ├── 技術指標計算 (EMA, SMA, support/resistance, RSI, VWAP... 支援任意 symbol)
│   ├── 拉新聞 + 簡單情緒 (支援任意 symbol)
│   ├── Backtest engine (pandas + ta-lib, 支援任意 symbol)
│   ├── Preference read/write (JSON / DB)
│   ├── Stock Scanner tool (掃描多股：拉 S&P 500 清單 + 快速篩選高 volume / volatility / 符合策略的股)
│   └── (未來) 圖表生成 (matplotlib → bytes → Telegram photo, 支援任意 symbol)
└── Multi-Agent Nodes
├── Strategy Generator Agent (泛化到任意 US stock)
├── Backtester Agent (泛化到任意 US stock)
├── Optimizer / Reflector Agent
├── Decision / Summarizer Agent
└── Scanner Agent (新：掃描高勝率 day trade 機會股)


## 3. 關鍵組件詳細說明

### 3.1 Tools / Skillset
- 每個 tool 是 @tool 裝飾的 Python function
- 目前已有：Finnhub quote
- 需新增：
  - calculate_ema / rsi / vwap / support_resistance (輸入 symbol)
  - fetch_news_sentiment (輸入 symbol)
  - backtest_strategy (輸入 strategy 描述 + symbol → 輸出 win_rate, profit_factor 等)
  - save_preference / get_preference
  - scan_stocks (新：輸入清單 e.g. S&P 500 symbols、策略模板 → 掃描 realtime 數據，找出高勝率 / 高 volatility / 適合快速進出的股，輸出 top N + 理由)

### 3.2 RAG (長期記憶與學習)
- 用 FAISS (本地，Zeabur Volume 持久化) 或 Pinecone
- 存什麼？
  - 我的 preference 文字
  - 每次生成的 strategies + backtest 結果 (包含 symbol 資訊)
  - 我的反饋（e.g. /feedback "這個策略太激進"）
  - 歷史學習結論（e.g. "EMA crossover + volume filter 在 NVDA 上勝率較高"）
  - Scanner 歷史：哪些股在哪些日子適合 day trade
- 每次 agent 啟動，先 retrieve 相關記憶注入 prompt

### 3.3 Multi-Agent 與自我提升流程 (LangGraph)

Graph 節點與條件邊：

1. **Generator** → 根據 preference + realtime 數據 + RAG 歷史，生成 3–5 種 strategy（文字描述 + 規則，支援任意 symbol）
2. **Backtester** → 對每種 strategy 跑 backtest（用 Finnhub 歷史 1-min bars，30 天內，支援任意 symbol）
3. **Evaluator** → 計算指標，排序，選 best
4. **Optimizer** (條件觸發) → 如果 best win_rate < 閾值（e.g. 65%），反思 + 生成改進版 → 回 Backtester（最多迭代 3–5 次）
5. **Decision** → 綜合 RAG preference + backtest，給最終建議 + 買賣價格
6. **Scanner** (新 node) → 掃描多股機會：用 scan_stocks tool，拉 S&P 500 或自訂清單，快速 backtest / 指標篩選，找出適合 day trade（高勝率、快速進出）的股
7. **Summarizer** → 整理成易讀 Telegram 訊息（可含圖表）

狀態 (AgentState) 包含：
- messages
- preference
- symbol (新：預設 TSLA，但可動態指定任意 US stock)
- strategies: list
- backtest_results: dict
- best_strategy
- optimized_strategies: list
- scan_results: list (新：掃描出的高勝率股)
- final_recommendation

## 4. 常見 Strategy 模板（作為 LLM 生成的起點，泛化到任意 US stock）

| 名稱                  | 核心邏輯                              | 買入條件示例                              | 賣出/止損示例                     |
|-----------------------|---------------------------------------|-------------------------------------------|-----------------------------------|
| EMA Crossover         | 快慢 EMA 交叉                         | EMA8 > EMA21 + volume > 1.5×avg           | EMA8 < EMA21 或 +2% / -1%         |
| VWAP Bounce           | 價格觸 VWAP 反彈                      | 價格下探 VWAP + 長下影線 + volume spike   | 達前高或 -0.8%                    |
| Breakout              | 突破趨勢線 / 前高                     | 突破 + volume > avg × 2                   | 跌回突破點下或 trailing stop      |
| RSI Exhaustion        | 超買超賣反轉                          | RSI < 30 + 看漲燭                         | RSI > 70 或固定利潤               |
| Volume + Momentum     | 高量突破                              | 價格新高 + volume > 2×avg                 | 動能減弱或止損                    |

LLM 可動態變奏（改 period、加 filter、結合多指標），並根據 symbol 特性調整（e.g. 高 volatility 股如 TSLA 用短 EMA）。

## 5. 實現優先順序建議

Phase 1（最快看到成果）
- 完成 tools：realtime quote、EMA、backtest（簡單 EMA crossover 模板，支援任意 symbol）
- 加 preference JSON 存取 + /set_preference 指令
- 讓 bot 能回答「[symbol] strategy」→ 給 1–2 種 + 簡單 backtest

Phase 2
- 加 RAG (FAISS) 存 preference + backtest 歷史
- 建 LangGraph：Generator → Backtester → Decision
- 支援多 strategy 列出 + 排序
- 泛化到任意 US stock（所有工具加 symbol 參數）

Phase 3（自我提升）
- 加 Optimizer node + 條件循環
- 加 Evaluator 自動判斷是否需再優化
- 存每次迭代結果進 RAG，讓未來生成偏好高勝率模式

Phase 4（Stock Scanner + polish）
- 加 scan_stocks tool + Scanner agent
- Scanner 邏輯：拉 S&P 500 清單（Finnhub API 或硬碼），對每股快速檢查 volume / volatility / 指標 match，篩出 top 高勝率 / 適合快速進出的股
- 新聞 + 情緒
- 圖表生成 + 發 Telegram photo
- 更多指標實現（support/resistance 用 peak detection？）

## 6. 注意事項與風險

- **法律與合規**：僅分析，不自動下單。馬來西亞 SC 監管注意。
- **成本**：Finnhub call、LLM token、Zeabur resource（scanner 多 call 需優化）
- **安全**：API key 用環境變數；backtest code 用 sandbox 或限制 eval
- **現實**：Backtest ≠ 未來表現，overfitting 風險高；scanner 需限頻率，避免 API 濫用
- **Debug**：先本地跑 graph，再 deploy Zeabur

## 7. 下一步想做的細節（待補充）

- 完整 backtest 邏輯（如何 parse 文字 strategy → 可執行 code）
- 最佳 LLM 選擇（Claude 3.5 / GPT-4o-mini / DeepSeek）
- 圖表產生範例 code
- Scanner 清單來源（Finnhub market API 拉 S&P 500 symbols？）
- 更多指標實現（support/resistance 用 peak detection？）

---
最後更新：2026-02-09  
這份文件作為我的「需求規格 + 架構藍圖」，可直接餵給 IDE / Copilot / Cursor / 自己看懂下一步要做什麼。
