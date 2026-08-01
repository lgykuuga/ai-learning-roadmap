"""
main.py — 学习路线图后台服务入口
==================================
启动: python -m uvicorn main:app --reload --port 8000
文档: http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from routers.phases import router as phases_router
from routers.checkins import router as checkins_router

app = FastAPI(
    title="📋 学习路线图 API",
    description="FastAPI + PostgreSQL 全栈后台",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(phases_router)
app.include_router(checkins_router)


app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
