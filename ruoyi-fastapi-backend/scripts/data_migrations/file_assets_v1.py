"""Frozen hard cut-over to the file asset module; SQLAlchemy Core only.

Used by the Alembic revision (deploy) and by dev-sync for the maintenance jobs. The cut-over migrates no
history (user decision 2026-10-27): it creates the asset and binding tables, adds the generator's logical
file field declarations (`gen_table.asset_fields`), drops `sys_user.avatar` (avatars fall back to the
default) and converts notice content to UTF-8 text in place. Old `/profile/...` images inside notice HTML
are not rewritten; they stop resolving and must be re-uploaded before such a notice can be saved again.
The retired upload directory stays on disk untouched. All steps are idempotent.

No current ORM or DTO imports: this module must keep meaning the same after the application code moves on.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

if TYPE_CHECKING:
    from sqlalchemy.engine import Connection

ASSET_TABLE = 'sys_file_asset'
BINDING_TABLE = 'sys_file_binding'
GEN_ASSET_FIELDS_COLUMN = 'asset_fields'
BINARY_TYPES = ('BLOB', 'LONGBLOB', 'MEDIUMBLOB', 'TINYBLOB', 'BYTEA', 'BINARY', 'VARBINARY', 'LARGEBINARY')

UTC_DATETIME = sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mysql')
AUTO_BIGINT = sa.BigInteger().with_variant(sa.Integer, 'sqlite')


def gen_asset_fields_column() -> sa.Column:
    """Frozen DDL for `gen_table.asset_fields`, added by this revision on top of the 20261022 generator shape."""
    return sa.Column(GEN_ASSET_FIELDS_COLUMN, sa.JSON(), nullable=True, comment='逻辑文件字段声明')


MAINTENANCE_JOBS = (
    (
        '文件资产-回收与删除',
        'modules.file_assets.jobs.maintain',
        '0 * * * * ?',
        '每分钟：草稿到期/上传遗弃/失败记录认领为待删除，并按资产状态执行到期删除（失败持久化退避）',
    ),
    (
        '文件资产-孤儿对象清扫',
        'modules.file_assets.jobs.sweep_orphans',
        '0 30 3 * * ?',
        '每日：列举当前与上一月前缀，删除宽限期后记录为 FAILED/DELETED 的对象，备份恢复窗口请暂停',
    ),
    (
        '文件资产-墓碑清除',
        'modules.file_assets.jobs.purge_tombstones',
        '0 0 4 * * ?',
        '每日：清除已确认删除满保留期的 DELETED 记录',
    ),
)


def frozen_tables(metadata: sa.MetaData) -> tuple[sa.Table, sa.Table]:
    asset = sa.Table(
        ASSET_TABLE,
        metadata,
        sa.Column('asset_id', sa.CHAR(36), primary_key=True, comment='资产ID（UUID）'),
        sa.Column('bucket', sa.String(63), nullable=False, comment='对象存储桶'),
        sa.Column('object_key', sa.String(255), nullable=False, comment='不可变对象键'),
        sa.Column('original_name', sa.String(255), nullable=False, comment='原始文件名'),
        sa.Column('display_name', sa.String(255), nullable=False, comment='安全显示名'),
        sa.Column('media_type', sa.String(127), nullable=True, comment='登记的规范媒体类型'),
        sa.Column('content_disposition', sa.String(16), nullable=False, comment='交付方式（inline/attachment）'),
        sa.Column('size_bytes', sa.BigInteger, nullable=True, comment='存储字节数'),
        sa.Column('sha256', sa.CHAR(64), nullable=True, comment='存储字节SHA-256'),
        sa.Column('uploader_id', sa.BigInteger, nullable=False, comment='上传者用户ID'),
        sa.Column('purpose', sa.String(64), nullable=False, comment='上传用途'),
        sa.Column('intended_owner_type', sa.String(64), nullable=False, comment='意图归属业务类型'),
        sa.Column('intended_owner_id', sa.String(128), nullable=True, comment='意图归属业务ID'),
        sa.Column('state', sa.String(16), nullable=False, comment='状态（UPLOADING/READY/FAILED/DELETING/DELETED）'),
        sa.Column('created_at', UTC_DATETIME, nullable=False, comment='创建时间（UTC）'),
        sa.Column('updated_at', UTC_DATETIME, nullable=False, comment='更新时间（UTC）'),
        sa.Column('uploaded_at', UTC_DATETIME, nullable=True, comment='READY提交时间（UTC）'),
        sa.Column('first_bound_at', UTC_DATETIME, nullable=True, comment='首次绑定时间（UTC）'),
        sa.Column('upload_deadline', UTC_DATETIME, nullable=False, comment='上传状态截止时间（UTC）'),
        sa.Column('expires_at', UTC_DATETIME, nullable=True, comment='草稿到期时间（UTC）'),
        sa.Column('delete_after', UTC_DATETIME, nullable=True, comment='删除到期时间（UTC）'),
        sa.Column('deleted_at', UTC_DATETIME, nullable=True, comment='删除确认时间（UTC）'),
        sa.Column('delete_next_attempt_at', UTC_DATETIME, nullable=True, comment='下次删除执行时间（租约或退避）'),
        sa.Column('delete_attempts', sa.Integer, nullable=False, server_default='0', comment='对象级删除失败次数'),
        sa.Column('delete_failing_since', UTC_DATETIME, nullable=True, comment='持续删除失败起点（UTC）'),
        sa.Column('last_error_code', sa.String(64), nullable=True, comment='脱敏错误码'),
        sa.Column('last_error_at', UTC_DATETIME, nullable=True, comment='最近错误时间（UTC）'),
        sa.UniqueConstraint('bucket', 'object_key', name='uq_sys_file_asset_bucket_object_key'),
        sa.Index('ix_sys_file_asset_state_expires_at', 'state', 'expires_at'),
        sa.Index('ix_sys_file_asset_state_upload_deadline', 'state', 'upload_deadline'),
        sa.Index('ix_sys_file_asset_state_delete_after', 'state', 'delete_after'),
        sa.Index('ix_sys_file_asset_state_delete_next_attempt_at', 'state', 'delete_next_attempt_at'),
        sa.Index('ix_sys_file_asset_state_deleted_at', 'state', 'deleted_at'),
        sa.Index('ix_sys_file_asset_uploader_state_first_bound_at', 'uploader_id', 'state', 'first_bound_at'),
        comment='文件资产表',
    )
    binding = sa.Table(
        BINDING_TABLE,
        metadata,
        sa.Column('binding_id', AUTO_BIGINT, primary_key=True, autoincrement=True, comment='绑定ID'),
        sa.Column(
            'asset_id',
            sa.CHAR(36),
            sa.ForeignKey(f'{ASSET_TABLE}.asset_id', ondelete='RESTRICT', name='fk_sys_file_binding_asset_id'),
            nullable=False,
            comment='资产ID',
        ),
        sa.Column('owner_type', sa.String(64), nullable=False, comment='归属业务类型'),
        sa.Column('owner_id', sa.String(128), nullable=False, comment='归属业务ID（规范化字符串）'),
        sa.Column('field_key', sa.String(64), nullable=False, comment='归属字段'),
        sa.Column('position', sa.Integer, nullable=False, comment='字段内顺序（从0开始）'),
        sa.Column('created_at', UTC_DATETIME, nullable=False, comment='绑定时间（UTC）'),
        sa.Column('created_by', sa.BigInteger, nullable=False, comment='绑定操作者用户ID'),
        sa.UniqueConstraint('asset_id', name='uq_sys_file_binding_asset_id'),
        sa.UniqueConstraint(
            'owner_type', 'owner_id', 'field_key', 'position', name='uq_sys_file_binding_owner_field_position'
        ),
        sa.Index('ix_sys_file_binding_owner_field', 'owner_type', 'owner_id', 'field_key'),
        comment='文件资产业务绑定表',
    )
    return asset, binding


def _has_column(connection: Connection, table: str, column: str) -> bool:
    inspector = sa.inspect(connection)
    if not inspector.has_table(table):
        return False
    return any(item['name'] == column for item in inspector.get_columns(table))


def _column_type(connection: Connection, table: str, column: str) -> str | None:
    inspector = sa.inspect(connection)
    if not inspector.has_table(table):
        return None
    for item in inspector.get_columns(table):
        if item['name'] == column:
            return type(item['type']).__name__.upper()
    return None


def notice_content_is_binary(connection: Connection) -> bool:
    kind = _column_type(connection, 'sys_notice', 'notice_content')
    return kind is not None and kind.upper() in BINARY_TYPES


def _commit(connection: Connection) -> None:
    # MySQL commits DDL implicitly; inside Alembic's autocommit block the proxy owns the transaction.
    if connection.get_execution_options().get('isolation_level') != 'AUTOCOMMIT' and connection.in_transaction():
        connection.commit()


def ensure_maintenance_jobs(connection: Connection) -> int:
    """Seed the three disabled-concurrency maintenance jobs once; operators may pause them in the job UI."""
    if not sa.inspect(connection).has_table('sys_job'):
        return 0
    job = sa.table(
        'sys_job',
        sa.column('job_name'),
        sa.column('job_group'),
        sa.column('job_executor'),
        sa.column('invoke_target'),
        sa.column('job_args'),
        sa.column('job_kwargs'),
        sa.column('cron_expression'),
        sa.column('misfire_policy'),
        sa.column('concurrent'),
        sa.column('status'),
        sa.column('remark'),
        sa.column('create_by'),
        sa.column('create_time'),
    )
    existing = set(connection.execute(sa.select(job.c.invoke_target)).scalars())
    inserted = 0
    for name, target, cron, remark in MAINTENANCE_JOBS:
        if target in existing:
            continue
        connection.execute(
            job.insert().values(
                job_name=name,
                job_group='default',
                job_executor='default',
                invoke_target=target,
                job_args='',
                job_kwargs='',
                cron_expression=cron,
                misfire_policy='3',
                concurrent='1',
                status='0',
                remark=remark,
                create_by='file-assets-cutover',
                create_time=datetime.now(),
            )
        )
        inserted += 1
    _commit(connection)
    return inserted


def upgrade(connection: Connection) -> dict[str, object]:
    report: dict[str, object] = {
        'createdTables': [],
        'genAssetFieldsColumn': False,
        'droppedAvatar': False,
        'noticeConverted': False,
        'jobsSeeded': 0,
    }
    metadata = sa.MetaData()
    inspector = sa.inspect(connection)
    for table in frozen_tables(metadata):
        if not inspector.has_table(table.name):
            table.create(connection)
            report['createdTables'].append(table.name)
    _commit(connection)
    if inspector.has_table('gen_table') and not _has_column(connection, 'gen_table', GEN_ASSET_FIELDS_COLUMN):
        column = gen_asset_fields_column()
        ddl = sa.schema.CreateColumn(column).compile(dialect=connection.dialect)
        connection.execute(sa.text(f'ALTER TABLE gen_table ADD COLUMN {ddl}'))
        _commit(connection)
        report['genAssetFieldsColumn'] = True
    # The only data-dependent step runs before anything destructive, so bad bytes stop the cut-over early.
    if notice_content_is_binary(connection):
        _convert_notice_content(connection)
        _commit(connection)
        report['noticeConverted'] = True
    if _has_column(connection, 'sys_user', 'avatar'):
        connection.execute(sa.text('ALTER TABLE sys_user DROP COLUMN avatar'))
        _commit(connection)
        report['droppedAvatar'] = True
    report['jobsSeeded'] = ensure_maintenance_jobs(connection)
    return report


class NoticeContentNotUtf8Error(RuntimeError):
    """Raised before any destructive step when stored notice bytes are not valid UTF-8."""


def invalid_utf8_notice_ids(connection: Connection, batch_size: int = 500) -> list[object]:
    """Strict Python decode of every stored notice; the server's sql_mode never decides correctness."""
    invalid: list[object] = []
    last_id = None
    while True:
        sql = 'SELECT notice_id, notice_content FROM sys_notice WHERE notice_content IS NOT NULL'
        params: dict[str, object] = {'limit': batch_size}
        if last_id is not None:
            sql += ' AND notice_id > :last_id'
            params['last_id'] = last_id
        rows = connection.execute(sa.text(f'{sql} ORDER BY notice_id LIMIT :limit'), params).all()
        for notice_id, content in rows:
            try:
                bytes(content).decode('utf-8')
            except UnicodeDecodeError:
                invalid.append(notice_id)
        if len(rows) < batch_size:
            return invalid
        last_id = rows[-1][0]


def _convert_notice_content(connection: Connection) -> None:
    """In-place UTF-8 conversion after a strict pre-scan; nothing is replaced, truncated or cleared."""
    invalid = invalid_utf8_notice_ids(connection)
    if invalid:
        raise NoticeContentNotUtf8Error(
            f'file-assets cut-over: sys_notice rows {invalid} are not valid UTF-8; fix them and re-run '
            '(no destructive step has been applied)'
        )
    comment = '公告内容（净化后的HTML）'
    if connection.dialect.name == 'mysql':
        # Belt and braces: a non-strict server would truncate at a bad byte with only a warning.
        connection.execute(
            sa.text("SET SESSION sql_mode = CONCAT_WS(',', NULLIF(@@SESSION.sql_mode, ''), 'STRICT_ALL_TABLES')")
        )
        connection.execute(
            sa.text(
                'ALTER TABLE sys_notice MODIFY COLUMN notice_content '
                f"MEDIUMTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '{comment}'"
            )
        )
    elif connection.dialect.name == 'postgresql':
        connection.execute(
            sa.text(
                'ALTER TABLE sys_notice ALTER COLUMN notice_content TYPE TEXT '
                "USING convert_from(notice_content, 'UTF8')"
            )
        )
    else:
        raise RuntimeError(f'file-assets cut-over: unsupported dialect {connection.dialect.name}')


def configured_engine():
    from config.env import DataBaseConfig  # noqa: PLC0415 - defer runtime settings

    driver = 'postgresql+psycopg2' if DataBaseConfig.db_type == 'postgresql' else 'mysql+pymysql'
    return sa.create_engine(
        sa.engine.URL.create(
            driver,
            username=DataBaseConfig.db_username,
            password=DataBaseConfig.db_password,
            host=DataBaseConfig.db_host,
            port=DataBaseConfig.db_port,
            database=DataBaseConfig.db_database,
        )
    )


def run_configured(step):
    engine = configured_engine()
    try:
        with engine.connect() as connection:
            result = step(connection)
            _commit(connection)
            return result
    finally:
        engine.dispose()
