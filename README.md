# 📋 学习路线图

6 个月 · 92 天 · 每天 3 小时

Python + FastAPI + SQLite 全栈应用，包含学习端和后台管理端，浏览器打开即用。

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

然后打开浏览器：

- 学习端：`http://localhost:8000/static/ai-learning-roadmap.html`
- 管理端：`http://localhost:8000/static/admin.html`

管理端默认账号为 `admin`，密码为 `admin123`；首次启动时自动创建，仅用于本地开发。

> **不需要**装 PostgreSQL 或 Docker——数据存在本地 SQLite 文件 `roadmap.db`。
> seed.py 首次运行会自动从 HTML 里解析 92 天学习内容并入库。

---

## 项目结构

```
python/crud-project/
├── main.py              # FastAPI 启动入口 + 静态文件挂载 + 默认管理员初始化
├── config.py            # 数据库连接串（切数据库只改这里）
├── database.py          # 异步 + 同步双引擎（SQLAlchemy 2.0）
├── models.py            # ORM 模型：学习内容、进度、资源和管理员会话
├── schemas.py           # Pydantic 请求/响应模型
├── seed.py              # 数据初始化脚本（从 HTML 解析 92 天 -> 入库）
├── docker-compose.yml   # PostgreSQL（可选，默认用 SQLite）
├── requirements.txt     # Python 依赖
├── roadmap.db           # SQLite 数据库文件（自动生成）
├── routers/
│   ├── phases.py        # /api/phases, /api/days/{id}, /api/stats
│   ├── checkins.py      # /api/checkins
│   └── auth.py          # /api/admin 登录、会话校验和退出
└── static/
    ├── ai-learning-roadmap.html  # 学习端页面（调 API 渲染，不存数据）
    └── admin.html                # 后台管理页面
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
| PUT / DELETE | `/api/checkins/{id}` | 编辑 / 删除打卡 |
| POST | `/api/admin/login` | 管理员登录 |
| GET | `/api/admin/me` | 获取当前管理员 |
| POST | `/api/admin/logout` | 退出登录 |
| POST | `/api/phases` | 新增阶段（需登录） |
| PUT / DELETE | `/api/phases/{id}` | 编辑 / 删除阶段（需登录） |
| POST | `/api/phases/{id}/weeks` | 新增周（需登录） |
| PUT / DELETE | `/api/weeks/{id}` | 编辑 / 删除周（需登录） |
| POST | `/api/weeks/{id}/days` | 新增学习日（需登录） |
| PUT / DELETE | `/api/days/{id}` | 编辑 / 删除学习日（需登录） |

Swagger 文档：`http://localhost:8000/docs`

阶段、周和学习日的管理接口使用登录返回的 Bearer Token，有效期 24 小时。

---

## 后台管理

- **内容管理** — 按“阶段 → 周 → 学习日”维护学习路线；阶段支持描述、建议和资源，学习日支持 Markdown 内容
- **打卡管理** — 分页查看、新增、编辑和删除打卡记录
- **统计概览** — 查看总学习日、完成进度、计划/完成学时和连续打卡天数
- **登录会话** — Token 保存在浏览器本地，退出后立即失效

> 默认管理员凭据仅适合本地学习环境，请勿直接将管理端暴露到公网。

---

## 功能

- **📊 进度追踪** — 点击复选框标记完成，自动计算各阶段/总体进度
- **📝 学习笔记** — 每页底部有笔记输入区，自动保存到数据库
- **📖 富文本教程** — 92 天详细指南，支持代码块、Java 对照卡、列表
- **🛠️ 后台管理** — 在线维护阶段、周、学习日、资源和打卡记录
- **💾 数据持久化** — 进度+笔记存 SQLite，文件在 `roadmap.db`，想备份 Copy 走就行
- **✨ 花里胡哨** — 纸屑特效、进度条流光、3D 卡片、Header 浮动粒子、CSS 小鸟、白色手套光标

---

## 浏览器支持

Chrome / Edge / Firefox / Safari。
