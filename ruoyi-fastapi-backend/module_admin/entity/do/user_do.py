from sqlalchemy import Column, DateTime, Integer, String
from module_admin.entity.do.base import LegacyBaseModel, RelationBaseModel
from module_admin.entity.do.enums import UserTypeEnum, GenderEnum, StatusEnum, DelFlagEnum
from utils.sensitive import sensitive_string_with_hash


class SysUser(LegacyBaseModel):
    """
    用户信息表
    """

    __tablename__ = 'sys_user'

    user_id = Column(Integer, primary_key=True, autoincrement=True, comment='用户ID')
    dept_id = Column(Integer, default=None, comment='部门ID')
    user_name = Column(String(30), nullable=False, comment='用户账号')
    nick_name = Column(String(30), nullable=False, comment='用户昵称')
    user_type = Column(String(2), default=UserTypeEnum.SYSTEM.value, comment='用户类型（00系统用户）')
    email, email_hash = sensitive_string_with_hash('email', default='', comment='用户邮箱')
    phonenumber, phonenumber_hash = sensitive_string_with_hash('phonenumber', default='', comment='手机号码')
    id_card, id_card_hash = sensitive_string_with_hash('id_card', default='', comment='身份证号')
    sex = Column(String(1), default=GenderEnum.MALE.value, comment='用户性别（0男 1女 2未知）')
    avatar = Column(String(100), default='', comment='头像地址')
    password = Column(String(100), default='', comment='密码')
    status = Column(String(1), default=StatusEnum.NORMAL.value, comment='帐号状态（0正常 1停用）')
    del_flag = Column(String(1), default=DelFlagEnum.EXIST.value, comment='删除标志（0代表存在 2代表删除）')
    login_ip = Column(String(128), default='', comment='最后登录IP')
    login_date = Column(DateTime, comment='最后登录时间')
    remark = Column(String(500), default=None, comment='备注')


class SysUserRole(RelationBaseModel):
    """
    用户和角色关联表
    """

    __tablename__ = 'sys_user_role'

    user_id = Column(Integer, primary_key=True, nullable=False, comment='用户ID')
    role_id = Column(Integer, primary_key=True, nullable=False, comment='角色ID')


class SysUserPost(RelationBaseModel):
    """
    用户与岗位关联表
    """

    __tablename__ = 'sys_user_post'

    user_id = Column(Integer, primary_key=True, nullable=False, comment='用户ID')
    post_id = Column(Integer, primary_key=True, nullable=False, comment='岗位ID')


# Backward-compatible alias for tests/imports expecting UserDO
UserDO = SysUser
