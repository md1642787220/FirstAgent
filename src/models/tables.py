"""
ORM 表定义
5张核心表：work_orders / process_steps / boms / bom_items / inventory
"""
from sqlalchemy import (
    Column, Text, Integer, Float, Date, DateTime, ForeignKey,
    Boolean, create_engine
)
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类"""
    pass


class WorkOrder(Base):
    """工单表"""
    __tablename__ = "work_orders"

    id = Column(Text, primary_key=True)              # 工单号 WO-2026-001
    product_name = Column(Text, nullable=False)      # 产品名称
    product_code = Column(Text)                      # 产品编码
    quantity = Column(Integer, nullable=False)       # 生产数量
    priority = Column(Text, default="中")            # 紧急/高/中/低
    status = Column(Text, default="待排产")          # 待排产/生产中/已完成/已暂停
    planned_start = Column(Date)                     # 计划开始
    planned_end = Column(Date)                       # 计划结束
    actual_start = Column(Date)                      # 实际开始
    actual_end = Column(Date)                        # 实际结束
    customer = Column(Text)                          # 客户
    progress = Column(Integer, default=0)            # 进度百分比
    delay_days = Column(Integer, default=0)          # 滞后天数
    created_at = Column(DateTime, default=datetime.now)

    # 关联工序
    process_steps = relationship("ProcessStep", back_populates="work_order", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "product_name": self.product_name,
            "product_code": self.product_code,
            "quantity": self.quantity,
            "priority": self.priority,
            "status": self.status,
            "planned_start": str(self.planned_start) if self.planned_start else None,
            "planned_end": str(self.planned_end) if self.planned_end else None,
            "actual_start": str(self.actual_start) if self.actual_start else None,
            "actual_end": str(self.actual_end) if self.actual_end else None,
            "customer": self.customer,
            "progress": self.progress,
            "delay_days": self.delay_days,
        }


class ProcessStep(Base):
    """工序进度表"""
    __tablename__ = "process_steps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    work_order_id = Column(Text, ForeignKey("work_orders.id"), nullable=False)
    step_name = Column(Text, nullable=False)         # 下料/焊接/打磨/检验/包装
    step_order = Column(Integer, nullable=False)     # 工序顺序
    status = Column(Text, default="未开始")          # 未开始/进行中/已完成/阻塞
    planned_duration = Column(Integer)               # 计划时长(小时)
    actual_duration = Column(Integer)                # 实际时长(小时)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    device_id = Column(Text)                         # 关联设备
    operator = Column(Text)                          # 操作员
    notes = Column(Text)                             # 备注

    work_order = relationship("WorkOrder", back_populates="process_steps")

    def to_dict(self):
        return {
            "id": self.id,
            "work_order_id": self.work_order_id,
            "step_name": self.step_name,
            "step_order": self.step_order,
            "status": self.status,
            "planned_duration": self.planned_duration,
            "actual_duration": self.actual_duration,
            "start_time": str(self.start_time) if self.start_time else None,
            "end_time": str(self.end_time) if self.end_time else None,
            "device_id": self.device_id,
            "operator": self.operator,
            "notes": self.notes,
        }


class BOM(Base):
    """BOM表头"""
    __tablename__ = "boms"

    id = Column(Text, primary_key=True)              # BOM-2026-001
    product_code = Column(Text, nullable=False)      # 产品编码
    product_name = Column(Text)                      # 产品名称
    version = Column(Text, nullable=False)           # 版本号 V1.0
    status = Column(Text, default="已发布")          # 草稿/已发布/已废弃
    effective_date = Column(Date)                    # 生效日期
    created_by = Column(Text)                        # 创建人
    created_at = Column(DateTime, default=datetime.now)
    description = Column(Text)                       # 描述

    items = relationship("BOMItem", back_populates="bom", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "product_code": self.product_code,
            "product_name": self.product_name,
            "version": self.version,
            "status": self.status,
            "effective_date": str(self.effective_date) if self.effective_date else None,
            "created_by": self.created_by,
            "description": self.description,
        }


class BOMItem(Base):
    """BOM明细（父子层级）"""
    __tablename__ = "bom_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bom_id = Column(Text, ForeignKey("boms.id"), nullable=False)
    parent_item_id = Column(Integer)                 # NULL表示顶层
    material_code = Column(Text, nullable=False)     # 物料编码
    material_name = Column(Text, nullable=False)     # 物料名称
    specification = Column(Text)                     # 规格
    quantity = Column(Float, nullable=False)         # 用量
    unit = Column(Text)                              # 件/米/公斤
    material_type = Column(Text)                     # 原材料/外购件/自制件/标准件
    source_supplier = Column(Text)                   # 供应商
    cost = Column(Float, default=0)                  # 单价
    lead_time = Column(Integer, default=0)           # 采购提前期(天)
    remark = Column(Text)                            # 备注

    bom = relationship("BOM", back_populates="items")

    def to_dict(self):
        return {
            "id": self.id,
            "bom_id": self.bom_id,
            "parent_item_id": self.parent_item_id,
            "material_code": self.material_code,
            "material_name": self.material_name,
            "specification": self.specification,
            "quantity": self.quantity,
            "unit": self.unit,
            "material_type": self.material_type,
            "source_supplier": self.source_supplier,
            "cost": self.cost,
            "lead_time": self.lead_time,
            "remark": self.remark,
        }


class Inventory(Base):
    """库存表"""
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    material_code = Column(Text, unique=True, nullable=False)  # 物料编码
    material_name = Column(Text, nullable=False)               # 物料名称
    category = Column(Text)                                    # 原材料/半成品/成品/辅料
    warehouse = Column(Text)                                   # 仓库
    location = Column(Text)                                    # 库位
    quantity = Column(Float, default=0)                        # 当前库存
    unit = Column(Text)                                        # 单位
    safety_stock = Column(Float, default=0)                    # 安全库存
    max_stock = Column(Float, default=0)                       # 最大库存
    reorder_point = Column(Float, default=0)                   # 再订货点
    last_inbound = Column(Date)                                # 最后入库
    last_outbound = Column(Date)                               # 最后出库
    turnover_days = Column(Integer, default=0)                 # 周转天数
    status = Column(Text, default="正常")                      # 正常/短缺/呆滞/超储
    supplier = Column(Text)                                    # 供应商
    unit_cost = Column(Float, default=0)                       # 单价

    def to_dict(self):
        return {
            "id": self.id,
            "material_code": self.material_code,
            "material_name": self.material_name,
            "category": self.category,
            "warehouse": self.warehouse,
            "location": self.location,
            "quantity": self.quantity,
            "unit": self.unit,
            "safety_stock": self.safety_stock,
            "max_stock": self.max_stock,
            "reorder_point": self.reorder_point,
            "last_inbound": str(self.last_inbound) if self.last_inbound else None,
            "last_outbound": str(self.last_outbound) if self.last_outbound else None,
            "turnover_days": self.turnover_days,
            "status": self.status,
            "supplier": self.supplier,
            "unit_cost": self.unit_cost,
        }


# ============================================================
# 对话历史表
# ============================================================

class ChatSession(Base):
    """对话会话表"""
    __tablename__ = "chat_sessions"

    id = Column(Text, primary_key=True)                # session_id: sess_xxxxxxxx
    title = Column(Text, default="新对话")              # 会话标题（取首条消息前若干字）
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at),
        }


class ChatMessage(Base):
    """对话消息表"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Text, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(Text, nullable=False)                # user / assistant
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    session = relationship("ChatSession", back_populates="messages")

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "created_at": str(self.created_at),
        }
