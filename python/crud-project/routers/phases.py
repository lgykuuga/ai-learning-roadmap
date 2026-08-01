"""
phases.py — 阶段/周/天/进度 路由
==================================
"""
# 导入路由类、依赖注入工具和 HTTP 异常类型。
from fastapi import APIRouter, Depends, HTTPException
# 导入异步数据库 Session 类型。
from sqlalchemy.ext.asyncio import AsyncSession
# select 用来构造查询，func 用来调用 count、sum 等数据库函数。
from sqlalchemy import select, func
# selectinload 用额外的批量查询提前加载 ORM 关联，避免逐条懒加载。
from sqlalchemy.orm import selectinload
# get_db 为每个接口请求提供数据库 Session。
from database import get_db
# 导入路线、进度和打卡相关的 ORM 模型。
from models import Phase, Week, Day, Progress, Checkin
# 导入本文件用于校验和格式化响应的 Pydantic Schema。
from schemas import (
    # 列表和详情响应模型。
    WeekOut, DayListItem, DayDetail, DayFullOut, WeekFullOut,
    # 完整阶段树、完成状态请求和笔记请求模型。
    PhaseFullOut, DoneToggle, NoteUpdate,
    # 统计响应和统一接口响应模型。
    StatsOut, ApiResult,
)
# 导入时间、日期和时间差工具；timezone.utc 用于生成带时区的当前时间。
from datetime import datetime, timezone, date, timedelta

# 创建学习路线图路由组；本文件中的路径统一带 /api 前缀。
router = APIRouter(prefix="/api", tags=["学习路线图"])


# ── 工具函数 ──────────────────────────────────────────────

# 定义可复用的异步查询函数，一次取得所有已完成学习日。
async def get_day_done_counts(db: AsyncSession):
    """一次性查出所有 Day 的完成状态，避免 N+1 查询"""
    # 查询已完成进度的 day_id 和 done 两列，不加载完整 ORM 对象。
    result = await db.execute(
        select(Progress.day_id, Progress.done)
        # 只保留 done 为 True 的记录。
        .where(Progress.done == True)
    )
    # 字典推导式把查询行转换成 {day_id: done}，后续可 O(1) 查状态。
    return {row[0]: row[1] for row in result.all()}


# ============================================================
# Phase
# ============================================================

# 把下面的函数注册为 GET /api/phases。
@router.get("/phases", response_model=ApiResult)
# FastAPI 通过 Depends(get_db) 自动提供异步 Session。
async def list_phases(db: AsyncSession = Depends(get_db)):
    """
    获取所有阶段及其嵌套的周、天、进度和笔记。
    前端一次性加载全部数据，减少请求次数。
    """
    # 一次性查出所有 Day 的 Progress（done + note）
    # 只查询组装响应需要的四列，避免加载不需要的字段。
    result = await db.execute(
        select(Progress.day_id, Progress.done, Progress.note, Progress.checked_at)
    )
    # 把每行按 day_id 建立索引，value 保留整行供后续读取其他列。
    progress_map = {row[0]: row for row in result.all()}

    # 查询所有阶段，并批量预加载关联的周、学习日和建议。
    result = await db.execute(
        select(Phase).options(
            # 第一条加载链：Phase.weeks，再从每个 Week 加载 Week.days。
            selectinload(Phase.weeks).selectinload(Week.days),
            # 第二条加载链：Phase.tips。
            selectinload(Phase.tips),
        # 阶段按 sort_order 排序。
        ).order_by(Phase.sort_order)
    )
    # scalars() 只取每行的 Phase 对象，all() 再收集为列表。
    phases = result.scalars().all()

    # out 用来保存最终的完整阶段响应对象。
    out = []
    # 逐个阶段组装 Phase → Week → Day 的嵌套结构。
    for p in phases:
        # td 是阶段总学习日数，dd 是阶段已完成学习日数。
        td, dd = 0, 0
        # 保存当前阶段组装后的周列表。
        weeks = []
        # 遍历当前阶段已经预加载的所有周。
        for w in p.weeks:
            # 分别统计当前周的总天数和完成天数。
            w_td, w_dd = 0, 0
            # 保存当前周组装后的学习日列表。
            days = []
            # 遍历当前周的每日学习内容。
            for d in w.days:
                # 同时累加阶段和当前周的总学习日数；分号允许一行写两条简单语句。
                td += 1; w_td += 1
                # 根据 Day.id 从进度字典中取得对应行，未创建进度时得到 None。
                prog = progress_map.get(d.id)
                # row[1] 是 done；没有进度记录时默认 False。
                done = prog[1] if prog else False
                # row[2] 是 note；数据库空值或没有记录时统一返回空字符串。
                note = prog[2] or "" if prog else ""
                # row[3] 是最后打卡时间；没有记录时返回 None。
                checked_at = prog[3] if prog else None
                # 已完成时同时累加阶段和当前周的完成数。
                if done: dd += 1; w_dd += 1
                # 创建完整学习日响应模型并追加到当前周。
                days.append(DayFullOut(
                    # 基础内容来自 Day ORM 对象。
                    id=d.id, topic=d.topic, hours=float(d.hours),
                    resource=d.resource, detail=d.detail,
                    # 用户状态来自前面查到的 Progress。
                    done=done, note=note, checked_at=checked_at,
                ))
            # 当前周的所有 Day 组装完成后，创建周响应并加入 weeks。
            weeks.append(WeekFullOut(
                id=w.id, title=w.title, week_num=w.week_num, days=days,
            ))
        # 当前阶段的所有 Week 组装完成后，创建完整阶段响应。
        out.append(PhaseFullOut(
            # 复制阶段基础字段和刚刚计算出的统计值。
            id=p.id, title=p.title, period=p.period, desc=p.desc, color=p.color,
            total_days=td, done_days=dd,
            # 把 Tip ORM 对象列表转换为纯文本列表；没有建议时返回空列表。
            tips=[t.text for t in p.tips] if p.tips else [],
            # 写入当前阶段的完整周树。
            weeks=weeks,
        ))
    # model_dump() 把每个 Pydantic 对象转成可 JSON 序列化的字典。
    return ApiResult(data=[o.model_dump() for o in out])


# 注册 GET /api/phases/{phase_id}/weeks；花括号部分会解析为路径参数。
@router.get("/phases/{phase_id}/weeks", response_model=ApiResult)
# phase_id: int 会让 FastAPI 自动校验路径参数必须能转成整数。
async def get_weeks(phase_id: int, db: AsyncSession = Depends(get_db)):
    """
    获取某阶段的周列表（含每天完成状态）。
    """
    # 先取得所有已完成学习日的字典，避免遍历每周时重复查询。
    done_map = await get_day_done_counts(db)

    # 按主键获取阶段，同时预加载该阶段的周和每天内容。
    phase = await db.get(Phase, phase_id, options=[
        selectinload(Phase.weeks).selectinload(Week.days),
    ])
    # db.get 没找到记录时返回 None，此时向调用方返回 404。
    if not phase:
        raise HTTPException(404, "阶段不存在")

    # 保存格式化后的周响应。
    weeks = []
    # 遍历当前阶段的所有周。
    for w in phase.weeks:
        # 初始化当前周总天数和完成天数。
        td, dd = 0, 0
        # 遍历当前周每天，计算统计值。
        for d in w.days:
            # 每发现一个 Day，总数加一。
            td += 1
            # done_map 中对应值为 True 时，完成数加一。
            if done_map.get(d.id):
                dd += 1
        # 用 ORM 基础字段和统计值创建 WeekOut。
        weeks.append(WeekOut(id=w.id, title=w.title, week_num=w.week_num,
                             # 数据库值可能为空，因此用 or False 统一为布尔值。
                             weeks_large=w.weeks_large or False,
                             total_days=td, done_days=dd))
    # 将周模型逐个转换为字典并用 ApiResult 包装。
    return ApiResult(data=[w.model_dump() for w in weeks])


# ============================================================
# Day
# ============================================================

# 注册 GET /api/weeks/{week_id}/days。
@router.get("/weeks/{week_id}/days", response_model=ApiResult)
# week_id 从 URL 读取，db 由依赖注入提供。
async def get_days(week_id: int, db: AsyncSession = Depends(get_db)):
    """
    获取某周的所有学习日（列表形式）。
    """
    # 预先取得完成状态字典。
    done_map = await get_day_done_counts(db)

    # 查询指定周并预加载其 Day 列表。
    result = await db.execute(
        select(Week)
        # selectinload 防止访问 week.days 时再逐条查询。
        .options(selectinload(Week.days))
        # where 添加 SQL WHERE weeks.id = :week_id 条件。
        .where(Week.id == week_id)
    )
    # 期望最多一行；没有结果时返回 None。
    week = result.scalar_one_or_none()
    # 周不存在时返回 HTTP 404。
    if not week:
        raise HTTPException(404, "周不存在")

    # 保存精简的学习日响应列表。
    days = []
    # 遍历已经预加载并按模型关系配置排序的 Day。
    for d in week.days:
        # 创建列表项，Numeric 学时转成 float，完成状态从字典读取。
        days.append(DayListItem(
            id=d.id, topic=d.topic, hours=float(d.hours),
            resource=d.resource, done=done_map.get(d.id, False),
        ))
    # 将 Pydantic 对象转换为字典列表后返回。
    return ApiResult(data=[d.model_dump() for d in days])


# 注册 GET /api/days/{day_id}，用于读取单日详情。
@router.get("/days/{day_id}", response_model=ApiResult)
# day_id 由 URL 提供，Session 由 get_db 提供。
async def get_day_detail(day_id: int, db: AsyncSession = Depends(get_db)):
    """
    获取某天的完整详情（含富文本 detail + 进度 + 笔记）。

    这是前端展开卡片时调用的接口。
    """
    # 同时查询 Day 和可能存在的 Progress。
    result = await db.execute(
        select(Day, Progress)
        # outerjoin 保留没有进度记录的 Day；此时 Progress 部分为 None。
        .outerjoin(Progress, Progress.day_id == Day.id)
        # 只查询 URL 指定的学习日。
        .where(Day.id == day_id)
    )
    # first() 取得第一行；没有结果时返回 None。
    row = result.first()
    # 学习日不存在时返回 HTTP 404。
    if not row:
        raise HTTPException(404, "学习日不存在")

    # 查询列顺序是 Day、Progress，因此可以直接解包。
    day, prog = row
    # 创建详情响应；Progress 不存在时为状态字段提供默认值。
    return ApiResult(data=DayDetail(
        # 复制 Day 的基础内容。
        id=day.id, topic=day.topic, hours=float(day.hours),
        resource=day.resource, detail=day.detail,
        # 三元表达式根据 prog 是否存在选择真实值或默认值。
        done=prog.done if prog else False,
        note=prog.note or "" if prog else "",
        checked_at=prog.checked_at if prog else None,
    # 先把 DayDetail 转成字典，再放入通用响应的 data。
    ).model_dump())


# ============================================================
# Progress — 标记完成 + 笔记
# ============================================================

# 注册 PUT /api/days/{day_id}/done，用于设置完成状态。
@router.put("/days/{day_id}/done", response_model=ApiResult)
# body 根据 DoneToggle 校验 JSON，请求示例为 {"done": true}。
async def toggle_done(day_id: int, body: DoneToggle, db: AsyncSession = Depends(get_db)):
    """
    标记某天为完成/取消。

    请求: {"done": true}
    """
    # 检查 day 存在
    # 按主键读取学习日，防止为不存在的 day_id 创建进度。
    day = await db.get(Day, day_id)
    # 找不到时返回 HTTP 404。
    if not day:
        raise HTTPException(404, "学习日不存在")

    # 查或建 Progress
    # 查询该学习日已有的一对一进度记录。
    result = await db.execute(
        select(Progress).where(Progress.day_id == day_id)
    )
    # 没有记录时得到 None。
    prog = result.scalar_one_or_none()
    # 首次修改这个学习日时创建 Progress。
    if not prog:
        # 此处先只设置外键，其他字段使用模型默认值或随后赋值。
        prog = Progress(day_id=day_id)
        # 把新对象加入当前事务。
        db.add(prog)

    # 无论记录是新建还是已有，都更新成请求指定的状态。
    prog.done = body.done
    # 设置为完成时，同时补充完成时间、时长和一条打卡历史。
    if body.done:
        # 记录当前 UTC 时间作为最后打卡时间。
        prog.checked_at = datetime.now(timezone.utc)
        # 进度还没有实际学时时，使用 Day 的计划学时或兜底值 3。
        if not prog.hours:
            prog.hours = day.hours or 3
        # 自动生成一条打卡记录
        # 每次设置为完成都会构造一条新的 Checkin 历史记录。
        ch = Checkin(
            # 关联当前学习日。
            day_id=day_id,
            # 只取当前 UTC 时间中的日期部分。
            date=datetime.now(timezone.utc).date(),
            # 打卡时长沿用 Progress 中的实际学时。
            hours=prog.hours,
        )
        # 将新打卡加入同一事务。
        db.add(ch)
    # 取消完成时不删除历史打卡，只清空当前完成时间。
    else:
        prog.checked_at = None

    # 一次提交保存 Progress 修改以及可能新增的 Checkin。
    await db.commit()
    # 根据目标状态返回不同提示文本。
    return ApiResult(msg="已完成" if body.done else "已取消")


# 注册 PUT /api/days/{day_id}/note，用于保存学习笔记。
@router.put("/days/{day_id}/note", response_model=ApiResult)
# body 根据 NoteUpdate 校验，确保请求中存在字符串 note。
async def save_note(day_id: int, body: NoteUpdate, db: AsyncSession = Depends(get_db)):
    """
    保存某天的学习笔记。

    请求: {"note": "今天学了列表推导式..."}
    """
    # 先验证学习日存在。
    day = await db.get(Day, day_id)
    # 不存在时返回 HTTP 404。
    if not day:
        raise HTTPException(404, "学习日不存在")

    # 查询已有的 Progress，因为笔记保存在 progress 表中。
    result = await db.execute(
        select(Progress).where(Progress.day_id == day_id)
    )
    # 取得唯一进度对象或 None。
    prog = result.scalar_one_or_none()
    # 第一次保存该学习日状态时，新建 Progress 并直接写入笔记。
    if not prog:
        prog = Progress(day_id=day_id, note=body.note)
        # 新对象加入当前事务。
        db.add(prog)
    # 已有记录时只更新 note，不影响完成状态和学时。
    else:
        prog.note = body.note

    # 提交事务，将笔记持久化到数据库。
    await db.commit()
    # 返回统一成功响应，不额外返回数据。
    return ApiResult(msg="笔记已保存")


# ============================================================
# Stats
# ============================================================

# 注册 GET /api/stats，用于读取整体进度统计。
@router.get("/stats", response_model=ApiResult)
# 统计接口只有数据库依赖，没有路径参数或请求体。
async def get_stats(db: AsyncSession = Depends(get_db)):
    """
    总体统计：完成天数、总天数、连续打卡、累计学时。

    前端进度卡片用这个接口。
    """
    # 总天数
    # count(Day.id) 让数据库直接计算 days 表记录数。
    total_r = await db.execute(select(func.count(Day.id)))
    # 取得总学习日数。
    total_days = total_r.scalar()

    # 已完成天数 + 累计学时
    # 一次聚合查询同时计算已完成记录数和实际学时总和。
    done_r = await db.execute(
        # coalesce(..., 0) 保证没有记录时 sum 返回 0 而不是 None。
        select(func.count(Progress.id), func.coalesce(func.sum(Progress.hours), 0))
        # 只统计完成状态为 True 的 Progress。
        .where(Progress.done == True)
    )
    # first() 返回包含 count 和 sum 的一行。
    row = done_r.first()
    # 第一列是已完成天数。
    done_days = row[0]
    # 第二列可能是 Decimal，转成 float 方便响应序列化。
    done_hours = float(row[1])

    # 计划总学时
    # 汇总所有 Day.hours，并用 coalesce 处理空表。
    plan_r = await db.execute(select(func.coalesce(func.sum(Day.hours), 0)))
    # 取聚合值并转成 float。
    total_planned = float(plan_r.scalar())

    # 连续打卡（按日期倒序查打卡记录）
    # 查询去重后的打卡日期，并从最近日期开始排列。
    ch_r = await db.execute(
        select(Checkin.date)
        .order_by(Checkin.date.desc())
        .distinct()
    )
    # 只取每行第一列，得到日期列表。
    dates = [row[0] for row in ch_r.all()]
    # streak 保存连续打卡天数，初始为 0。
    streak = 0
    # 在函数内部再次导入 date；它与文件顶部导入的是同一个类型。
    from datetime import date
    # 获取服务器本地时区的今天日期。
    today = date.today()
    # enumerate 同时提供日期在倒序列表中的下标和日期值。
    for i, dt in enumerate(dates):
        # 当前实现先判断本次遍历日期是否等于 today 变量。
        if dt == today:
            # 将数据库日期经字符串重新转换成 date 对象。
            today = date.fromisoformat(str(dt))
            # timedelta 用来向前推算应该连续出现的日期。
            from datetime import timedelta
            # 根据下标 i 计算本轮期望日期。
            check_day = today - timedelta(days=i)
            # 给 date 类型设置另一个局部别名 d2；当前后续代码没有使用这个别名。
            from datetime import date as d2
            # 实际打卡日期等于期望日期时，连续天数加一。
            if date.fromisoformat(str(dt)) == check_day:
                streak += 1
            # 出现日期间隔时结束循环。
            else:
                break
        # 第一条记录不是今天时，当前实现将有记录的 streak 设置为 1 后停止。
        else:
            streak = 1 if dates else 0
            break

    # 用完成数除以总数得到整数百分比；总数为 0 时避免除零并返回 0。
    pct = round(done_days / total_days * 100) if total_days else 0

    # 用 StatsOut 校验统计字段，再转换成字典放入统一响应。
    return ApiResult(data=StatsOut(
        # 写入天数统计。
        total_days=total_days,
        done_days=done_days,
        # 写入计划和实际学时统计。
        total_planned_hours=total_planned,
        done_hours=done_hours,
        # 写入连续打卡天数和百分比。
        streak_days=streak,
        progress_pct=pct,
    ).model_dump())
