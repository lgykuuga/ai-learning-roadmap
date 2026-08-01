# 📋 学习路线图

6 个月 · 92 天 · 每天 3 小时

Python + FastAPI + SQLite 全栈应用，浏览器打开即用。

---

## 快速启动

```bash
cd python/crud-project

# 1. 安装依赖（首次）
pip install -r requirements.txt

# 2. 初始化数据（首次，需要 Node.js）
python seed.py

# 3. 启动服务
python -m uvicorn main:app --reload --port 8000
```

然后打开浏览器访问 `http://localhost:8000/static/ai-learning-roadmap.html`

> **不需要**装 PostgreSQL 或 Docker——数据存在本地 SQLite 文件 `roadmap.db`。
> seed.py 首次运行会自动从 HTML 里解析 92 天学习内容并入库。

---

## 项目结构

```
python/crud-project/
├── main.py              # FastAPI 启动入口 + 静态文件挂载
├── config.py            # 数据库连接串（切数据库只改这里）
├── database.py          # 异步 + 同步双引擎（SQLAlchemy 2.0）
├── models.py            # ORM 模型：Phase / Week / Day / Progress / Checkin / Tip
├── schemas.py           # Pydantic 请求/响应模型
├── seed.py              # 数据初始化脚本（从 HTML 解析 92 天 -> 入库）
├── docker-compose.yml   # PostgreSQL（可选，默认用 SQLite）
├── requirements.txt     # Python 依赖
├── roadmap.db           # SQLite 数据库文件（自动生成）
├── routers/
│   ├── phases.py        # /api/phases, /api/days/{id}, /api/stats
│   └── checkins.py      # /api/checkins
└── static/
    └── ai-learning-roadmap.html  # 前端页面（调 API 渲染，不存数据）
```

---

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/phases` | 全部数据（阶段→周→天，含进度+笔记） |
| GET | `/api/days/{id}` | 某天详情（富文本 detail） |
| PUT | `/api/days/{id}/done` | 标记完成/取消 `{"done":true}` |
| PUT | `/api/days/{id}/note` | 保存笔记 `{"note":"..."}` |
| GET | `/api/stats` | 总体统计 |
| GET | `/api/checkins` | 打卡记录 |
| POST | `/api/checkins` | 新增打卡 |

Swagger 文档：`http://localhost:8000/docs`

---

## 功能

- **📊 进度追踪** — 点击复选框标记完成，自动计算各阶段/总体进度
- **📝 学习笔记** — 每页底部有笔记输入区，自动保存到数据库
- **📖 富文本教程** — 92 天详细指南，支持代码块、Java 对照卡、列表
- **💾 数据持久化** — 进度+笔记存 SQLite，文件在 `roadmap.db`，想备份 Copy 走就行
- **✨ 花里胡哨** — 纸屑特效、进度条流光、3D 卡片、Header 浮动粒子、CSS 小鸟、白色手套光标

---

## 浏览器支持

Chrome / Edge / Firefox / Safari。
