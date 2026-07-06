# 股票量化agent研究台

> 项目定位：**个人量化研究台**——看大盘 → 选股 → 策略回测 → AI Agent 智能解读。
> 不做实盘交易，聚焦研究 / 回测 / 智能分析。

---

# 快速开始

> 开发环境快速启动。数据库默认走 PostgreSQL（Docker），也可回落 SQLite。

## 数据库（PostgreSQL）

用 Docker Compose 起库，凭据在 `docker-compose.yml` / `backend/.env`。

```bash
# 项目根目录
docker compose up -d          # 启动 PostgreSQL（首次会拉 postgres:16 镜像）
docker compose ps             # 查看状态，healthy 即就绪
docker compose down           # 停库（数据保留在命名卷）
docker compose down -v        # 停库并清空数据（谨慎）
```

首次启动或换环境后，确保 `backend/.env` 有以下配置（已在 `.env.example` 提供）：

```
POSTGRES_DB=quant
POSTGRES_USER=quant
POSTGRES_PASSWORD=quant_dev_pw
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

> **回落 SQLite**：把 `.env` 里的 `POSTGRES_DB` 注释掉或删除即可，Django 会自动用 `backend/db.sqlite3`。设了 `POSTGRES_DB` 才走 PG。

## 后端（Django + DRF）

```bash
cd backend
conda run -n llmbase python manage.py migrate      # 首次 / 有模型变更时建表
conda run -n llmbase python manage.py runserver 8000
```

后端起在 `http://localhost:8000`，API 挂在 `/api/` 下。

## 前端（Vue + Vite）

```bash
cd frontend
npm install        # 首次
npm run dev        # http://localhost:5173（被占用会顺延到 5174/5175）
```

前端已配 Vite 代理，`/api` 转发到后端 8000。

## 依赖安装（首次 / 换机）

```bash
# 后端
cd backend && conda run -n llmbase python -m pip install -r requirements.txt
# 前端
cd frontend && npm install
```

## 数据迁移备份

- `backend/db.sqlite3.bak`：迁移前的 SQLite 库备份
- `backend/data_backup.json`：迁移用的全量 fixture（`dumpdata` 导出）

确认 PostgreSQL 稳定后，这两个文件可删除。若需从 SQLite 重新灌数据到 PG：

```bash
cd backend && conda run -n llmbase python manage.py loaddata data_backup.json
```

## 常见问题

- **镜像拉不到**：已在 `~/.docker/daemon.json` 配国内镜像加速器，改动后需重启 Docker Desktop 生效。
- **`conda run python -c` 报换行错**：conda run 不支持带换行的 `-c` 脚本，多行逻辑写成 `.py` 文件再跑。
- **端口占用**：后端 8000、前端 5173、数据库 5432。前端会自动顺延端口。



## 一、项目定位与介绍

前后端分离的 A 股量化研究 Web 应用：用户在暗色金融风界面查看实时大盘行情，
对个股运行经典量化策略回测，并能用**自然语言**让 AI Agent 自动解析需求、调用回测引擎、解读结果。

核心卖点：
- **数据稳**：通达信协议直连 + akshare 兜底的多源降级，数据库缓存，对外部接口抖动有韧性。
- **回测真**：自写向量化回测引擎，shift 防未来函数，输出收益/回撤/夏普/胜率四大金融指标。
- **AI 亮**：Claude + tool use 手动循环，把"自然语言 → 工具调用 → 结果解读"完整跑通，是区别于普通课设的关键亮点。

---

## 二、技术栈

| 层 | 选型 | 说明 |
|----|------|------|
| 后端 | Django 6 + Django REST Framework | 提供 JSON API，conda `llmbase` 环境 |
| 前端 | Vue 3 + Vite + Pinia + ECharts | 前后端分离，OKX 风暗色金融界面，Tailwind v4 |
| 数据库 | SQLite（开发）/ PostgreSQL（论文方案） | 行情 / 策略 / 回测 / 对话持久化 |
| 数据源 | 通达信（mootdx）+ akshare | 实时指数/个股走通达信，板块/广度走 akshare，多源降级 |
| 回测 | 自写 pandas 向量化引擎 | 非调库，论文有料 |
| AI Agent | Claude API + tool use | 自然语言驱动回测，核心亮点 |
| 认证 | DRF Token | 注册/登录、自选股、回测历史 |

---

## 三、系统架构

```
        Vue 3 前端 (Vite + Pinia + ECharts)
                  │ HTTP / JSON，Vite 代理 /api
                  ▼
        Django + DRF 后端
   ┌──────────┬──────────┬──────────┬──────────┐
 行情服务    回测引擎    Agent 服务   用户系统
(多源降级   (pandas    (Claude     (Token 认证
 +DB缓存)   向量化)     tool use)   自选股/历史)
                  │
                  ▼
        SQLite / PostgreSQL
   (行情缓存 / 策略 / 回测结果 / 对话)
```

四个后端 app：`market`（行情）、`backtest`（回测）、`agent`（AI）、`accounts`（用户）。
前端五个视图：大盘看板 / 量化工作台 / 回测历史 / 个股详情 / 登录。

---

## 四、核心模块与技术亮点

### 1. 行情数据层 —— 多源降级 + 缓存（稳定性设计）

这是整个系统的地基，也是答辩里能讲"工程深度"的地方。

**问题**：免费数据源（akshare 背后是 eastmoney/sina）慢且经常掉线，单一数据源不可靠。

**解法**：分数据类型做不同的主备策略，而非盲目堆一个源。

| 数据 | 主源 | 备源 | 说明 |
|------|------|------|------|
| 指数实时行情 | 通达信 mootdx | akshare 日线收盘 | 通达信走 TDX 原生二进制协议直连券商行情服务器，免 key、实时、稳 |
| 个股实时报价 | 通达信 mootdx | — | 给看板 ticker 跑马灯用 |
| 涨跌广度 / 行业板块 | akshare eastmoney | — | 数据最全（带领涨股、换手率），偶发波动时前端降级显示 |
| 个股 K 线历史 | akshare 新浪源 | — | 首次拉取后**落库 SQLite 缓存**，命中缓存不再打外部接口 |

工程细节：
- **缓存命中判断**：检查本地数据是否覆盖请求区间（容忍 ±7 天的节假日空档），未命中才拉外部。
- **退避重试**：外部调用包了 3 次线性退避重试，吸收瞬时网络抖动。
- **逐源容错**：看板接口里指数/广度/板块各自独立取数，任一失败只记入 `errors` 字段，不会让整个看板 500，前端对失败的源单独降级提示。
- **客户端单例**：mootdx 首次连接要选服务器（慢），做成进程内单例复用。


### 2. 向量化回测引擎（金融 + 工程双重含金量）

**自写**而非调用现成回测框架，这是论文的核心技术贡献。

- **向量化**：用 pandas 一次性算出整条收益曲线，而非逐日循环，性能好、代码简洁。
- **防未来函数**：策略在 T 日产生信号，引擎用 `position.shift(1)` 把持仓推迟一天兑现——
  即"今天的信号、明天才成交"，杜绝用到未来信息的 look-ahead bias。这是回测可信度的关键，答辩重点讲。
- **四大绩效指标**，每个都有金融含义：
  - 累计收益 `total_return`：策略最终净值 - 1
  - 最大回撤 `max_drawdown`：净值从峰值的最大跌幅，衡量风险
  - 夏普比率 `sharpe`：年化超额收益 / 波动率（×√252 年化），衡量风险调整后收益
  - 胜率 `win_rate`：盈利交易日占比
- **三种经典策略**：
  - 双均线 `ma_cross`：快线上穿慢线持有
  - RSI：超卖买入、超买卖出（均值回归）
  - 布林带 `bollinger`：触下轨买入、回中轨卖出
- **买卖点标注**：检测持仓翻转点，输出 buy/sell 标记供前端在收益曲线上画点。

实测样例：茅台布林带策略 2023–24 年 +21.6%，夏普 0.78。


### 3. 量化 AI Agent（最大亮点）

- **Claude + tool use 手动循环**：后端实现一个 while 循环，反复调用 Claude，
  直到 `stop_reason == "end_turn"`。Claude 决定调哪个工具、传什么参数，后端执行后把
  `tool_result` 喂回去，多轮直到给出最终答复。
- **三个工具**（复用已有后端能力）：
  - `list_strategies` 列策略
  - `get_quote` 查行情
  - `run_backtest` 跑回测（直接复用回测引擎）
- **完整链路**："用双均线回测茅台近三年，5日20日均线" → Claude 解析出 code/kind/params →
  调 `run_backtest` → 拿到真实指标 → 用中文解读收益/回撤/风险。
- **数字不编造**：system prompt 强约束所有数字必须来自工具返回。
- **对话持久化**：`Conversation` / `Message` 表存多轮上下文，前端可展开查看工具调用 `trace`（它做了什么）。
- **prompt caching**：system prompt 和工具定义各打 cache_control 断点，降低重复 token 成本。
- **安全**：API key 只在后端 `.env`，绝不下发前端。

> 论文对应章节："LLM Agent 的工具调用机制与 prompt 设计"。

### 4. 看板 UI（极客 / OKX 风）

- **实时轮询**：前端定时（8s）拉取大盘快照和 ticker 报价，数字平滑过渡。
- **动效**：
  - 顶部 ticker 跑马灯（热门股实时滚动，hover 暂停）
  - 指数卡 count-up 数字滚动 + 红涨绿跌 tick 闪烁 + hover 发光上浮 + 扫描线
  - 涨跌广度做成"恐贪指数"半圆仪表盘
  - 行业板块 ECharts treemap 热力图（红涨绿跌）
  - 全屏科技网格背景 + 蓝紫渐变光晕
  - 错峰进场动画，`prefers-reduced-motion` 降级
- **设计语言**：A 股惯例红涨绿跌，等宽字体显示数字，玻璃拟态面板。

### 5. 用户系统

- DRF Token 认证：注册 / 登录
- 自选股 CRUD（`WatchItem`）
- 回测历史：`Backtest.user` 可空——匿名也能回测，登录才存历史、可在历史页对比各次指标。

---

## 五、技术难点与解决

| 难点 | 解决 |
|------|------|
| 免费数据源不稳、慢 | 多源降级 + DB 缓存 + 退避重试 + 逐源容错 |
| 回测的未来函数陷阱 | 持仓 shift(1)，信号 T 日产生、T+1 兑现 |
| 让 LLM 真正"做事"而非空谈 | tool use 手动循环 + 工具复用后端引擎 + 数字强约束来自工具 |
| 通达信无行业板块涨跌幅 | 行业板块保留 akshare（通达信只有宽基指数、无行业板块行情）——**做了技术验证后的务实取舍** |
| 看板实时感 | 前端轮询 + 数字动画，而非整页刷新 |


## 八、项目数据一览

- 后端：4 个 Django app，11 个 API 接口
- 回测：3 种策略，4 个绩效指标，向量化实现
- 数据源：2 个（通达信 + akshare），多源降级
- AI：3 个工具，Claude tool use 多轮循环
- 前端：5 个视图，实时轮询 + ECharts 可视化

---

_配套文档：`docs/api.md`（接口文档）、`docs/frontend_design.md`（前端设计）、`PLAN.md`（开发计划与里程碑）。_
