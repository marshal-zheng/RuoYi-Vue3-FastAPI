"""性能优化索引

Revision ID: 20260127_perf_idx
Revises: 20260127_add_create_time
Create Date: 2026-01-27 14:00:00.000000

P1-001~006: 创建性能优化索引
- 用户表索引
- 部门表索引
- 角色表索引
- 菜单表索引
- 日志表索引
- 关联表索引

索引命名规范：
- 单列索引: idx_{table}_{column}
- 复合索引: idx_{table}_{col1}_{col2}
- 唯一索引: uk_{table}_{column}
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20260127_perf_idx'
down_revision = '20260127_add_create_time'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    创建性能优化索引
    
    注意：使用 IF NOT EXISTS 语法避免重复创建错误
    """
    # ========================================================================
    # 兼容处理：MySQL 不支持 CREATE INDEX IF NOT EXISTS
    # ========================================================================
    def _index_exists(table_name: str, index_name: str) -> bool:
        conn = op.get_bind()
        inspector = inspect(conn)
        for idx in inspector.get_indexes(table_name):
            if idx.get('name') == index_name:
                return True
        return False

    def create_index(name, table_name, columns, **kw):
        if _index_exists(table_name, name):
            return
        kw.pop('if_not_exists', None)
        op.create_index(name, table_name, columns, **kw)

    # ========================================================================
    # P1-001: 用户表索引
    # ========================================================================
    
    # 登录查询优化：用户名 + 状态 + 删除标志
    create_index(
        'idx_user_username_status',
        'sys_user',
        ['user_name', 'status', 'del_flag'],
        unique=False,
        if_not_exists=True
    )
    
    # 部门查询优化
    create_index(
        'idx_user_dept',
        'sys_user',
        ['dept_id'],
        unique=False,
        if_not_exists=True
    )
    
    # 手机号查询
    create_index(
        'idx_user_phone',
        'sys_user',
        ['phonenumber'],
        unique=False,
        if_not_exists=True
    )
    
    # 邮箱查询
    create_index(
        'idx_user_email',
        'sys_user',
        ['email'],
        unique=False,
        if_not_exists=True
    )
    
    # 状态筛选
    create_index(
        'idx_user_status_delflag',
        'sys_user',
        ['status', 'del_flag'],
        unique=False,
        if_not_exists=True
    )
    
    # 创建时间排序（降序）
    create_index(
        'idx_user_create_time',
        'sys_user',
        [sa.text('create_time DESC')],
        unique=False,
        if_not_exists=True
    )
    
    # ========================================================================
    # P1-002: 部门表索引
    # ========================================================================
    
    # 父部门查询
    create_index(
        'idx_dept_parent',
        'sys_dept',
        ['parent_id'],
        unique=False,
        if_not_exists=True
    )
    
    # 祖先路径查询（用于查找子部门）
    create_index(
        'idx_dept_ancestors',
        'sys_dept',
        ['ancestors'],
        unique=False,
        if_not_exists=True
    )
    
    # 状态筛选
    create_index(
        'idx_dept_status_delflag',
        'sys_dept',
        ['status', 'del_flag'],
        unique=False,
        if_not_exists=True
    )
    
    # 排序优化
    create_index(
        'idx_dept_order',
        'sys_dept',
        ['order_num'],
        unique=False,
        if_not_exists=True
    )
    
    # ========================================================================
    # P1-003: 角色表索引
    # ========================================================================
    
    # 角色键查询
    create_index(
        'idx_role_key',
        'sys_role',
        ['role_key'],
        unique=False,
        if_not_exists=True
    )
    
    # 状态筛选
    create_index(
        'idx_role_status_delflag',
        'sys_role',
        ['status', 'del_flag'],
        unique=False,
        if_not_exists=True
    )
    
    # 排序优化
    create_index(
        'idx_role_sort',
        'sys_role',
        ['role_sort'],
        unique=False,
        if_not_exists=True
    )
    
    # ========================================================================
    # P1-003: 菜单表索引
    # ========================================================================
    
    # 父菜单查询
    create_index(
        'idx_menu_parent',
        'sys_menu',
        ['parent_id'],
        unique=False,
        if_not_exists=True
    )
    
    # 菜单类型筛选
    create_index(
        'idx_menu_type_status',
        'sys_menu',
        ['menu_type', 'status'],
        unique=False,
        if_not_exists=True
    )
    
    # 权限标识查询
    create_index(
        'idx_menu_perms',
        'sys_menu',
        ['perms'],
        unique=False,
        if_not_exists=True
    )
    
    # 排序优化
    create_index(
        'idx_menu_order',
        'sys_menu',
        ['order_num'],
        unique=False,
        if_not_exists=True
    )
    
    # ========================================================================
    # P1-004: 日志表索引（部分索引已在模型中定义）
    # ========================================================================
    
    # 操作日志 - 操作人查询
    create_index(
        'idx_operlog_name',
        'sys_oper_log',
        ['oper_name'],
        unique=False,
        if_not_exists=True
    )
    
    # 操作日志 - 标题查询
    create_index(
        'idx_operlog_title',
        'sys_oper_log',
        ['title'],
        unique=False,
        if_not_exists=True
    )
    
    # 登录日志 - 用户名查询
    create_index(
        'idx_loginlog_username',
        'sys_logininfor',
        ['user_name'],
        unique=False,
        if_not_exists=True
    )
    
    # 登录日志 - IP地址查询
    create_index(
        'idx_loginlog_ipaddr',
        'sys_logininfor',
        ['ipaddr'],
        unique=False,
        if_not_exists=True
    )
    
    # ========================================================================
    # P1-005: 关联表索引
    # ========================================================================
    
    # 用户角色关联 - 双向查询优化
    create_index(
        'idx_user_role_user',
        'sys_user_role',
        ['user_id'],
        unique=False,
        if_not_exists=True
    )
    
    create_index(
        'idx_user_role_role',
        'sys_user_role',
        ['role_id'],
        unique=False,
        if_not_exists=True
    )
    
    # 用户岗位关联
    create_index(
        'idx_user_post_user',
        'sys_user_post',
        ['user_id'],
        unique=False,
        if_not_exists=True
    )
    
    create_index(
        'idx_user_post_post',
        'sys_user_post',
        ['post_id'],
        unique=False,
        if_not_exists=True
    )
    
    # 角色菜单关联
    create_index(
        'idx_role_menu_role',
        'sys_role_menu',
        ['role_id'],
        unique=False,
        if_not_exists=True
    )
    
    create_index(
        'idx_role_menu_menu',
        'sys_role_menu',
        ['menu_id'],
        unique=False,
        if_not_exists=True
    )
    
    # 角色部门关联
    create_index(
        'idx_role_dept_role',
        'sys_role_dept',
        ['role_id'],
        unique=False,
        if_not_exists=True
    )
    
    create_index(
        'idx_role_dept_dept',
        'sys_role_dept',
        ['dept_id'],
        unique=False,
        if_not_exists=True
    )
    
    # ========================================================================
    # 岗位表索引
    # ========================================================================
    
    create_index(
        'idx_post_code',
        'sys_post',
        ['post_code'],
        unique=False,
        if_not_exists=True
    )
    
    create_index(
        'idx_post_status',
        'sys_post',
        ['status'],
        unique=False,
        if_not_exists=True
    )
    
    # ========================================================================
    # 字典表索引
    # ========================================================================
    
    create_index(
        'idx_dict_type_type',
        'sys_dict_type',
        ['dict_type'],
        unique=False,
        if_not_exists=True
    )
    
    create_index(
        'idx_dict_data_type',
        'sys_dict_data',
        ['dict_type'],
        unique=False,
        if_not_exists=True
    )
    
    create_index(
        'idx_dict_data_status',
        'sys_dict_data',
        ['status'],
        unique=False,
        if_not_exists=True
    )
    
    # ========================================================================
    # 配置表索引
    # ========================================================================
    
    create_index(
        'idx_config_key',
        'sys_config',
        ['config_key'],
        unique=False,
        if_not_exists=True
    )
    
    # ========================================================================
    # 定时任务表索引
    # ========================================================================
    
    create_index(
        'idx_job_status',
        'sys_job',
        ['status'],
        unique=False,
        if_not_exists=True
    )
    
    create_index(
        'idx_job_group',
        'sys_job',
        ['job_group'],
        unique=False,
        if_not_exists=True
    )
    
    create_index(
        'idx_job_log_name',
        'sys_job_log',
        ['job_name'],
        unique=False,
        if_not_exists=True
    )
    
    create_index(
        'idx_job_log_group',
        'sys_job_log',
        ['job_group'],
        unique=False,
        if_not_exists=True
    )
    
    create_index(
        'idx_job_log_status',
        'sys_job_log',
        ['status'],
        unique=False,
        if_not_exists=True
    )


def downgrade() -> None:
    """
    删除性能优化索引
    """
    # 定时任务表索引
    op.drop_index('idx_job_log_status', table_name='sys_job_log', if_exists=True)
    op.drop_index('idx_job_log_group', table_name='sys_job_log', if_exists=True)
    op.drop_index('idx_job_log_name', table_name='sys_job_log', if_exists=True)
    op.drop_index('idx_job_group', table_name='sys_job', if_exists=True)
    op.drop_index('idx_job_status', table_name='sys_job', if_exists=True)
    
    # 配置表索引
    op.drop_index('idx_config_key', table_name='sys_config', if_exists=True)
    
    # 字典表索引
    op.drop_index('idx_dict_data_status', table_name='sys_dict_data', if_exists=True)
    op.drop_index('idx_dict_data_type', table_name='sys_dict_data', if_exists=True)
    op.drop_index('idx_dict_type_type', table_name='sys_dict_type', if_exists=True)
    
    # 岗位表索引
    op.drop_index('idx_post_status', table_name='sys_post', if_exists=True)
    op.drop_index('idx_post_code', table_name='sys_post', if_exists=True)
    
    # 关联表索引
    op.drop_index('idx_role_dept_dept', table_name='sys_role_dept', if_exists=True)
    op.drop_index('idx_role_dept_role', table_name='sys_role_dept', if_exists=True)
    op.drop_index('idx_role_menu_menu', table_name='sys_role_menu', if_exists=True)
    op.drop_index('idx_role_menu_role', table_name='sys_role_menu', if_exists=True)
    op.drop_index('idx_user_post_post', table_name='sys_user_post', if_exists=True)
    op.drop_index('idx_user_post_user', table_name='sys_user_post', if_exists=True)
    op.drop_index('idx_user_role_role', table_name='sys_user_role', if_exists=True)
    op.drop_index('idx_user_role_user', table_name='sys_user_role', if_exists=True)
    
    # 日志表索引
    op.drop_index('idx_loginlog_ipaddr', table_name='sys_logininfor', if_exists=True)
    op.drop_index('idx_loginlog_username', table_name='sys_logininfor', if_exists=True)
    op.drop_index('idx_operlog_title', table_name='sys_oper_log', if_exists=True)
    op.drop_index('idx_operlog_name', table_name='sys_oper_log', if_exists=True)
    
    # 菜单表索引
    op.drop_index('idx_menu_order', table_name='sys_menu', if_exists=True)
    op.drop_index('idx_menu_perms', table_name='sys_menu', if_exists=True)
    op.drop_index('idx_menu_type_status', table_name='sys_menu', if_exists=True)
    op.drop_index('idx_menu_parent', table_name='sys_menu', if_exists=True)
    
    # 角色表索引
    op.drop_index('idx_role_sort', table_name='sys_role', if_exists=True)
    op.drop_index('idx_role_status_delflag', table_name='sys_role', if_exists=True)
    op.drop_index('idx_role_key', table_name='sys_role', if_exists=True)
    
    # 部门表索引
    op.drop_index('idx_dept_order', table_name='sys_dept', if_exists=True)
    op.drop_index('idx_dept_status_delflag', table_name='sys_dept', if_exists=True)
    op.drop_index('idx_dept_ancestors', table_name='sys_dept', if_exists=True)
    op.drop_index('idx_dept_parent', table_name='sys_dept', if_exists=True)
    
    # 用户表索引
    op.drop_index('idx_user_create_time', table_name='sys_user', if_exists=True)
    op.drop_index('idx_user_status_delflag', table_name='sys_user', if_exists=True)
    op.drop_index('idx_user_email', table_name='sys_user', if_exists=True)
    op.drop_index('idx_user_phone', table_name='sys_user', if_exists=True)
    op.drop_index('idx_user_dept', table_name='sys_user', if_exists=True)
    op.drop_index('idx_user_username_status', table_name='sys_user', if_exists=True)
