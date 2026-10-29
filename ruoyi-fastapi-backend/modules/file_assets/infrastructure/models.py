"""ORM mapping of file asset metadata; the binding table is the only ownership source of truth."""

from __future__ import annotations

from sqlalchemy import (
    CHAR,
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects import mysql

from config.database import Base

# Microsecond UTC timestamps on MySQL; plain DateTime elsewhere (tests, PostgreSQL).
UtcDateTime = DateTime().with_variant(mysql.DATETIME(fsp=6), 'mysql')
AutoBigInteger = BigInteger().with_variant(Integer, 'sqlite')


class FileAssetDO(Base):
    """
    文件资产表
    """

    __tablename__ = 'sys_file_asset'
    __table_args__ = (
        UniqueConstraint('bucket', 'object_key', name='uq_sys_file_asset_bucket_object_key'),
        Index('ix_sys_file_asset_state_expires_at', 'state', 'expires_at'),
        Index('ix_sys_file_asset_state_upload_deadline', 'state', 'upload_deadline'),
        Index('ix_sys_file_asset_state_delete_after', 'state', 'delete_after'),
        Index('ix_sys_file_asset_state_delete_next_attempt_at', 'state', 'delete_next_attempt_at'),
        Index('ix_sys_file_asset_state_deleted_at', 'state', 'deleted_at'),
        Index('ix_sys_file_asset_uploader_state_first_bound_at', 'uploader_id', 'state', 'first_bound_at'),
        {'comment': '文件资产表'},
    )

    asset_id = Column(CHAR(36), primary_key=True, comment='资产ID（UUID）')
    bucket = Column(String(63), nullable=False, comment='对象存储桶')
    object_key = Column(String(255), nullable=False, comment='不可变对象键')
    original_name = Column(String(255), nullable=False, comment='原始文件名')
    display_name = Column(String(255), nullable=False, comment='安全显示名')
    media_type = Column(String(127), nullable=True, comment='登记的规范媒体类型')
    content_disposition = Column(String(16), nullable=False, comment='交付方式（inline/attachment）')
    size_bytes = Column(BigInteger, nullable=True, comment='存储字节数')
    sha256 = Column(CHAR(64), nullable=True, comment='存储字节SHA-256')
    uploader_id = Column(BigInteger, nullable=False, comment='上传者用户ID')
    purpose = Column(String(64), nullable=False, comment='上传用途')
    intended_owner_type = Column(String(64), nullable=False, comment='意图归属业务类型')
    intended_owner_id = Column(String(128), nullable=True, comment='意图归属业务ID')
    state = Column(String(16), nullable=False, comment='状态（UPLOADING/READY/FAILED/DELETING/DELETED）')
    created_at = Column(UtcDateTime, nullable=False, comment='创建时间（UTC）')
    updated_at = Column(UtcDateTime, nullable=False, comment='更新时间（UTC）')
    uploaded_at = Column(UtcDateTime, nullable=True, comment='READY提交时间（UTC）')
    first_bound_at = Column(UtcDateTime, nullable=True, comment='首次绑定时间（UTC）')
    upload_deadline = Column(UtcDateTime, nullable=False, comment='上传状态截止时间（UTC）')
    expires_at = Column(UtcDateTime, nullable=True, comment='草稿到期时间（UTC）')
    delete_after = Column(UtcDateTime, nullable=True, comment='删除到期时间（UTC）')
    deleted_at = Column(UtcDateTime, nullable=True, comment='删除确认时间（UTC）')
    delete_next_attempt_at = Column(UtcDateTime, nullable=True, comment='下次删除执行时间（租约或退避）')
    delete_attempts = Column(Integer, nullable=False, default=0, server_default='0', comment='对象级删除失败次数')
    delete_failing_since = Column(UtcDateTime, nullable=True, comment='持续删除失败起点（UTC）')
    last_error_code = Column(String(64), nullable=True, comment='脱敏错误码')
    last_error_at = Column(UtcDateTime, nullable=True, comment='最近错误时间（UTC）')


class FileBindingDO(Base):
    """
    文件资产业务绑定表
    """

    __tablename__ = 'sys_file_binding'
    __table_args__ = (
        UniqueConstraint('asset_id', name='uq_sys_file_binding_asset_id'),
        UniqueConstraint(
            'owner_type', 'owner_id', 'field_key', 'position', name='uq_sys_file_binding_owner_field_position'
        ),
        Index('ix_sys_file_binding_owner_field', 'owner_type', 'owner_id', 'field_key'),
        {'comment': '文件资产业务绑定表'},
    )

    binding_id = Column(AutoBigInteger, primary_key=True, autoincrement=True, comment='绑定ID')
    asset_id = Column(
        CHAR(36),
        ForeignKey('sys_file_asset.asset_id', ondelete='RESTRICT', name='fk_sys_file_binding_asset_id'),
        nullable=False,
        comment='资产ID',
    )
    owner_type = Column(String(64), nullable=False, comment='归属业务类型')
    owner_id = Column(String(128), nullable=False, comment='归属业务ID（规范化字符串）')
    field_key = Column(String(64), nullable=False, comment='归属字段')
    position = Column(Integer, nullable=False, comment='字段内顺序（从0开始）')
    created_at = Column(UtcDateTime, nullable=False, comment='绑定时间（UTC）')
    created_by = Column(BigInteger, nullable=False, comment='绑定操作者用户ID')
