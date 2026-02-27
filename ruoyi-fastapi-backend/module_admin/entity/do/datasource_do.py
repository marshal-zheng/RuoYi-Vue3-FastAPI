from sqlalchemy import Column, String, Integer, JSON
from module_admin.entity.do.base import BaseModel
from utils.sensitive.types import sensitive_string


class DataSourceDO(BaseModel):
    __tablename__ = 'sys_datasource'

    name = Column(String(100), unique=True, nullable=False, comment='数据源名称')
    type = Column(String(20), nullable=False, comment='数据源类型(mysql/mongodb/minio/postgresql)')
    host = Column(String(255), nullable=False, comment='主机地址')
    port = Column(Integer, nullable=False, comment='端口号')
    username = Column(String(100), comment='用户名')
    password = sensitive_string(length=500, comment='密码')
    database_name = Column(String(100), comment='数据库名/存储桶')
    description = Column(String(500), comment='描述信息')
    status = Column(String(10), default='offline', comment='连接状态(online/offline)')
    extra_config = Column(JSON, default=dict, comment='类型独有配置')
