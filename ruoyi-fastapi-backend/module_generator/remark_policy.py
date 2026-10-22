"""Explicit generated-field semantics; never infer them from field names or JSON."""

from pydantic.alias_generators import to_camel

from exceptions.exception import ServiceException


def validate_remark_generation(table, actual_columns=None):
    tables = [table] + ([table.sub_table] if table.sub_table else [])
    has_remark = any(c.html_type == 'remark' for t in tables for c in (t.columns or []))
    if not has_remark:
        return
    if table.tpl_web_type != 'element-plus':
        raise ServiceException(message='基础富文本备注仅支持 Vue3 / element-plus 模板，请改选 Vue3')
    for current in tables:
        column_names = {column.column_name for column in current.columns or []}
        client_names = {
            name
            for column in current.columns or []
            for name in (column.python_field, to_camel(column.column_name or ''))
        }
        reserved = {
            current.sub_table_fk_name,
            current.tree_code,
            current.tree_parent_code,
            current.tree_name,
            table.sub_table_fk_name if current is not table else None,
        }
        for column in current.columns or []:
            if column.html_type != 'remark':
                continue
            if f'{column.column_name}_text' in column_names or f'{column.python_field}Text' in client_names:
                raise ServiceException(
                    message=f'{current.table_name}.{column.column_name}: 只读派生字段与实际字段冲突，请调整字段名'
                )
            if (
                str(column.column_type).lower() != 'json'
                or column.is_required == '1'
                or column.is_pk == '1'
                or column.is_query == '1'
                or column.is_unique == '1'
                or column.column_name in reserved
                or column.python_field in reserved
            ):
                raise ServiceException(
                    message=f'{current.table_name}.{column.column_name}: 备注需要 nullable JSON，不能用于身份、关联、树、唯一或查询字段'
                )
            if actual_columns is not None:
                source = actual_columns.get(current.table_name, {}).get(column.column_name)
                if (
                    not source
                    or str(source.get('column_type')).lower() != 'json'
                    or str(source.get('is_required')) != '0'
                    or str(source.get('is_pk')) == '1'
                ):
                    raise ServiceException(
                        message=f'{current.table_name}.{column.column_name}: 实际数据库列必须是 nullable JSON;生成器不会自动改列'
                    )
