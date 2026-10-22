"""Seven generic remark columns use the frozen Document v2 codec.

Revision ID: 20261022_remark_v2
Revises: 20261017_dashboard
"""

import sqlalchemy as sa

from alembic import op
from scripts.data_migrations.remark_document_v2 import migrate

revision = '20261022_remark_v2'
down_revision = '20261017_dashboard'
branch_labels = None
depends_on = None


GEN_TABLE_COMMENTS = {
    'table_id': '编号',
    'table_name': '表名称',
    'table_comment': '表描述',
    'sub_table_name': '关联子表的表名',
    'sub_table_fk_name': '子表关联的外键名',
    'class_name': '实体类名称',
    'tpl_category': '使用的模板（crud单表操作 tree树表操作）',
    'tpl_web_type': '前端模板类型（element-ui模版 element-plus模版）',
    'package_name': '生成包路径',
    'module_name': '生成模块名',
    'business_name': '生成业务名',
    'function_name': '生成功能名',
    'function_author': '生成功能作者',
    'gen_type': '生成代码方式（0zip压缩包 1自定义路径）',
    'gen_path': '生成路径（不填默认项目路径）',
    'options': '其它生成选项',
    'create_by': '创建者',
    'create_time': '创建时间',
    'update_by': '更新者',
    'update_time': '更新时间',
    'remark': '备注文档',
}
GEN_COLUMN_COMMENTS = {
    'column_id': '编号',
    'table_id': '归属表编号',
    'column_name': '列名称',
    'column_comment': '列描述',
    'column_type': '列类型',
    'python_type': 'PYTHON类型',
    'python_field': 'PYTHON字段名',
    'is_pk': '是否主键（1是）',
    'is_increment': '是否自增（1是）',
    'is_required': '是否必填（1是）',
    'is_unique': '是否唯一（1是）',
    'is_insert': '是否为插入字段（1是）',
    'is_edit': '是否编辑字段（1是）',
    'is_list': '是否列表字段（1是）',
    'is_query': '是否查询字段（1是）',
    'query_type': '查询方式（等于、不等于、大于、小于、范围）',
    'html_type': '显示类型（文本框、文本域、下拉框、复选框、单选框、日期控件）',
    'dict_type': '字典类型',
    'sort': '排序',
    'create_by': '创建者',
    'create_time': '创建时间',
    'update_by': '更新者',
    'update_time': '更新时间',
}


def upgrade():
    options = dict(op.get_context().config.attributes.get('remark_migration', {}))
    # Run backup/freeze admission before even adding the missing generator table.
    # Each DDL and batch checkpoint is durable in both supported dialects.
    with op.get_context().autocommit_block():
        migrate(op.get_bind(), **options)
    bind = op.get_bind()
    # The original initial revision omitted these existing generator models.
    # Freeze their shape here, instead of importing a future business ORM.
    if not sa.inspect(bind).has_table('gen_table'):
        columns = [sa.Column('table_id', sa.Integer, primary_key=True, autoincrement=True)]
        for name, length in {
            'table_name': 200,
            'table_comment': 500,
            'sub_table_name': 64,
            'sub_table_fk_name': 64,
            'class_name': 100,
            'tpl_category': 200,
            'tpl_web_type': 30,
            'package_name': 100,
            'module_name': 30,
            'business_name': 30,
            'function_name': 100,
            'function_author': 100,
            'gen_type': 1,
            'gen_path': 200,
            'options': 1000,
            'create_by': 64,
            'update_by': 64,
        }.items():
            columns.append(sa.Column(name, sa.String(length), nullable=True))
        columns.extend(
            [
                sa.Column('create_time', sa.DateTime),
                sa.Column('update_time', sa.DateTime),
                sa.Column('remark', sa.JSON(none_as_null=True), nullable=True),
            ]
        )
        for column in columns:
            column.comment = GEN_TABLE_COMMENTS[column.name]
        op.create_table('gen_table', *columns)
    if not sa.inspect(bind).has_table('gen_table_column'):
        columns = [
            sa.Column('column_id', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('table_id', sa.Integer, sa.ForeignKey('gen_table.table_id')),
            sa.Column('sort', sa.Integer),
        ]
        for name, length in {
            'column_name': 200,
            'column_comment': 500,
            'column_type': 100,
            'python_type': 500,
            'python_field': 200,
            'is_pk': 1,
            'is_increment': 1,
            'is_required': 1,
            'is_unique': 1,
            'is_insert': 1,
            'is_edit': 1,
            'is_list': 1,
            'is_query': 1,
            'query_type': 200,
            'html_type': 200,
            'dict_type': 200,
            'create_by': 64,
            'update_by': 64,
        }.items():
            columns.append(sa.Column(name, sa.String(length), nullable=True))
        columns.extend([sa.Column('create_time', sa.DateTime), sa.Column('update_time', sa.DateTime)])
        for column in columns:
            column.comment = GEN_COLUMN_COMMENTS[column.name]
        op.create_table('gen_table_column', *columns)


def downgrade():
    raise RuntimeError(
        'Remark downgrade would lose formatting. Stop writers and restore a verified complete snapshot with matching old code; see the remark upgrade/recovery guide.'
    )
