# Agent System Context (Zeabur + Telegram + Python)

> 目的：构建一个可持续运行的 AI Agent 系统  
> - 有长期记忆（跨会话理解用户与历史任务）  
> - 可扩展 Skillset（工具化能力）  
> - 能拆分成多个子 agent 推进 workflow（受控并发）  
> - 严格控制 token 成本（避免滥用，自动降级）

---

## 1. 当前系统现状与近期目标

### 现状
- 部署平台：Zeabur（当前为 $5/月 developer plan + $5 额度）
- 服务形态：
  1) Backoffice（Python）：用于配置管理（CRUD）
  2) Telegram bot（polling）：接收消息并回复
- 未来要加：scheduler（定时任务）

### 近期目标
- 建立 Agent 的长期记忆机制（不把长历史全塞 prompt）
- 建立 Skill Registry + Router + Executor 的工具架构
- 增加 Scheduler/Worker（可选队列），支持自动化 workflow
- 加一个 LLM Gateway（middleware）统一控 token、缓存、降级、审计

---

## 2. 核心原则（非常重要）

1) **记忆分层**：短期/事件/语义分开，按需检索，不全量拼 prompt  
2) **模型负责决策，代码负责执行**：技能调用、数据库操作尽量在代码侧  
3) **昂贵推理只在关键节点用**：路由与改写尽量用小模型或规则  
4) **幂等与可重试**：scheduler、webhook/polling、多 agent 并发都必须幂等  
5) **token 预算是产品能力的一部分**：在 gateway 层统一治理

---

## 3. 目标架构（建议）

### 服务拆分（最低可行）
- backoffice-web：配置 CRUD、查看状态、手动触发任务
- telegram-bot：收消息/发消息，尽量不做耗时任务
- scheduler（建议独立服务）：定时扫描 DB → 生成任务/执行轻任务
- （可选）worker：专门处理耗时任务（LLM、外部 API、批处理）

### 逻辑层拆分（代码内）
- LLM Gateway（middleware）：统一
  - prompt 组装与上下文预算
  - memory 检索与摘要
  - 模型分层与自动降级
  - 缓存、日志、成本统计、限流
- Agent Runtime：
  - Router/Planner（决定用哪些 skill / 是否拆分子任务）
  - Executor（执行工具/业务逻辑）
  - Memory Writer（回合结束写入记忆）

---

## 4. 记忆系统设计（Long Memory）

### 4.1 三层记忆
1) Working Memory（短期）
- 当前会话最近 N 条消息 + 当前任务状态（仅运行时）
- 目标：让回答连贯，不超 token

2) Episodic Memory（事件记忆）
- "一次对话/一次任务发生了什么"的摘要
- 存：时间、主题、结论、行动项、未完成事项、关键参数
- 目标：回顾、追溯、减少长对话重放

3) Semantic Memory（语义记忆）
- 从多次对话提炼的稳定事实/偏好/规则/配置解释
- 用向量检索（RAG）按需取 topK
- 目标：跨会话"懂你"，但不浪费 token

### 4.2 记忆写入策略（token 省钱关键）
- **不要每条消息都写 semantic**  
- 推荐：每轮对话结束（或每个任务完成）做一次"结构化总结"：
  - 写入 episodic（几乎必写）
  - 决定是否提炼 semantic（只写稳定信息）
- 摘要写入可用小模型/短提示；严格 schema 输出

---

## 5. Skillset（技能系统）设计

### 5.1 Skill Registry（技能注册表）
每个 skill 都定义：
- name
- description（用来路由匹配）
- input_schema（JSON schema / pydantic）
- output_schema
- cost_tier（low/med/high）
- timeout_s
- can_parallel（true/false）
- idempotency_key strategy（如何保证重复调用不出错）

示例（概念）：
- search_memory(query) -> memories[]
- update_config(key, value) -> ok
- send_telegram(chat_id, text) -> message_id
- run_workflow(workflow_id) -> status

### 5.2 Router / Planner（路由/规划）
职责：
- 先判断 "是否需要工具调用"
- 再决定 "调用哪个 skill / 是否拆分子任务"
- 低成本优先（规则 > 小模型 > 大模型）

### 5.3 Executor（执行器）
职责：
- 真正调用数据库/外部 API/文件系统/队列
- 返回结构化结果
- 写入日志与 memory（必要时）

---

## 6. 多 Agent 工作流（受控并发）

### 6.1 不建议无限"生成 agent"
建议固定角色池（更省 token、更可控）：
- Planner：拆任务、产出计划（少调用）
- Worker：执行子任务（可并发、可重试）
- Critic/Verifier：关键节点验收（按需调用）

### 6.2 子 agent 上下文严格压缩
给子 agent 的输入只包含：
- 任务目标
- 必要约束（3~8条）
- 必要资料（检索 topK）
- 输出格式（schema）

避免：
- 把全量对话、全量记忆、全量日志发给每个子 agent

---

## 7. LLM Gateway（Middleware）— token 成本治理中心

必须实现的能力：

### 7.1 Prompt 组装与预算
- 设定 token_budget（例如 8k）
- 自动截断/摘要长对话
- memory 检索 topK + 去重
- 不同 skill 使用不同模板（不要一套 prompt 打天下）

### 7.2 模型分层与降级
- intent 简单：用小模型或规则
- intent 复杂：才用大模型
- 超预算/频率过高：自动降级为
  - "检索+模板答复"
  - "澄清问题（但要最少提问）"
  - "只返回行动计划不执行"

### 7.3 缓存（立刻省钱）
- embedding 结果缓存
- 检索 topK 缓存（短 TTL）
- 常见问答/改写结果缓存（短 TTL）

### 7.4 观测与审计
- 每次请求记录：input_tokens/output_tokens/latency/model/skill_calls
- 按 user / chat / workflow 统计月度 token

### 7.5 防滥用阀门
- 每轮允许的大模型调用次数
- 每分钟调用上限
- 预算耗尽提示 + 降级策略

---

## 8. 数据库设计（Postgres 建议）

> 注：可先不做向量，先做结构化 + 基础检索；后续再加 pgvector。

### 8.1 核心表（最小可行）
- users
  - id, telegram_user_id, created_at
- conversations
  - id, user_id, channel, created_at, updated_at
- messages
  - id, conversation_id, role(user/assistant/system), content, created_at, meta(jsonb)
- memory_episodic
  - id, user_id, conversation_id, summary_text, summary_json(jsonb), tags(text[]), created_at
- memory_semantic
  - id, user_id, key, value_text, value_json(jsonb), source_episode_id, created_at, updated_at

### 8.2 任务与调度（为 scheduler 准备）
- jobs
  - id
  - type (e.g. "reminder", "retry_send", "daily_digest")
  - run_at (timestamp)
  - status ("pending", "running", "done", "failed")
  - payload (jsonb)
  - locked_at, locked_by
  - retry_count, max_retries
  - last_error
  - created_at, updated_at

**幂等策略**：
- 为每类 job 设计 natural key（例如 user_id + date + type）
- 或使用 idempotency_key 字段唯一约束

---

## 9. 执行流程（推荐）

### 9.1 Telegram polling 主流程（低 token 版）
1) 接收 update
2) 幂等检查（update_id 是否已处理）
3) 写入 messages（user）
4) intent 分类（规则或小模型）
5) memory 检索（semantic topK + 最近 episodic topN）
6) router 决策（是否调用 skill / 是否启动 workflow）
7) 调用 LLM（受预算控制）
8) 输出回复（send_telegram）
9) 回合结束：写入 episodic summary；必要时提炼 semantic

### 9.2 Scheduler 流程（省钱 + 稳定）
- 每 30~60 秒醒一次（或外部 cron 触发）
- SELECT 到期 pending jobs（limit N）
- 原子加锁（locked_at/locked_by）
- 执行（轻任务优先；重任务丢给 worker）
- 更新状态 + 记录错误 + 重试策略

---

## 10. Query Rewrite（把问题"变专业"以省 token）

两步走：
1) Rewrite（轻量）
- 把用户输入改写成：
  - 明确目标
  - 必要约束
  - 期望输出格式（schema）
- 这一步尽量用小模型或规则

2) Retrieve & Answer（真正回答）
- 用改写后的 query 做 memory 检索
- 把"精炼问题 + 检索结果"发给大模型
- 减少模型追问与胡猜

---

## 11. 落地路线图（按最小成本上线）

### Phase 1：Memory v1（马上可用）
- messages + episodic summary 写入
- semantic 先用结构化 key-value（不做向量）
- gateway：只做上下文截断 + 基础日志

### Phase 2：Skill Registry + Router（稳定性显著提升）
- 先做 3~5 个核心 skill
- router 用规则/小模型决定是否调用
- executor 统一错误处理与重试

### Phase 3：Scheduler（自动化开始）
- jobs 表 + scheduler service
- 幂等锁 + 重试
- 先不引入队列也行

### Phase 4：Worker + Queue（当耗时任务变多）
- 把 LLM/外部 API/批处理放进 worker
- scheduler 只负责派发
- gateway 加缓存 + 降级策略

### Phase 5：多 agent（只在复杂 workflow 上启用）
- 固定三角色池（Planner/Worker/Critic）
- 并发只在可独立验证任务上开启
- 子 agent 上下文严格压缩

---

## 12. 关键决策建议（结合 Zeabur $5 档）

- polling 可以继续用：务必使用 long polling（阻塞等待，降低 CPU）
- scheduler 建议做成"轻量循环 + 长 sleep"，避免空转
- 不要一开始就引入复杂编排/多 agent：先把 gateway + memory + skills 打稳
- token 成本治理优先级高于"更聪明"：先控预算再谈智能

---

## 13. 开发检查清单（DoD）

### Memory
- [ ] 每轮结束写 episodic summary（结构化 + 文本）
- [ ] semantic 只写稳定信息（偏好/规则/配置解释）
- [ ] 检索 topK，且去重、限长

### Gateway
- [ ] token budget + 自动摘要/截断
- [ ] 记录 token/latency/model
- [ ] 缓存（至少检索与改写）
- [ ] 超预算降级策略

### Skills
- [ ] registry（schema、成本级别、超时）
- [ ] executor 幂等 + 重试
- [ ] router 优先规则/小模型

### Scheduler
- [ ] jobs 表 + 锁字段
- [ ] 原子抢锁，防重复执行
- [ ] retry 策略与告警（至少日志可查）

---

## 14. 下一步要实现的最小代码模块（建议）

1) `gateway/`
- prompt_builder.py
- memory_retriever.py
- budget.py
- cache.py
- metrics.py

2) `agent/`
- router.py
- planner.py (optional)
- runtime.py

3) `skills/`
- registry.py
- executor.py
- skills_impl/*.py

4) `scheduler/`
- scheduler_loop.py
- jobs_repo.py

---

## 15. 约定（Cursor 需要遵守的实现偏好）

- 语言：Python
- DB：Postgres（先结构化，后可加向量）
- 设计优先：幂等、可观测、低 token、可扩展
- 默认避免：把长历史全量塞 prompt；无限多 agent 并发；每条消息都写 semantic

END
