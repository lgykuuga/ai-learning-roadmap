"""
checkins.py — 打卡记录路由
===========================
"""
# 导入路由类、依赖注入、HTTP 异常和查询参数校验工具。
from fastapi import APIRouter, Depends, HTTPException, Query
# 导入异步数据库 Session 类型，用于路由参数类型标注。
from sqlalchemy.ext.asyncio import AsyncSession
# select 构造查询语句，func 调用 count 等数据库函数。
from sqlalchemy import select, func
# get_db 为每次请求提供数据库 Session。
from database import get_db
# 导入本文件需要查询或写入的 ORM 模型。
from models import Checkin, Day, Progress
# 导入请求、响应和通用结果 Schema。
from schemas import CheckinCreate, CheckinOut, ApiResult
# datetime 生成当前时间，timezone.utc 提供明确的 UTC 时区。
from datetime import datetime, timezone

# 创建打卡路由组；这里定义的所有路径都会自动带上 /api 前缀。
router = APIRouter(prefix="/api", tags=["打卡记录"])


# 装饰器把下面的函数注册为 GET /api/checkins，并声明统一响应模型。
@router.get("/checkins", response_model=ApiResult)
# async def 定义异步路由函数，请求到达时由 FastAPI 调用。
async def list_checkins(
    # Query(1, ge=1) 表示 page 默认 1，并且必须大于等于 1。
    page: int = Query(1, ge=1),
    # page_size 默认 20，限制在 1 到 100 之间。
    page_size: int = Query(20, ge=1, le=100),
    # Depends(get_db) 自动取得本次请求使用的异步 Session。
    db: AsyncSession = Depends(get_db),
):
    """
    打卡记录列表（按时间倒序）。
    """
    # 构造统计 checkins 表总记录数的 SQL，并异步执行。
    total_r = await db.execute(select(func.count(Checkin.id)))
    # scalar() 取查询结果第一行第一列，也就是总记录数。
    total = total_r.scalar()

    # 构造打卡分页查询，同时关联 Day 表取得学习主题。
    result = await db.execute(
        # 一行结果包含 Checkin ORM 对象和 Day.topic 字符串。
        select(Checkin, Day.topic)
        # 按 day_id 连接 Day 表。
        .join(Day, Checkin.day_id == Day.id)
        # 创建时间越新的记录排在越前面。
        .order_by(Checkin.created_at.desc())
        # offset 跳过前面页已经展示的记录。
        .offset((page - 1) * page_size)
        # limit 限制本页最多返回 page_size 条。
        .limit(page_size)
    )
    # all() 把查询结果转换为可遍历的行列表。
    rows = result.all()

    # 准备最终返回给前端的打卡字典列表。
    data = []
    # 每行按查询列顺序解包为打卡对象和学习主题。
    for ch, topic in rows:
        # 先用 CheckinOut 校验和格式化数据，再转成普通字典加入列表。
        data.append(CheckinOut(
            # ORM 的 Numeric 需要显式转成 JSON 更友好的 float。
            id=ch.id, day_id=ch.day_id, date=ch.date,
            hours=float(ch.hours), note=ch.note or "",
            # topic 来自上面的 Day 表连接查询。
            day_topic=topic,
        ).model_dump())

    # data 中同时返回总数、当前页和本页记录，外层再用 ApiResult 统一包装。
    return ApiResult(data={"total": total, "page": page, "list": data})


# 装饰器把下面的函数注册为 POST /api/checkins。
@router.post("/checkins", response_model=ApiResult)
# body 会由 FastAPI 根据 CheckinCreate 自动解析和校验。
async def create_checkin(body: CheckinCreate, db: AsyncSession = Depends(get_db)):
    """
    手动新增一条打卡记录。
    """
    # 按主键查询要打卡的 Day；db.get 是主键查询的快捷方式。
    day = await db.get(Day, body.day_id)
    # 如果学习日不存在，立即返回 HTTP 404，避免写入无效外键。
    if not day:
        # 抛出 HTTPException 后，FastAPI 会生成对应的错误响应。
        raise HTTPException(404, "学习日不存在")

    # 根据已经校验的请求体创建新的 Checkin ORM 对象。
    ch = Checkin(
        # 将请求字段逐项写入数据库模型。
        day_id=body.day_id,
        date=body.date,
        hours=body.hours,
        note=body.note,
    )
    # add 只是把对象加入当前事务，真正写库要等 flush 或 commit。
    db.add(ch)

    # 同时更新 Progress
    # 查询这个学习日是否已经有一对一的进度记录。
    result = await db.execute(
        select(Progress).where(Progress.day_id == body.day_id)
    )
    # scalar_one_or_none() 要么返回唯一对象，要么返回 None。
    prog = result.scalar_one_or_none()
    # 没有进度记录时创建一条，并直接标记完成。
    if not prog:
        prog = Progress(day_id=body.day_id, done=True, hours=body.hours,
                        checked_at=datetime.now(timezone.utc))
        # 新建的 Progress 也加入当前事务。
        db.add(prog)
    # 已有进度记录时直接更新其字段。
    else:
        # 手动打卡意味着该学习日已经完成。
        prog.done = True
        # 使用本次打卡提交的学习时长覆盖进度时长。
        prog.hours = body.hours
        # 记录本次更新的 UTC 时间。
        prog.checked_at = datetime.now(timezone.utc)

    # 一次提交同时保存 Checkin 和 Progress，保持两者状态一致。
    await db.commit()
    # 提交后返回新打卡记录的主键。
    return ApiResult(msg="打卡成功", data={"id": ch.id})
