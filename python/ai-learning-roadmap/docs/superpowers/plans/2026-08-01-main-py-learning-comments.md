# Python Source Learning Comments Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为项目全部非空 Python 源码的有效逻辑行补充面向初学者的中文学习注释，同时保持运行行为完全不变。

**Architecture:** 只修改现有 Python 文件的注释层，不重排或重写可执行语句。按配置与数据库、模型与 Schema、路由、数据导入四组处理，使用编译检查、AST 等价、纯新增行 diff 和 UTF-8 解码检查证明行为没有改变。

**Tech Stack:** Python 3、FastAPI、Uvicorn

---

### Task 1: 为入口文件补充逐行学习注释

**Files:**
- Modify: `main.py:7-35`
- Test: no new test file; comments have no runtime branch, use compiler and diff checks

- [ ] **Step 1: 保留原始可执行行并加入中文解释**

将 `main.py` 更新为以下内容：

```python
"""
main.py — 学习路线图后台服务入口
==================================
启动: python -m uvicorn main:app --reload --port 8000
文档: http://localhost:8000/docs
"""
# 从 FastAPI 包导入应用类，用它创建整个 Web 服务。
from fastapi import FastAPI
# 导入静态文件服务，让浏览器能够访问 static 目录中的 HTML、CSS 和 JavaScript。
from fastapi.staticfiles import StaticFiles
# 导入跨域中间件，控制其他网站能否调用本项目的接口。
from fastapi.middleware.cors import CORSMiddleware
# 导入学习路线相关路由，并改名，避免与其他 router 变量重名。
from routers.phases import router as phases_router
# 导入打卡记录相关路由，同样给 router 设置清晰的别名。
from routers.checkins import router as checkins_router

# 创建 FastAPI 应用对象；Uvicorn 启动时寻找的 app 就是这个变量。
app = FastAPI(
    # 接口文档页面显示的项目标题。
    title="📋 学习路线图 API",
    # 接口文档页面显示的项目说明。
    description="FastAPI + PostgreSQL 全栈后台",
    # 当前 API 版本号。
    version="2.0.0",
)

# 给应用添加 CORS 中间件；中间件会在请求到达路由前统一处理跨域规则。
app.add_middleware(
    # 指定要添加的中间件类型。
    CORSMiddleware,
    # "*" 表示允许任意来源的网站访问接口。
    allow_origins=["*"],
    # "*" 表示允许 GET、POST、PUT 等所有 HTTP 方法。
    allow_methods=["*"],
    # "*" 表示允许请求携带任意 HTTP 请求头。
    allow_headers=["*"],
)

# 把阶段、周、天、进度相关接口注册到主应用。
app.include_router(phases_router)
# 把打卡记录相关接口注册到主应用。
app.include_router(checkins_router)


# 将本地 static 目录挂载到 /static URL，name 用于框架内部标识这组静态资源。
app.mount("/static", StaticFiles(directory="static"), name="static")


# 只有直接执行 python main.py 时该条件才成立；被 Uvicorn 导入时不会重复启动。
if __name__ == "__main__":
    # 延迟导入 Uvicorn，使正常导入 main:app 时只创建应用对象。
    import uvicorn
    # 启动开发服务器：监听所有网卡的 8000 端口，并在源码变化时自动重载。
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

- [ ] **Step 2: 验证 Python 语法**

Run:

```powershell
python -m py_compile main.py
```

Expected: exit code `0`，没有错误输出。

- [ ] **Step 3: 验证只增加注释**

Run:

```powershell
git diff --word-diff=porcelain -- main.py
```

Expected: 原有 Python 可执行行没有删除或替换，新增内容全部以 `#` 开头。

- [ ] **Step 4: 验证 UTF-8 和原始中文**

Run:

```powershell
python -c "from pathlib import Path; t=Path('main.py').read_text(encoding='utf-8'); assert '学习路线图后台服务入口' in t and '📋 学习路线图 API' in t; print('UTF-8: OK')"
```

Expected: `UTF-8: OK`。

- [ ] **Step 5: 保留为未提交改动**

不执行 `git commit`；用户没有要求提交，最终仅报告修改文件和验证结果。

### Task 2: 注释配置、数据库和 ORM 模型

**Files:**
- Modify: `config.py:7-19`
- Modify: `database.py:7-30`
- Modify: `models.py:8-104`

- [ ] **Step 1: 注释配置和会话创建流程**

逐行解释环境变量、异步与同步数据库 URL、引擎、Session 工厂、声明式基类和 `yield` 依赖。只增加 `#` 注释。

- [ ] **Step 2: 注释 ORM 表和关系**

逐行解释 `__tablename__`、Column 类型、主键、外键、约束、默认值和 `relationship`。只增加 `#` 注释。

- [ ] **Step 3: 编译本组文件**

Run: `python -m py_compile config.py database.py models.py`

Expected: exit code `0`。

### Task 3: 注释 Pydantic Schema

**Files:**
- Modify: `schemas.py:5-135`

- [ ] **Step 1: 注释导入、配置、字段类型和各请求/响应模型**

逐行解释 `BaseModel`、`ConfigDict`、类型标注、`Optional`、列表、默认值和通用响应包装。只增加 `#` 注释。

- [ ] **Step 2: 编译 Schema**

Run: `python -m py_compile schemas.py`

Expected: exit code `0`。

### Task 4: 注释 API 路由和查询流程

**Files:**
- Modify: `routers/phases.py:5-298`
- Modify: `routers/checkins.py:5-78`

- [ ] **Step 1: 注释路由声明、依赖注入、SQLAlchemy 查询和响应拼装**

逐行解释装饰器、路径参数、查询参数、`Depends`、`select`、异步执行、结果提取、循环聚合、事务提交和 HTTP 404。只增加 `#` 注释。

- [ ] **Step 2: 编译路由**

Run: `python -m py_compile routers/phases.py routers/checkins.py`

Expected: exit code `0`。

### Task 5: 注释数据导入脚本并做全量验证

**Files:**
- Modify: `seed.py:8-106`
- Verify: `main.py`, `config.py`, `database.py`, `models.py`, `schemas.py`, `seed.py`, `routers/phases.py`, `routers/checkins.py`

- [ ] **Step 1: 注释 HTML 解析、Node 子进程、建表、清表和批量写入流程**

逐行解释标准库导入、路径定位、临时脚本、异常处理、Session 上下文、外键写入和事务提交。只增加 `#` 注释。

- [ ] **Step 2: 验证所有目标文件**

Run: `python -m py_compile main.py config.py database.py models.py schemas.py seed.py routers/phases.py routers/checkins.py`

Expected: exit code `0`；AST 与 Git 基线一致；diff 中没有删除行且所有新增行均以 `#` 开头；UTF-8 中文检查通过。
