"""
phases.py — 阶段/周/天/进度 路由
==================================
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from database import get_db
from models import Phase, Week, Day, Progress, Checkin
from schemas import (
    WeekOut, DayListItem, DayDetail, DayFullOut, WeekFullOut,
    PhaseFullOut, DoneToggle, NoteUpdate,
    StatsOut, ApiResult,
)
from datetime import datetime, timezone, date, timedelta

router = APIRouter(prefix="/api", tags=["学习路线图"])


# ── 工具函数 ──────────────────────────────────────────────

async def get_day_done_counts(db: AsyncSession):
    """一次性查出所有 Day 的完成状态，避免 N+1 查询"""
    result = await db.execute(
        select(Progress.day_id, Progress.done)
        .where(Progress.done == True)
    )
    return {row[0]: row[1] for row in result.all()}


# ============================================================
# Phase
# ============================================================

@router.get("/phases", response_model=ApiResult)
async def list_phases(db: AsyncSession = Depends(get_db)):
    """
    获取所有阶段及其嵌套的周、天、进度和笔记。
    前端一次性加载全部数据，减少请求次数。
    """
    # 一次性查出所有 Day 的 Progress（done + note）
    result = await db.execute(
        select(Progress.day_id, Progress.done, Progress.note, Progress.checked_at)
    )
    progress_map = {row[0]: row for row in result.all()}

    result = await db.execute(
        select(Phase).options(
            selectinload(Phase.weeks).selectinload(Week.days),
            selectinload(Phase.tips),
        ).order_by(Phase.sort_order)
    )
    phases = result.scalars().all()

    out = []
    for p in phases:
        td, dd = 0, 0
        weeks = []
        for w in p.weeks:
            w_td, w_dd = 0, 0
            days = []
            for d in w.days:
                td += 1; w_td += 1
                prog = progress_map.get(d.id)
                done = prog[1] if prog else False
                note = prog[2] or "" if prog else ""
                checked_at = prog[3] if prog else None
                if done: dd += 1; w_dd += 1
                days.append(DayFullOut(
                    id=d.id, topic=d.topic, hours=float(d.hours),
                    resource=d.resource, detail=d.detail,
                    done=done, note=note, checked_at=checked_at,
                ))
            weeks.append(WeekFullOut(
                id=w.id, title=w.title, week_num=w.week_num, days=days,
            ))
        out.append(PhaseFullOut(
            id=p.id, title=p.title, period=p.period, desc=p.desc, color=p.color,
            total_days=td, done_days=dd,
            tips=[t.text for t in p.tips] if p.tips else [],
            weeks=weeks,
        ))
    return ApiResult(data=[o.model_dump() for o in out])


@router.get("/phases/{phase_id}/weeks", response_model=ApiResult)
async def get_weeks(phase_id: int, db: AsyncSession = Depends(get_db)):
    """
    获取某阶段的周列表（含每天完成状态）。
    """
    done_map = await get_day_done_counts(db)

    phase = await db.get(Phase, phase_id, options=[
        selectinload(Phase.weeks).selectinload(Week.days),
    ])
    if not phase:
        raise HTTPException(404, "阶段不存在")

    weeks = []
    for w in phase.weeks:
        td, dd = 0, 0
        for d in w.days:
            td += 1
            if done_map.get(d.id):
                dd += 1
        weeks.append(WeekOut(id=w.id, title=w.title, week_num=w.week_num,
                             weeks_large=w.weeks_large or False,
                             total_days=td, done_days=dd))
    return ApiResult(data=[w.model_dump() for w in weeks])


# ============================================================
# Day
# ============================================================

@router.get("/weeks/{week_id}/days", response_model=ApiResult)
async def get_days(week_id: int, db: AsyncSession = Depends(get_db)):
    """
    获取某周的所有学习日（列表形式）。
    """
    done_map = await get_day_done_counts(db)

    result = await db.execute(
        select(Week)
        .options(selectinload(Week.days))
        .where(Week.id == week_id)
    )
    week = result.scalar_one_or_none()
    if not week:
        raise HTTPException(404, "周不存在")

    days = []
    for d in week.days:
        days.append(DayListItem(
            id=d.id, topic=d.topic, hours=float(d.hours),
            resource=d.resource, done=done_map.get(d.id, False),
        ))
    return ApiResult(data=[d.model_dump() for d in days])


@router.get("/days/{day_id}", response_model=ApiResult)
async def get_day_detail(day_id: int, db: AsyncSession = Depends(get_db)):
    """
    获取某天的完整详情（含富文本 detail + 进度 + 笔记）。

    这是前端展开卡片时调用的接口。
    """
    result = await db.execute(
        select(Day, Progress)
        .outerjoin(Progress, Progress.day_id == Day.id)
        .where(Day.id == day_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(404, "学习日不存在")

    day, prog = row
    return ApiResult(data=DayDetail(
        id=day.id, topic=day.topic, hours=float(day.hours),
        resource=day.resource, detail=day.detail,
        done=prog.done if prog else False,
        note=prog.note or "" if prog else "",
        checked_at=prog.checked_at if prog else None,
    ).model_dump())


# ============================================================
# Progress — 标记完成 + 笔记
# ============================================================

@router.put("/days/{day_id}/done", response_model=ApiResult)
async def toggle_done(day_id: int, body: DoneToggle, db: AsyncSession = Depends(get_db)):
    """
    标记某天为完成/取消。

    请求: {"done": true}
    """
    # 检查 day 存在
    day = await db.get(Day, day_id)
    if not day:
        raise HTTPException(404, "学习日不存在")

    # 查或建 Progress
    result = await db.execute(
        select(Progress).where(Progress.day_id == day_id)
    )
    prog = result.scalar_one_or_none()
    if not prog:
        prog = Progress(day_id=day_id)
        db.add(prog)

    prog.done = body.done
    if body.done:
        prog.checked_at = datetime.now(timezone.utc)
        if not prog.hours:
            prog.hours = day.hours or 3
        # 自动生成一条打卡记录
        ch = Checkin(
            day_id=day_id,
            date=datetime.now(timezone.utc).date(),
            hours=prog.hours,
        )
        db.add(ch)
    else:
        prog.checked_at = None

    await db.commit()
    return ApiResult(msg="已完成" if body.done else "已取消")


@router.put("/days/{day_id}/note", response_model=ApiResult)
async def save_note(day_id: int, body: NoteUpdate, db: AsyncSession = Depends(get_db)):
    """
    保存某天的学习笔记。

    请求: {"note": "今天学了列表推导式..."}
    """
    day = await db.get(Day, day_id)
    if not day:
        raise HTTPException(404, "学习日不存在")

    result = await db.execute(
        select(Progress).where(Progress.day_id == day_id)
    )
    prog = result.scalar_one_or_none()
    if not prog:
        prog = Progress(day_id=day_id, note=body.note)
        db.add(prog)
    else:
        prog.note = body.note

    await db.commit()
    return ApiResult(msg="笔记已保存")


# ============================================================
# Stats
# ============================================================

@router.get("/stats", response_model=ApiResult)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """
    总体统计：完成天数、总天数、连续打卡、累计学时。

    前端进度卡片用这个接口。
    """
    # 总天数
    total_r = await db.execute(select(func.count(Day.id)))
    total_days = total_r.scalar()

    # 已完成天数 + 累计学时
    done_r = await db.execute(
        select(func.count(Progress.id), func.coalesce(func.sum(Progress.hours), 0))
        .where(Progress.done == True)
    )
    row = done_r.first()
    done_days = row[0]
    done_hours = float(row[1])

    # 计划总学时
    plan_r = await db.execute(select(func.coalesce(func.sum(Day.hours), 0)))
    total_planned = float(plan_r.scalar())

    # 连续打卡（按日期倒序查打卡记录）
    ch_r = await db.execute(
        select(Checkin.date)
        .order_by(Checkin.date.desc())
        .distinct()
    )
    dates = [row[0] for row in ch_r.all()]
    streak = 0
    from datetime import date
    today = date.today()
    for i, dt in enumerate(dates):
        if dt == today:
            today = date.fromisoformat(str(dt))
            from datetime import timedelta
            check_day = today - timedelta(days=i)
            from datetime import date as d2
            if date.fromisoformat(str(dt)) == check_day:
                streak += 1
            else:
                break
        else:
            streak = 1 if dates else 0
            break

    pct = round(done_days / total_days * 100) if total_days else 0

    return ApiResult(data=StatsOut(
        total_days=total_days,
        done_days=done_days,
        total_planned_hours=total_planned,
        done_hours=done_hours,
        streak_days=streak,
        progress_pct=pct,
    ).model_dump())
