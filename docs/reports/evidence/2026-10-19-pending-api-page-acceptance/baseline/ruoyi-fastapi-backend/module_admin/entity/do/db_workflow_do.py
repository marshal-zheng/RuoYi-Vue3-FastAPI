from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Index, Integer, String, Text, UniqueConstraint

from config.database import Base

BIGINT_PK = BigInteger().with_variant(Integer(), 'sqlite')


class DbWorkflowArtifactDO(Base):
    """Formal managed-data/release-manifest apply history."""

    __tablename__ = 'sys_db_workflow_artifact'

    artifact_id = Column(BIGINT_PK, primary_key=True, autoincrement=True, comment='工作流产物主键')
    bundle_id = Column(String(64), nullable=False, comment='Bundle 标识')
    artifact_type = Column(String(32), nullable=False, comment='产物类型(managed-data/release-manifest)')
    artifact_checksum = Column(String(128), nullable=False, comment='产物校验和')
    apply_status = Column(String(16), nullable=False, comment='应用状态')
    applied_at = Column(DateTime, nullable=False, default=datetime.now, comment='应用时间')
    applied_by = Column(String(64), nullable=True, default=None, comment='应用人/执行器')
    details_json = Column(Text, nullable=True, default=None, comment='结构化结果明细(JSON)')

    __table_args__ = (
        UniqueConstraint('bundle_id', 'artifact_type', name='uq_sys_db_workflow_artifact_bundle_type'),
        Index('idx_sys_db_workflow_artifact_status', 'apply_status'),
        Index('idx_sys_db_workflow_artifact_applied_at', 'applied_at'),
    )


class DbWorkflowObjectDO(Base):
    """Managed object ownership metadata for prune safety."""

    __tablename__ = 'sys_db_workflow_object'

    object_id = Column(BIGINT_PK, primary_key=True, autoincrement=True, comment='受管对象主键')
    object_type = Column(String(32), nullable=False, comment='对象类型(sys_menu/sys_dict_type/...)')
    object_key = Column(String(191), nullable=False, comment='对象业务键')
    module_key = Column(String(64), nullable=False, comment='所属 capability 模块键')
    object_domain = Column(String(32), nullable=False, comment='能力域(menus/role_grants/dict_types/...)')
    owner_scope = Column(String(32), nullable=False, comment='管理范围(menus/dict_types/configs/...)')
    last_bundle_id = Column(String(64), nullable=True, default=None, comment='最近一次写入的 bundle_id')
    last_source_path = Column(String(255), nullable=True, default=None, comment='最近一次声明来源路径')
    source_checksum = Column(String(128), nullable=False, comment='声明源内容校验和')
    checksum = Column(String(128), nullable=False, comment='当前对象受管内容校验和')
    active_flag = Column(String(1), nullable=False, default='Y', comment='是否仍由统一工作流受管(Y/N)')
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    __table_args__ = (
        UniqueConstraint('object_type', 'object_key', name='uq_sys_db_workflow_object_type_key'),
        Index('idx_sys_db_workflow_object_module', 'module_key'),
        Index('idx_sys_db_workflow_object_domain', 'object_domain'),
        Index('idx_sys_db_workflow_object_scope', 'owner_scope'),
        Index('idx_sys_db_workflow_object_bundle', 'last_bundle_id'),
        Index('idx_sys_db_workflow_object_active', 'active_flag'),
    )
