"""
数据库枚举类型定义
替代魔法值字符串，提供类型安全和代码可读性
"""
from enum import Enum as PyEnum


class StatusEnum(str, PyEnum):
    """状态枚举（通用）"""
    NORMAL = '0'  # 正常
    DISABLED = '1'  # 停用


class DelFlagEnum(str, PyEnum):
    """删除标志枚举（兼容旧系统）"""
    EXIST = '0'  # 存在
    DELETED = '2'  # 已删除


class GenderEnum(str, PyEnum):
    """性别枚举"""
    MALE = '0'  # 男
    FEMALE = '1'  # 女
    UNKNOWN = '2'  # 未知


class UserTypeEnum(str, PyEnum):
    """用户类型枚举"""
    SYSTEM = '00'  # 系统用户


class YesNoEnum(str, PyEnum):
    """是否枚举（通用）"""
    YES = 'Y'
    NO = 'N'


class DataScopeEnum(str, PyEnum):
    """数据权限范围枚举"""
    ALL = '1'  # 全部数据权限
    CUSTOM = '2'  # 自定义数据权限
    DEPT = '3'  # 本部门数据权限
    DEPT_AND_CHILD = '4'  # 本部门及以下数据权限
    SELF = '5'  # 仅本人数据权限


class MenuTypeEnum(str, PyEnum):
    """菜单类型枚举"""
    DIR = 'M'  # 目录
    MENU = 'C'  # 菜单
    BUTTON = 'F'  # 按钮


class VisibleEnum(str, PyEnum):
    """显示状态枚举"""
    SHOW = '0'  # 显示
    HIDE = '1'  # 隐藏


class JobStatusEnum(str, PyEnum):
    """定时任务状态枚举"""
    NORMAL = '0'  # 正常
    PAUSED = '1'  # 暂停


class JobGroupEnum(str, PyEnum):
    """任务组名枚举"""
    DEFAULT = 'default'  # 默认
    SYSTEM = 'system'  # 系统


class MisfirePolicyEnum(str, PyEnum):
    """计划执行策略枚举"""
    DEFAULT = '0'  # 默认
    IMMEDIATELY = '1'  # 立即执行
    ONCE = '2'  # 执行一次
    ABANDON = '3'  # 放弃执行


class NoticeTypeEnum(str, PyEnum):
    """通知类型枚举"""
    NOTICE = '1'  # 通知
    ANNOUNCEMENT = '2'  # 公告


class NoticeStatusEnum(str, PyEnum):
    """通知状态枚举"""
    NORMAL = '0'  # 正常
    CLOSED = '1'  # 关闭


class OperTypeEnum(str, PyEnum):
    """操作类型枚举"""
    OTHER = '0'  # 其他
    ADD = '1'  # 新增
    MODIFY = '2'  # 修改
    DELETE = '3'  # 删除
    GRANT = '4'  # 授权
    EXPORT = '5'  # 导出
    IMPORT = '6'  # 导入
    FORCE_LOGOUT = '7'  # 强退
    CLEAN = '8'  # 清空


class BusinessStatusEnum(str, PyEnum):
    """业务操作状态枚举"""
    SUCCESS = '0'  # 成功
    FAIL = '1'  # 失败


class LoginStatusEnum(str, PyEnum):
    """登录状态枚举"""
    SUCCESS = '0'  # 成功
    FAIL = '1'  # 失败


class EnableStatusEnum(str, PyEnum):
    """启用状态枚举"""
    DISABLED = '0'  # 停用
    ENABLED = '1'  # 启用


class SimulationStatusEnum(str, PyEnum):
    """仿真状态枚举"""
    CREATED = 'created'
    RUNNING = 'running'
    STOPPED = 'stopped'


class AlarmSeverityEnum(str, PyEnum):
    """告警严重程度枚举"""
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
