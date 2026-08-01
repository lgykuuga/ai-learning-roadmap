"""
models.py — 学习路线图 5 张表
=============================
Phase → Week → Day   (1:N:N)
每 Day 关联一个 Progress   (1:1)
每 Day 可以有多个 Checkin  (1:N)
"""
# 从 SQLAlchemy 导入建表所需的列类型、约束和数据库函数。
from sqlalchemy import (
    # Column 描述字段；Integer、String、Text、Numeric 是常用字段类型。
    Column, Integer, String, Text, Numeric,
    # Boolean、DateTime、Date 是布尔和日期类型；ForeignKey 声明外键，func 调用数据库函数。
    Boolean, DateTime, Date, ForeignKey, func,
)
# relationship 描述 ORM 对象之间的关联，方便通过对象属性访问关联数据。
from sqlalchemy.orm import relationship
# 导入所有 ORM 模型共同继承的声明式基类。
from database import Base


# 定义阶段 ORM 模型；继承 Base 后，这个类会映射到一张数据库表。
class Phase(Base):
    """阶段表 — 对标若依 sys_dept"""
    # __tablename__ 指定数据库中的真实表名。
    __tablename__ = "phases"

    # 主键 id 使用整数并自动递增。
    id = Column(Integer, primary_key=True, autoincrement=True)
    # nullable=False 表示阶段标题不能为空。
    title = Column(String(200), nullable=False, comment="阶段标题")
    # period 保存阶段对应的时间范围，未指定 nullable=False，因此允许为空。
    period = Column(String(100), comment="时间范围，如'第1-6周'")
    # Text 适合保存长度不固定的阶段说明。
    desc = Column(Text, comment="阶段描述")
    # String(20) 限制颜色字符串的最大长度。
    color = Column(String(20), comment="阶段颜色，如'#19c8b9'")
    # sort_order 用作展示顺序，创建对象时默认值为 0。
    sort_order = Column(Integer, default=0)

    # 一个 Phase 对应多个 Week，并按 Week.sort_order 排序。
    weeks = relationship("Week", back_populates="phase", order_by="Week.sort_order")
    # 一个 Phase 对应多个 Tip，并按 Tip.sort_order 排序。
    tips = relationship("Tip", back_populates="phase", order_by="Tip.sort_order")


# 定义周 ORM 模型。
class Week(Base):
    """周表 — 对标若依文档的子章节"""
    # 映射到 weeks 表。
    __tablename__ = "weeks"

    # 周记录的自增主键。
    id = Column(Integer, primary_key=True, autoincrement=True)
    # phase_id 外键指向 phases.id，保证每周都属于一个阶段。
    phase_id = Column(Integer, ForeignKey("phases.id"), nullable=False)
    # 周标题不能为空。
    title = Column(String(200), nullable=False, comment="周标题")
    # week_num 保存整条路线中的全局周序号。
    week_num = Column(Integer, comment="第几周（全局编号）")
    # weeks_large 标记这一项是否跨越多周。
    weeks_large = Column(Boolean, default=False, comment="是否跨2周的项目周（14-15,16-17,21-22）")
    # 同一阶段内的展示顺序。
    sort_order = Column(Integer, default=0)

    # 多个 Week 反向关联到一个 Phase；名称与 Phase.weeks 的 back_populates 对应。
    phase = relationship("Phase", back_populates="weeks")
    # 一个 Week 拥有多个 Day，并按 Day.sort_order 排序。
    days = relationship("Day", back_populates="week", order_by="Day.sort_order")


# 定义每日学习内容 ORM 模型。
class Day(Base):
    """天表 — 核心内容表。detail 存富文本（Markdown格式）"""
    # 映射到 days 表。
    __tablename__ = "days"

    # 每日学习记录的自增主键。
    id = Column(Integer, primary_key=True, autoincrement=True)
    # week_id 外键指向 weeks.id，表示这一天属于哪一周。
    week_id = Column(Integer, ForeignKey("weeks.id"), nullable=False)
    # topic 保存当天主题且不能为空。
    topic = Column(String(300), nullable=False, comment="今日主题")
    # Numeric(3, 1) 最多三位有效数字并保留一位小数，默认计划学习 3 小时。
    hours = Column(Numeric(3, 1), default=3, comment="建议学时")
    # resource 保存推荐资源地址或描述。
    resource = Column(String(500), comment="推荐资源")
    # detail 使用 Text 保存完整教学内容且不能为空。
    detail = Column(Text, nullable=False, comment="教学内容（Markdown富文本）")
    # 同一周中的展示顺序。
    sort_order = Column(Integer, default=0)

    # 多个 Day 反向关联到一个 Week。
    week = relationship("Week", back_populates="days")
    # uselist=False 把关联结果表现为单个 Progress，而不是列表。
    progress = relationship("Progress", back_populates="day", uselist=False)
    # 一个 Day 可以拥有多条 Checkin 打卡记录。
    checkins = relationship("Checkin", back_populates="day")


# 定义学习进度 ORM 模型。
class Progress(Base):
    """学习进度表 — 每 Day 最多一条记录（1:1）"""
    # 映射到 progress 表。
    __tablename__ = "progress"

    # 进度记录的自增主键。
    id = Column(Integer, primary_key=True, autoincrement=True)
    # unique=True 保证一个 day_id 最多只有一条进度记录，从数据库层实现一对一。
    day_id = Column(Integer, ForeignKey("days.id"), unique=True, nullable=False)
    # done 表示该学习日是否已经完成。
    done = Column(Boolean, default=False, comment="是否完成")
    # hours 保存实际学习时长，允许暂时为空。
    hours = Column(Numeric(3, 1), comment="实际学时")
    # note 保存学习笔记。
    note = Column(Text, comment="学习笔记")
    # timezone=True 表示时间值可以携带时区信息。
    checked_at = Column(DateTime(timezone=True), comment="最后打卡时间")

    # 每条 Progress 反向关联到对应的 Day。
    day = relationship("Day", back_populates="progress")


# 定义打卡历史 ORM 模型。
class Checkin(Base):
    """打卡记录表 — 每次打卡一条记录（1:N）"""
    # 映射到 checkins 表。
    __tablename__ = "checkins"

    # 打卡记录的自增主键。
    id = Column(Integer, primary_key=True, autoincrement=True)
    # day_id 外键表示本次打卡属于哪个学习日。
    day_id = Column(Integer, ForeignKey("days.id"), nullable=False)
    # date 只保存打卡日期，不包含具体时间。
    date = Column(Date, nullable=False, comment="打卡日期")
    # 本次打卡的学习时长，默认 3 小时。
    hours = Column(Numeric(3, 1), default=3, comment="学习时长")
    # 本次打卡的补充说明。
    note = Column(Text, comment="打卡备注")
    # server_default=func.now() 让数据库在插入记录时自动填写创建时间。
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 多条 Checkin 反向关联到一个 Day。
    day = relationship("Day", back_populates="checkins")


# 定义阶段建议 ORM 模型。
class Tip(Base):
    """阶段建议表 — 每个 Phase 有 2 条 tips"""
    # 映射到 tips 表。
    __tablename__ = "tips"

    # 建议记录的自增主键。
    id = Column(Integer, primary_key=True, autoincrement=True)
    # phase_id 外键表示建议属于哪个阶段。
    phase_id = Column(Integer, ForeignKey("phases.id"), nullable=False)
    # 建议正文不能为空。
    text = Column(Text, nullable=False, comment="建议内容")
    # 同一阶段中建议的展示顺序。
    sort_order = Column(Integer, default=0)

    # 多条 Tip 反向关联到一个 Phase。
    phase = relationship("Phase", back_populates="tips")


# 选一个简单名字导出
# __all__ 明确 from models import * 时允许导出的名称，不影响显式导入。
__all__ = ["Phase", "Week", "Day", "Progress", "Checkin", "Tip", "Base"]
