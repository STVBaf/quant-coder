# 股票量化研究台 — 开发计划

> 课程结课项目：Python 前后端 + 数据库 + 论文。
> 定位「个人量化研究台」：看大盘 → 选股 → 策略回测 → AI Agent 智能解读。
> 不做实盘交易，聚焦研究 / 回测 / 智能分析。

## 技术栈

| 层 | 选型 | 说明 |
|----|------|------|
| 后端 | Django 6 + DRF | conda `llmbase` 环境，提供 JSON API |
| 前端 | Vue 3 + Vite + Pinia + ECharts | 前后端分离，暗色金融风 |
| 数据库 | SQLite（开发）/ PostgreSQL（论文方案） | 行情 / 策略 / 回测 / 对话 |
| 数据源 | akshare | A股行情、指数、板块，免费 |
| 回测 | 自写 pandas 向量化引擎 | 论文有料 |
| Agent | Claude API + tool use | 自然语言驱动回测，核心亮点 |

## 系统架构

```
Vue 前端  ──HTTP/JSON──>  Django + DRF
                              │
              ┌───────────────┼────────────────┐
          行情服务         回测引擎          Agent 服务
        (akshare缓存)    (pandas向量化)   (Claude tool use)
                              │
                          SQLite/PG
                    (行情/策略/回测结果/对话)
```

关键设计：akshare 数据落库缓存，缓存未命中才打外部接口（慢且不稳）。

## 数据模型

- `market.Stock`：code / name / industry
- `market.DailyBar`：stock / date / OHLCV，unique(stock, date)
- `backtest.Strategy`：name / kind(ma_cross|rsi|bollinger) / params(JSON)
- `backtest.Backtest`：strategy / stock / 区间 / metrics(JSON) / equity_curve(JSON)
- Agent 对话表：里程碑 5 引入（Conversation / Message）

## 里程碑

### M1 — 脚手架与数据层 ✅ 已完成
- [x] 后端工程：config + market + backtest，DRF/CORS 配置
- [x] 数据模型 + migration
- [x] akshare 数据层 + DB 缓存（`market/services.py`）
- [x] K线 API：`GET /api/market/kline/<code>/?start=&end=`
- [x] 前端脚手架：路由 / 看板占位 / K线图（ECharts 蜡烛图，可缩放）
- [x] 全链路验证：真实茅台行情拉通，前端 build 通过

### M2 — 大盘看板
- [x] 指数行情 API：上证 / 深证 / 创业板（`stock_zh_index_daily`）
- [x] 涨跌分布 API：当日涨跌/涨停/跌停家数（`stock_market_activity_legu`）
- [x] 行业板块 API：板块涨跌幅（`stock_board_industry_name_em`）
- [x] 前端看板：指数卡片 + 涨跌分布 + 板块热力图（ECharts treemap，红涨绿跌）
- [x] 修复个股 name 回填（改用 `stock_zh_a_spot_em` 全市场快照 + 进程内缓存；旧的 `stock_individual_info_em` 在当前 akshare 版本有列数 bug）
- 验收：首页展示真实大盘数据，板块热力图可交互 ✅

### M3 — 回测引擎
- [x] 向量化回测核心（`backtest/engine.py`）：信号 → 持仓(shift 防未来函数) → 收益曲线
- [x] 三个策略：双均线、RSI、布林带（`backtest/strategies.py`）
- [x] 绩效指标：累计收益、最大回撤、夏普比率、胜率
- [x] 回测 API：`GET /api/backtest/strategies/`、`POST /api/backtest/run/`（结果落 `Backtest` 表）
- [x] 前端回测页：参数表单 + 收益曲线 + 指标卡 + 买卖点标注
- 验收：选股选策略调参，能跑出收益曲线和指标 ✅（茅台布林带 2023-24 +21.6%/夏普0.78）

### M4 — 用户系统与历史
- [ ] 用户注册 / 登录（DRF Token 或 Session）
- [ ] 自选股 CRUD
- [ ] 回测历史保存与列表（落 `Backtest` 表）
- [ ] 多策略 / 多参数对比视图
- 验收：登录后保存回测、查看历史、对比结果（体现完整 CRUD）

### M5 — 量化 Agent（核心亮点）
- [ ] Agent 服务（`agent/` app）：Claude API + tool use
- [ ] 工具注册：`get_quote` / `run_backtest` / `list_strategies`
- [ ] 对话表 + 工具调用记录持久化
- [ ] Agent API：`POST /api/agent/chat/`（流式可选）
- [ ] 前端对话面板：自然语言驱动回测，展示解读
- [ ] API key 放后端 `.env`，绝不进前端
- 验收：「用双均线回测茅台近三年，5日20日均线」→ Agent 自动解析参数、调回测工具、自然语言解读收益与风险

## 论文章节（建议）

1. 选题背景与系统定位
2. 系统架构与前后端分离设计
3. 行情数据采集与缓存层设计
4. 向量化回测引擎实现与绩效指标金融含义
5. LLM Agent 的工具调用机制与 prompt 设计
6. 回测实验与结果分析
7. 总结与展望

## 启动方式

```bash
# 后端
cd backend && conda run -n llmbase python manage.py runserver 8000
# 前端（另开终端）
cd frontend && npm run dev   # http://localhost:5173
```

## 待确认事项

- Agent 是否需要流式输出（打字机效果，演示更佳但实现略复杂）
- 用户系统用 Token 还是 Session 认证
- 论文是否需要中英文对照
