"""
checkins.py — 打卡记录路由
===========================
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models import Checkin, Day, Progress
from schemas import CheckinCreate, CheckinOut, ApiResult
from datetime import datetime, timezone

router = APIRouter(prefix="/api", tags=["打卡记录"])


@router.get("/checkins", response_model=ApiResult)
async def list_checkins(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    打卡记录列表（按时间倒序）。
    """
    total_r = await db.execute(select(func.count(Checkin.id)))
    total = total_r.scalar()

    result = await db.execute(
        select(Checkin, Day.topic)
        .join(Day, Checkin.day_id == Day.id)
        .order_by(Checkin.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = result.all()

    data = []
    for ch, topic in rows:
        data.append(CheckinOut(
            id=ch.id, day_id=ch.day_id, date=ch.date,
            hours=float(ch.hours), note=ch.note or "",
            day_topic=topic,
        ).model_dump())

    return ApiResult(data={"total": total, "page": page, "list": data})


@router.post("/checkins", response_model=ApiResult)
async def create_checkin(body: CheckinCreate, db: AsyncSession = Depends(get_db)):
    """
    手动新增一条打卡记录。
    """
    day = await db.get(Day, body.day_id)
    if not day:
        raise HTTPException(404, "学习日不存在")

    ch = Checkin(
        day_id=body.day_id,
        date=body.date,
        hours=body.hours,
        note=body.note,
    )
    db.add(ch)

    # 同时更新 Progress
    result = await db.execute(
        select(Progress).where(Progress.day_id == body.day_id)
    )
    prog = result.scalar_one_or_none()
    if not prog:
        prog = Progress(day_id=body.day_id, done=True, hours=body.hours,
                        checked_at=datetime.now(timezone.utc))
        db.add(prog)
    else:
        prog.done = True
        prog.hours = body.hours
        prog.checked_at = datetime.now(timezone.utc)

    await db.commit()
    return ApiResult(msg="打卡成功", data={"id": ch.id})
