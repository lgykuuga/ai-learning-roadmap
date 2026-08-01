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
