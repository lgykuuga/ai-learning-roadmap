"""
models.py — 学习路线图 5 张表
=============================
Phase → Week → Day   (1:N:N)
每 Day 关联一个 Progress   (1:1)
每 Day 可以有多个 Checkin  (1:N)
"""
from sqlalchemy import (
    Column, Integer, String, Text, Numeric,
    Boolean, DateTime, Date, ForeignKey, func,
)
from sqlalchemy.orm import relationship
from database import Base


class Phase(Base):
    """阶段表 — 对标若依 sys_dept"""
    __tablename__ = "phases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, comment="阶段标题")
    period = Column(String(100), comment="时间范围，如'第1-6周'")
    desc = Column(Text, comment="阶段描述")
    color = Column(String(20), comment="阶段颜色，如'#19c8b9'")
    sort_order = Column(Integer, default=0)

    weeks = relationship("Week", back_populates="phase", order_by="Week.sort_order")
    tips = relationship("Tip", back_populates="phase", order_by="Tip.sort_order")


class Week(Base):
    """周表 — 对标若依文档的子章节"""
    __tablename__ = "weeks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phase_id = Column(Integer, ForeignKey("phases.id"), nullable=False)
    title = Column(String(200), nullable=False, comment="周标题")
    week_num = Column(Integer, comment="第几周（全局编号）")
    weeks_large = Column(Boolean, default=False, comment="是否跨2周的项目周（14-15,16-17,21-22）")
    sort_order = Column(Integer, default=0)

    phase = relationship("Phase", back_populates="weeks")
    days = relationship("Day", back_populates="week", order_by="Day.sort_order")


class Day(Base):
    """天表 — 核心内容表。detail 存富文本（Markdown格式）"""
    __tablename__ = "days"

    id = Column(Integer, primary_key=True, autoincrement=True)
    week_id = Column(Integer, ForeignKey("weeks.id"), nullable=False)
    topic = Column(String(300), nullable=False, comment="今日主题")
    hours = Column(Numeric(3, 1), default=3, comment="建议学时")
    resource = Column(String(500), comment="推荐资源")
    detail = Column(Text, nullable=False, comment="教学内容（Markdown富文本）")
    sort_order = Column(Integer, default=0)

    week = relationship("Week", back_populates="days")
    progress = relationship("Progress", back_populates="day", uselist=False)
    checkins = relationship("Checkin", back_populates="day")


class Progress(Base):
    """学习进度表 — 每 Day 最多一条记录（1:1）"""
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    day_id = Column(Integer, ForeignKey("days.id"), unique=True, nullable=False)
    done = Column(Boolean, default=False, comment="是否完成")
    hours = Column(Numeric(3, 1), comment="实际学时")
    note = Column(Text, comment="学习笔记")
    checked_at = Column(DateTime(timezone=True), comment="最后打卡时间")

    day = relationship("Day", back_populates="progress")


class Checkin(Base):
    """打卡记录表 — 每次打卡一条记录（1:N）"""
    __tablename__ = "checkins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    day_id = Column(Integer, ForeignKey("days.id"), nullable=False)
    date = Column(Date, nullable=False, comment="打卡日期")
    hours = Column(Numeric(3, 1), default=3, comment="学习时长")
    note = Column(Text, comment="打卡备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    day = relationship("Day", back_populates="checkins")


class Tip(Base):
    """阶段建议表 — 每个 Phase 有 2 条 tips"""
    __tablename__ = "tips"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phase_id = Column(Integer, ForeignKey("phases.id"), nullable=False)
    text = Column(Text, nullable=False, comment="建议内容")
    sort_order = Column(Integer, default=0)

    phase = relationship("Phase", back_populates="tips")


# 选一个简单名字导出
__all__ = ["Phase", "Week", "Day", "Progress", "Checkin", "Tip", "Base"]
