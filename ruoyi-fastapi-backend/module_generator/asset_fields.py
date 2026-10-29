"""Explicit generated asset fields; never inferred from column names.

A declared field is a logical relation bound through the file asset module: no business column, no URL CSV.
The generated server policy, DTOs and the four page templates are all rendered from the same declaration.
"""

import math
import re

from pydantic.alias_generators import to_camel, to_snake

from config.env import FileAssetConfig
from exceptions.exception import ServiceException
from modules.file_assets.ports import MAX_ATTACHMENT_BYTES, MAX_IMAGE_BYTES, validate_type_ids

# Physical upload columns stored URL strings; generated code only supports logical file fields (hard cut-over).
PHYSICAL_UPLOAD_HTML_TYPES = frozenset({'imageUpload', 'fileUpload'})
FIELD_NAME = re.compile(r'^[a-z][A-Za-z0-9]{0,39}$')
RESERVED_NAMES = frozenset({'params', 'page', 'pageSize', 'beginTime', 'endTime'})
# Labels are pasted into generated Python, JS, HTML and Markdown; keep them to plain display text.
LABEL_FORBIDDEN = re.compile(r'[\'"\\`<>{}$\r\n]')
# sys_file_asset.purpose / intended_owner_type and sys_file_binding.owner_type are VARCHAR(64).
MAX_PURPOSE_LENGTH = 64
MIB = 1024 * 1024


def _fail(table, message: str):
    raise ServiceException(message=f'{table.table_name}: {message}')


def _reject_physical_upload_columns(table) -> None:
    for current in [table] + ([table.sub_table] if table.sub_table else []):
        for column in current.columns or []:
            if column.html_type in PHYSICAL_UPLOAD_HTML_TYPES:
                _fail(
                    current,
                    f'{column.column_name} 是物理列，不能直接作为文件字段，请改为声明逻辑文件字段',
                )


def _check_field(table, field, taken: set[str], column_names: set[str]) -> None:
    name = field.field_name
    if not FIELD_NAME.match(name) or to_camel(to_snake(name)) != name:
        _fail(table, f'文件字段名 {name!r} 需为 camelCase 标识（字母开头，最多 40 字符）')
    if name in taken or name in RESERVED_NAMES or to_snake(name) in column_names:
        _fail(table, f'文件字段名 {name} 与实际字段、派生字段或保留名冲突')
    if not field.label.strip() or len(field.label) > 50:
        _fail(table, f'文件字段 {name} 的标签不能为空且不超过 50 字符')
    if LABEL_FORBIDDEN.search(field.label):
        _fail(table, f'文件字段 {name} 的标签不能包含引号、反斜杠、尖括号、花括号、$ 或换行')
    purpose = f'{table.module_name}.{table.business_name}.{name}'
    if len(purpose) > MAX_PURPOSE_LENGTH:
        _fail(table, f'文件字段用途 {purpose} 超过 {MAX_PURPOSE_LENGTH} 字符，请缩短模块名、业务名或字段名')
    try:
        field.allowed_type_ids = list(validate_type_ids(field.allowed_type_ids, image_only=field.asset_kind == 'image'))
    except ValueError as exc:
        _fail(table, f'文件字段 {name} 的类型声明无效：{exc}')
    ceiling = MAX_IMAGE_BYTES if field.asset_kind == 'image' else MAX_ATTACHMENT_BYTES
    if not 0 < field.max_bytes <= ceiling:
        _fail(table, f'文件字段 {name} 的单个大小上限需在 1 字节至 {ceiling // MIB} MiB 之间')
    if not 0 < field.max_count <= FileAssetConfig.file_asset_draft_quota_count:
        _fail(table, f'文件字段 {name} 的数量需在 1 至 {FileAssetConfig.file_asset_draft_quota_count} 之间')


def validate_asset_fields(table) -> None:
    """Configuration errors fail generation; nothing defaults to an open type set or open permissions."""
    _reject_physical_upload_columns(table)
    if table.sub_table is not None and table.sub_table.asset_fields:
        _fail(table.sub_table, '子表行不能拥有文件字段，请在主表声明')
    fields = table.asset_fields or []
    if not fields:
        return
    columns = table.columns or []
    taken = {name for column in columns for name in (column.python_field, to_camel(column.column_name or ''))}
    taken |= {f'{column.python_field}Text' for column in columns if column.html_type == 'remark'}
    if table.sub_table is not None:
        taken.add(f'{(table.sub_table.class_name or "").lower()}List')
    column_names = {column.column_name for column in columns}
    for field in fields:
        _check_field(table, field, taken, column_names)
        taken.add(field.field_name)
    # One form can stage every field at its limits; that must fit the uploader's draft quota.
    total_bytes = sum(field.max_bytes * field.max_count for field in fields)
    total_count = sum(field.max_count for field in fields)
    quota_bytes, quota_count = (
        FileAssetConfig.file_asset_draft_quota_bytes,
        FileAssetConfig.file_asset_draft_quota_count,
    )
    if total_bytes > quota_bytes or total_count > quota_count:
        _fail(
            table,
            f'同一表单文件字段容量之和（{total_count} 个 / {total_bytes / MIB:.1f} MiB）超过用户草稿配额'
            f'（{quota_count} 个 / {quota_bytes / MIB:.0f} MiB），请调小数量或大小',
        )


def asset_template_context(table, permission_prefix: str) -> dict:
    """Template context derived from the declaration only (purposes, owner type, permissions)."""
    owner_type = f'{table.module_name}.{table.business_name}'
    fields = [
        {
            'name': field.field_name,
            'attr': to_snake(field.field_name),
            'const': to_snake(field.field_name).upper(),
            'label': field.label,
            'kind': field.asset_kind,
            'typeIds': list(field.allowed_type_ids),
            'maxBytes': field.max_bytes,
            'maxCount': field.max_count,
            # Client hint only (the server enforces bytes): round up so it never rejects an allowed file.
            'sizeMb': max(math.ceil(field.max_bytes / MIB * 100) / 100, 0.01),
            'required': field.required,
            'list': field.show_in_list,
            'purpose': f'{owner_type}.{field.field_name}',
        }
        for field in table.asset_fields or []
    ]
    return {
        'hasAssets': bool(fields),
        'assetFields': fields,
        'assetOwnerType': owner_type,
        'assetCreatePermission': f'{permission_prefix}:add',
        'assetEditPermission': f'{permission_prefix}:edit',
        'assetReadPermissions': [f'{permission_prefix}:list', f'{permission_prefix}:query'],
    }
