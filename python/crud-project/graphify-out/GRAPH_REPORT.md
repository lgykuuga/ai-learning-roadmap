# Graph Report - .  (2026-08-01)

## Corpus Check
- Corpus is ~7,106 words - fits in a single context window. You may not need a graph.

## Summary
- 84 nodes · 178 edges · 8 communities
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Response Schemas
- Roadmap API Handlers
- Check-in Workflow
- Domain Models and Seed
- Frontend API Calls
- Runtime Dependencies
- Database Sessions

## God Nodes (most connected - your core abstractions)
1. `ApiResult` - 13 edges
2. `toggle_done()` - 9 edges
3. `Progress` - 8 edges
4. `create_checkin()` - 8 edges
5. `list_phases()` - 8 edges
6. `save_note()` - 8 edges
7. `Day` - 7 edges
8. `Checkin` - 7 edges
9. `get_weeks()` - 6 edges
10. `get_days()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `save_note()` --calls--> `Progress`  [EXTRACTED]
  routers/phases.py → models.py
- `toggle_done()` --calls--> `Progress`  [EXTRACTED]
  routers/phases.py → models.py
- `toggle_done()` --calls--> `Checkin`  [EXTRACTED]
  routers/phases.py → models.py
- `list_checkins()` --calls--> `ApiResult`  [EXTRACTED]
  routers/checkins.py → schemas.py
- `create_checkin()` --calls--> `ApiResult`  [EXTRACTED]
  routers/checkins.py → schemas.py

## Import Cycles
- None detected.

## Communities (8 total, 0 thin omitted)

### Community 0 - "Response Schemas"
Cohesion: 0.27
Nodes (15): BaseModel, list_phases(), phases.py — 阶段/周/天/进度 路由 ==================================, 获取所有阶段及其嵌套的周、天、进度和笔记。 前端一次性加载全部数据，减少请求次数。, DayDetail, DayFullOut, DayListItem, DoneToggle (+7 more)

### Community 1 - "Roadmap API Handlers"
Cohesion: 0.23
Nodes (16): put, get_day_detail(), get_day_done_counts(), get_days(), get_stats(), get_weeks(), AsyncSession, get (+8 more)

### Community 2 - "Check-in Workflow"
Cohesion: 0.19
Nodes (13): main.py — 学习路线图后台服务入口 ================================== 启动: python -m uvicorn…, Checkin, Progress, 学习进度表 — 每 Day 最多一条记录（1:1）, 打卡记录表 — 每次打卡一条记录（1:N）, post, create_checkin(), list_checkins() (+5 more)

### Community 3 - "Domain Models and Seed"
Cohesion: 0.27
Nodes (12): Base, Day, Phase, models.py — 学习路线图 5 张表 ============================= Phase → Week → Day (1:N:N)…, 天表 — 核心内容表。detail 存富文本（Markdown格式）, 阶段建议表 — 每个 Phase 有 2 条 tips, Tip, Week (+4 more)

### Community 4 - "Frontend API Calls"
Cohesion: 0.25
Nodes (9): API-Backed Roadmap State, PUT /api/days/{id}/done, PUT /api/days/{id}/note, GET /api/phases, GET /api/stats, AI Learning Roadmap Application, Daily Learning Check-In, Learning Progress Tracking (+1 more)

### Community 5 - "Runtime Dependencies"
Cohesion: 0.29
Nodes (7): PostgreSQL Service, asyncpg 0.30.0, FastAPI 0.115.6, psycopg2-binary 2.9.10, Python Application Dependencies, SQLAlchemy AsyncIO 2.0.36, Uvicorn 0.34.0

### Community 6 - "Database Sessions"
Cohesion: 0.40
Nodes (3): config.py — 数据库连接配置 ============================ 异步引擎连接…, get_db(), database.py — 异步 + 同步双引擎 ================================= 注意点 1: 异步引擎用于…

## Knowledge Gaps
- **8 isolated node(s):** `PostgreSQL Service`, `FastAPI 0.115.6`, `Uvicorn 0.34.0`, `SQLAlchemy AsyncIO 2.0.36`, `psycopg2-binary 2.9.10` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ApiResult` connect `Roadmap API Handlers` to `Response Schemas`, `Check-in Workflow`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Why does `create_checkin()` connect `Check-in Workflow` to `Roadmap API Handlers`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `Day` connect `Domain Models and Seed` to `Response Schemas`, `Check-in Workflow`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **What connects `PostgreSQL Service`, `FastAPI 0.115.6`, `Uvicorn 0.34.0` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._