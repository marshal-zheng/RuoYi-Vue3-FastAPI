from datetime import datetime
from sqlalchemy import BigInteger, Column, DateTime, Index, String, Text
from config.database import Base


class SysAuditLog(Base):
    """
    数据库审计日志
    """

    __tablename__ = 'sys_audit_log'

    audit_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='审计日志主键')
    action = Column(String(10), nullable=False, default='', comment='动作类型（READ/INSERT/UPDATE/DELETE）')
    table_name = Column(String(64), nullable=False, default='', comment='表名')
    pk = Column(String(128), nullable=True, default='', comment='主键标识')
    before_data = Column(Text, nullable=True, default='', comment='变更前数据(JSON)')
    after_data = Column(Text, nullable=True, default='', comment='变更后数据(JSON)')
    changed_fields = Column(Text, nullable=True, default='', comment='变更字段(JSON)')
    query = Column(Text, nullable=True, default='', comment='读操作SQL/描述')
    operator_id = Column(String(64), nullable=True, default='', comment='操作人ID')
    operator_name = Column(String(64), nullable=True, default='', comment='操作人')
    operator_ip = Column(String(128), nullable=True, default='', comment='操作IP')
    request_id = Column(String(64), nullable=True, default='', comment='请求ID')
    trace_id = Column(String(64), nullable=True, default='', comment='链路ID')
    request_method = Column(String(16), nullable=True, default='', comment='请求方法')
    request_path = Column(String(255), nullable=True, default='', comment='请求路径')
    user_agent = Column(String(255), nullable=True, default='', comment='User-Agent')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='记录时间')

    idx_sys_audit_log_table = Index('idx_sys_audit_log_table', table_name)
    idx_sys_audit_log_action = Index('idx_sys_audit_log_action', action)
    idx_sys_audit_log_time = Index('idx_sys_audit_log_time', create_time)
    idx_sys_audit_log_operator = Index('idx_sys_audit_log_operator', operator_name)
