"""
ORM 基类和 Mixin
提供统一的审计字段、时间戳和软删除功能
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, BigInteger
from config.database import Base
from module_admin.entity.do.validators import ValidatorMixin


class TimestampMixin:
    """时间戳 Mixin - 自动管理创建和更新时间"""
    
    create_time = Column(
        DateTime, 
        default=datetime.now, 
        nullable=True, 
        comment='创建时间'
    )
    update_time = Column(
        DateTime, 
        default=datetime.now, 
        onupdate=datetime.now, 
        nullable=True, 
        comment='更新时间'
    )


class AuditMixin:
    """审计 Mixin - 记录创建者和更新者"""
    
    create_by = Column(String(64), default='', comment='创建者')
    update_by = Column(String(64), default='', comment='更新者')


class SoftDeleteMixin:
    """软删除 Mixin - 支持逻辑删除而非物理删除"""
    
    deleted_at = Column(DateTime, nullable=True, index=True, comment='删除时间')
    is_deleted = Column(Boolean, default=False, nullable=False, index=True, comment='是否删除')
    
    def soft_delete(self):
        """执行软删除"""
        self.is_deleted = True
        self.deleted_at = datetime.now()
    
    def restore(self):
        """恢复软删除的记录"""
        self.is_deleted = False
        self.deleted_at = None


class RemarkMixin:
    """备注 Mixin - 通用备注字段"""
    
    remark = Column(String(500), default='', comment='备注')


class BaseModel(Base, TimestampMixin, AuditMixin, SoftDeleteMixin, ValidatorMixin):
    """
    基础 Model 类
    
    包含所有通用字段：
    - id: 主键
    - create_time, update_time: 时间戳
    - create_by, update_by: 审计字段
    - is_deleted, deleted_at: 软删除字段
    """
    __abstract__ = True
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')


class LegacyBaseModel(Base, TimestampMixin, AuditMixin, ValidatorMixin):
    """
    遗留系统兼容基类
    
    用于逐步迁移现有模型，仅包含时间戳和审计字段
    不包含软删除字段，保留原有的 del_flag 字段兼容性
    """
    __abstract__ = True


class CreateTimeOnlyMixin:
    """只有创建时间的 Mixin - 用于日志表等只记录创建时间的场景"""
    
    create_time = Column(
        DateTime, 
        default=datetime.now, 
        nullable=True, 
        comment='创建时间'
    )


class LogBaseModel(Base, CreateTimeOnlyMixin, ValidatorMixin):
    """
    日志基类
    
    用于日志、记录等只需要创建时间的表
    """
    __abstract__ = True


class RelationBaseModel(Base, ValidatorMixin):
    """
    关联表基类
    
    用于多对多关联表，通常无审计字段
    """
    __abstract__ = True
