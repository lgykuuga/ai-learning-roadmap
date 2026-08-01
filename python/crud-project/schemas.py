"""
schemas.py — Pydantic 请求/响应模型
=====================================
"""
from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional


# ============================================================
# Phase
# ============================================================

class PhaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    period: Optional[str] = None
    desc: Optional[str] = None
    color: Optional[str] = None
    total_days: int = 0
    done_days: int = 0
    tips: list[str] = []

class WeekOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    week_num: Optional[int] = None
    weeks_large: bool = False
    total_days: int = 0
    done_days: int = 0

# ============================================================
# Day
# ============================================================

class DayListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    topic: str
    hours: float = 3
    resource: Optional[str] = None
    done: bool = False

class DayDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    topic: str
    hours: float = 3
    resource: Optional[str] = None
    detail: str
    done: bool = False
    note: str = ""
    checked_at: Optional[datetime] = None


# ============================================================
# Full nested output for the frontend list view
# ============================================================

class DayFullOut(BaseModel):
    id: int
    topic: str
    hours: float = 3
    resource: Optional[str] = None
    detail: str
    done: bool = False
    note: str = ""
    checked_at: Optional[datetime] = None


class WeekFullOut(BaseModel):
    id: int
    title: str
    week_num: Optional[int] = None
    days: list[DayFullOut] = []


class PhaseFullOut(BaseModel):
    id: int
    title: str
    period: Optional[str] = None
    desc: Optional[str] = None
    color: Optional[str] = None
    total_days: int = 0
    done_days: int = 0
    tips: list[str] = []
    weeks: list[WeekFullOut] = []

# ============================================================
# Progress
# ============================================================

class DoneToggle(BaseModel):
    done: bool

class NoteUpdate(BaseModel):
    note: str

class CheckinCreate(BaseModel):
    day_id: int
    date: date
    hours: float = 3
    note: str = ""

class CheckinOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    day_id: int
    date: date
    hours: float
    note: str = ""
    day_topic: str = ""

# ============================================================
# Stats
# ============================================================

class StatsOut(BaseModel):
    total_days: int
    done_days: int
    total_planned_hours: float
    done_hours: float
    streak_days: int
    progress_pct: int

# ============================================================
# Generic
# ============================================================

class ApiResult(BaseModel):
    code: int = 200
    msg: str = "success"
    data: object = None
