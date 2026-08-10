"""
schemas.py — Pydantic 请求/响应模型
=====================================
"""
# BaseModel 是所有 Pydantic 数据模型的基类；ConfigDict 用于配置模型行为。
from pydantic import BaseModel, ConfigDict
# 导入日期和日期时间类型，让 Pydantic 能自动校验并转换对应字符串。
from datetime import date, datetime
# Optional[T] 表示字段既可以是 T，也可以是 None。
from typing import Optional


# ============================================================
# Phase
# ============================================================

# 定义阶段列表或详情中的阶段响应结构。
class PhaseOut(BaseModel):
    # from_attributes=True 允许直接从 SQLAlchemy ORM 对象读取同名属性。
    model_config = ConfigDict(from_attributes=True)
    # 阶段主键。
    id: int
    # 阶段标题，必须是字符串。
    title: str
    # 时间范围允许为空，默认值为 None。
    period: Optional[str] = None
    # 阶段说明允许为空。
    desc: Optional[str] = None
    # 阶段颜色允许为空。
    color: Optional[str] = None
    # 阶段包含的学习日总数，默认 0。
    total_days: int = 0
    # 已完成的学习日数量，默认 0。
    done_days: int = 0
    # tips 是字符串列表，默认空列表。
    tips: list[str] = []

# 定义周列表中的单周响应结构。
class WeekOut(BaseModel):
    # 允许从 ORM Week 对象读取字段。
    model_config = ConfigDict(from_attributes=True)
    # 周记录主键。
    id: int
    # 周标题。
    title: str
    # 全局周序号允许为空。
    week_num: Optional[int] = None
    # 是否为跨多周项目，默认否。
    weeks_large: bool = False
    # 本周学习日总数。
    total_days: int = 0
    # 本周已完成学习日数。
    done_days: int = 0

# ============================================================
# Day
# ============================================================

# 定义学习日列表中的精简响应结构。
class DayListItem(BaseModel):
    # 允许从 ORM Day 对象读取字段。
    model_config = ConfigDict(from_attributes=True)
    # 学习日主键。
    id: int
    # 当天学习主题。
    topic: str
    # 计划学时转换为浮点数，默认 3 小时。
    hours: float = 3
    # 推荐资源允许为空。
    resource: Optional[str] = None
    # 当前完成状态，默认未完成。
    done: bool = False

# 定义单个学习日详情响应结构。
class DayDetail(BaseModel):
    # 允许从 ORM Day 对象读取字段。
    model_config = ConfigDict(from_attributes=True)
    # 学习日主键。
    id: int
    # 当天学习主题。
    topic: str
    # 计划学时。
    hours: float = 3
    # 推荐资源允许为空。
    resource: Optional[str] = None
    # 当天完整教学内容。
    detail: str
    # 是否完成。
    done: bool = False
    # 学习笔记，默认空字符串，前端不需要额外判断 None。
    note: str = ""
    # 最后打卡时间允许为空。
    checked_at: Optional[datetime] = None


# ============================================================
# Full nested output for the frontend list view
# ============================================================

# 定义嵌套在完整周数据中的学习日结构。
class DayFullOut(BaseModel):
    # 学习日主键。
    id: int
    # 当天学习主题。
    topic: str
    # 计划学时。
    hours: float = 3
    # 推荐资源允许为空。
    resource: Optional[str] = None
    # 当天完整教学内容。
    detail: str
    # 是否完成。
    done: bool = False
    # 学习笔记。
    note: str = ""
    # 最后打卡时间。
    checked_at: Optional[datetime] = None


# 定义包含每日详情的完整周结构。
class WeekFullOut(BaseModel):
    # 周记录主键。
    id: int
    # 周标题。
    title: str
    # 全局周序号允许为空。
    week_num: Optional[int] = None
    # 本周包含的完整学习日列表。
    days: list[DayFullOut] = []


# 定义前端一次性加载时使用的完整阶段树结构。
class ResourceIn(BaseModel):
    title: str
    url: str
    kind: str = "free"
    sort_order: int = 0


class ResourceOut(ResourceIn):
    id: int


class PhaseCreate(BaseModel):
    title: str
    period: Optional[str] = None
    desc: Optional[str] = None
    color: Optional[str] = None
    sort_order: int = 0
    tips: list[str] = []
    resources: list[ResourceIn] = []


class PhaseUpdate(BaseModel):
    title: Optional[str] = None
    period: Optional[str] = None
    desc: Optional[str] = None
    color: Optional[str] = None
    sort_order: Optional[int] = None
    tips: Optional[list[str]] = None
    resources: Optional[list[ResourceIn]] = None


class WeekCreate(BaseModel):
    title: str
    week_num: Optional[int] = None
    weeks_large: bool = False
    sort_order: int = 0


class WeekUpdate(BaseModel):
    title: Optional[str] = None
    week_num: Optional[int] = None
    weeks_large: Optional[bool] = None
    sort_order: Optional[int] = None


class DayCreate(BaseModel):
    topic: str
    hours: float = 3
    resource: Optional[str] = None
    detail: str = ""
    sort_order: int = 0


class DayUpdate(BaseModel):
    topic: Optional[str] = None
    hours: Optional[float] = None
    resource: Optional[str] = None
    detail: Optional[str] = None
    sort_order: Optional[int] = None


class PhaseFullOut(BaseModel):
    # 阶段主键。
    id: int
    # 阶段标题。
    title: str
    # 阶段时间范围。
    period: Optional[str] = None
    # 阶段说明。
    desc: Optional[str] = None
    # 阶段颜色。
    color: Optional[str] = None
    # 阶段中的学习日总数。
    total_days: int = 0
    # 阶段中已完成的学习日数。
    done_days: int = 0
    # 阶段建议文本列表。
    tips: list[str] = []
    resources: list[ResourceOut] = []
    # 阶段下完整的周列表，周中继续嵌套学习日。
    weeks: list[WeekFullOut] = []

# ============================================================
# Progress
# ============================================================

# 定义切换学习日完成状态接口的请求体。
class DoneToggle(BaseModel):
    # done 是必填布尔值，表示要设置成完成还是未完成。
    done: bool

# 定义保存学习笔记接口的请求体。
class NoteUpdate(BaseModel):
    # note 是要保存的完整笔记文本。
    note: str

# 定义手动新增打卡记录接口的请求体。
class CheckinCreate(BaseModel):
    # 要打卡的学习日 id。
    day_id: int
    # 打卡日期；请求 JSON 中通常使用 YYYY-MM-DD 字符串。
    date: date
    # 本次学习时长，默认 3 小时。
    hours: float = 3
    # 打卡备注，默认空字符串。
    note: str = ""

class CheckinUpdate(BaseModel):
    day_id: Optional[int] = None
    date: Optional[date] = None
    hours: Optional[float] = None
    note: Optional[str] = None

# 定义打卡记录的响应结构。
class CheckinOut(BaseModel):
    # 允许从 ORM Checkin 对象读取字段。
    model_config = ConfigDict(from_attributes=True)
    # 打卡记录主键。
    id: int
    # 对应的学习日 id。
    day_id: int
    # 打卡日期。
    date: date
    # 实际学习时长。
    hours: float
    # 打卡备注。
    note: str = ""
    # 额外返回关联 Day 的主题，方便列表直接展示。
    day_topic: str = ""

# ============================================================
# Stats
# ============================================================

# 定义首页统计卡片的响应结构。
class StatsOut(BaseModel):
    # 全部计划学习日数量。
    total_days: int
    # 已完成学习日数量。
    done_days: int
    # 全部计划学时总和。
    total_planned_hours: float
    # 已完成项目对应的实际学时总和。
    done_hours: float
    # 连续打卡天数。
    streak_days: int
    # 整体进度百分比。
    progress_pct: int

# ============================================================
# Generic
# ============================================================

# 定义所有接口共同使用的外层响应包装。
class ApiResult(BaseModel):
    # code 是业务状态码，默认 200 表示成功。
    code: int = 200
    # msg 是给调用方看的结果说明。
    msg: str = "success"
    # data 可以承载列表、字典或具体 Schema，因此使用通用 object 类型。
    data: object = None


class LoginRequest(BaseModel):
    username: str
    password: str
