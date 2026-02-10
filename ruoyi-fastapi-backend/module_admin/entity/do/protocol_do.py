from sqlalchemy import Column, DateTime, Integer, String, Boolean, JSON
from module_admin.entity.do.base import LegacyBaseModel
from module_admin.entity.do.enums import StatusEnum, DelFlagEnum


class ProtocolDO(LegacyBaseModel):
    """
    协议管理表
    """

    __tablename__ = 'sys_protocol'

    protocol_id = Column(Integer, primary_key=True, autoincrement=True, comment='协议ID')
    protocol_name = Column(String(100), nullable=False, comment='协议名称')
    protocol_type = Column(String(50), nullable=False, comment='协议类型')
    status = Column(String(1), nullable=False, default=StatusEnum.NORMAL.value, comment='状态（0正常 1停用）')
    description = Column(String(500), nullable=True, comment='协议描述')
    protocol_config = Column(JSON, nullable=True, comment='协议配置')
    del_flag = Column(String(1), nullable=True, default=DelFlagEnum.EXIST.value, comment='删除标志')

    def __init__(self, **kwargs):
        extra_fields = {
            'bus_speed',
            'word_length',
            'rt_address',
            'sub_address',
            'word_count',
            'baud_rate',
            'can_id',
            'data_length',
            'data_bits',
            'stop_bits',
            'parity',
            'ip_address',
            'port',
            'protocol',
        }
        extras = {}
        for key in list(kwargs.keys()):
            if key in extra_fields:
                extras[key] = kwargs.pop(key)
        super().__init__(**kwargs)
        for key, value in extras.items():
            setattr(self, key, value)


# Backward-compatible alias for tests/imports expecting Protocol
Protocol = ProtocolDO
