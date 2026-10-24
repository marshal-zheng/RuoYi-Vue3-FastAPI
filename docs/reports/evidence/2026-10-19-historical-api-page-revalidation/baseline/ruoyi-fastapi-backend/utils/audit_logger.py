"""
审计日志记录器
基于 SQLAlchemy 事件记录读写审计
"""
import json
import random
from typing import Any, Dict, Iterable, List, Optional, Set
from sqlalchemy import event
from sqlalchemy.orm import Session
from sqlalchemy.inspection import inspect

from config.env import AuditConfig
from module_admin.entity.do.audit_log_do import AuditLogDO
from utils.audit_context import get_audit_context, append_read_audit
from utils.sensitive.registry import get_mask_fields


ACTION_READ = 'READ'
ACTION_INSERT = 'INSERT'
ACTION_UPDATE = 'UPDATE'
ACTION_DELETE = 'DELETE'


def _parse_config_set(value: str) -> Set[str]:
    return {item.strip().lower() for item in value.split(',') if item.strip()} if value else set()


AUDIT_TABLES = _parse_config_set(getattr(AuditConfig, 'audit_tables', ''))


def _get_mask_fields() -> Set[str]:
    return get_mask_fields(getattr(AuditConfig, 'audit_mask_fields', ''))


def _should_audit_table(table_name: Optional[str]) -> bool:
    if not table_name:
        return False
    if table_name.lower() == AuditLogDO.__tablename__:
        return False
    if not AUDIT_TABLES:
        return True
    return table_name.lower() in AUDIT_TABLES


def _safe_value(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, 'isoformat'):
        try:
            value = value.isoformat()
        except Exception:
            value = str(value)
    if isinstance(value, (str, int, float, bool)):
        text_value = str(value)
        max_len = getattr(AuditConfig, 'audit_max_value_length', 2000)
        if max_len and len(text_value) > max_len:
            return text_value[:max_len] + '...'
        return value

    text_value = str(value)
    max_len = getattr(AuditConfig, 'audit_max_value_length', 2000)
    if max_len and len(text_value) > max_len:
        return text_value[:max_len] + '...'
    return text_value


def _serialize_instance(obj) -> Dict[str, Any]:
    state = inspect(obj)
    data = {}
    exclude = set(getattr(obj, '__audit_exclude__', []) or [])
    mask_fields = _get_mask_fields()
    for attr in state.mapper.column_attrs:
        key = attr.key
        if key in exclude:
            continue
        value = getattr(obj, key, None)
        if key.lower() in mask_fields:
            data[key] = '***'
        else:
            data[key] = _safe_value(value)
    return data


def _collect_pk(obj) -> Dict[str, Any]:
    state = inspect(obj)
    pk_pairs = {}
    for col in state.mapper.primary_key:
        key = col.key
        pk_pairs[key] = getattr(obj, key, None)
    return pk_pairs


def _pk_to_str(pk_pairs: Dict[str, Any]) -> str:
    return json.dumps(pk_pairs, ensure_ascii=False)


def _pk_has_none(pk_pairs: Dict[str, Any]) -> bool:
    return any(value is None for value in pk_pairs.values())


def _diff_instance(obj) -> Dict[str, Any]:
    state = inspect(obj)
    before = {}
    after = {}
    changed_fields = []
    exclude = set(getattr(obj, '__audit_exclude__', []) or [])
    mask_fields = _get_mask_fields()
    for attr in state.mapper.column_attrs:
        key = attr.key
        if key in exclude:
            continue
        hist = state.attrs[key].history
        if not hist.has_changes():
            continue
        old_val = hist.deleted[0] if hist.deleted else getattr(obj, key, None)
        new_val = hist.added[0] if hist.added else getattr(obj, key, None)
        if key.lower() in mask_fields:
            before[key] = '***'
            after[key] = '***'
        else:
            before[key] = _safe_value(old_val)
            after[key] = _safe_value(new_val)
        changed_fields.append(key)
    return {
        'before': before,
        'after': after,
        'changed_fields': changed_fields,
    }


def _extract_table_names(statement) -> Set[str]:
    tables = set()
    try:
        froms = statement.get_final_froms()
    except Exception:
        return tables

    def _collect_from(obj) -> Set[str]:
        if obj is None:
            return set()
        if hasattr(obj, 'name') and obj.name:
            return {obj.name}
        if hasattr(obj, 'left') and hasattr(obj, 'right'):
            return _collect_from(obj.left) | _collect_from(obj.right)
        if hasattr(obj, 'element'):
            return _collect_from(obj.element)
        return set()

    for item in froms:
        tables.update(_collect_from(item))
    return tables


def _build_write_audit(entry: Dict[str, Any]) -> AuditLogDO:
    ctx = get_audit_context()
    return AuditLogDO(
        action=entry.get('action', ''),
        table_name=entry.get('table_name', ''),
        pk=entry.get('pk', ''),
        before_data=entry.get('before_data', ''),
        after_data=entry.get('after_data', ''),
        changed_fields=entry.get('changed_fields', ''),
        operator_id=ctx.get('user_id') or '',
        operator_name=ctx.get('user_name') or '',
        operator_ip=ctx.get('ip') or '',
        request_id=ctx.get('request_id') or '',
        trace_id=ctx.get('trace_id') or '',
        request_method=ctx.get('method') or '',
        request_path=ctx.get('path') or '',
        user_agent=ctx.get('user_agent') or '',
    )


_AUDIT_LOGGER_INITIALIZED = False


def init_audit_logger():
    global _AUDIT_LOGGER_INITIALIZED
    if _AUDIT_LOGGER_INITIALIZED:
        return
    if not AuditConfig.audit_enabled:
        return
    _AUDIT_LOGGER_INITIALIZED = True

    @event.listens_for(Session, 'before_flush')
    def before_flush(session, flush_context, instances):
        if not AuditConfig.audit_write_enabled:
            return
        if session.info.get('audit_in_progress'):
            return

        audit_entries: List[Dict[str, Any]] = []

        def _append_entry(obj, action: str):
            if isinstance(obj, AuditLogDO):
                return
            table_name = getattr(obj, '__tablename__', '')
            if not _should_audit_table(table_name):
                return

            if action == ACTION_INSERT:
                after_data = _serialize_instance(obj)
                audit_entries.append({
                    'action': ACTION_INSERT,
                    'table_name': table_name,
                    'pk': _pk_to_str(_collect_pk(obj)),
                    'pk_obj': obj,
                    'before_data': '',
                    'after_data': json.dumps(after_data, ensure_ascii=False),
                    'changed_fields': json.dumps(list(after_data.keys()), ensure_ascii=False),
                })
            elif action == ACTION_DELETE:
                before_data = _serialize_instance(obj)
                audit_entries.append({
                    'action': ACTION_DELETE,
                    'table_name': table_name,
                    'pk': _pk_to_str(_collect_pk(obj)),
                    'before_data': json.dumps(before_data, ensure_ascii=False),
                    'after_data': '',
                    'changed_fields': json.dumps(list(before_data.keys()), ensure_ascii=False),
                })
            elif action == ACTION_UPDATE:
                diff = _diff_instance(obj)
                if not diff['changed_fields']:
                    return
                audit_entries.append({
                    'action': ACTION_UPDATE,
                    'table_name': table_name,
                    'pk': _pk_to_str(_collect_pk(obj)),
                    'pk_obj': obj,
                    'before_data': json.dumps(diff['before'], ensure_ascii=False),
                    'after_data': json.dumps(diff['after'], ensure_ascii=False),
                    'changed_fields': json.dumps(diff['changed_fields'], ensure_ascii=False),
                })

        for obj in session.new:
            _append_entry(obj, ACTION_INSERT)
        for obj in session.deleted:
            _append_entry(obj, ACTION_DELETE)
        for obj in session.dirty:
            _append_entry(obj, ACTION_UPDATE)

        if audit_entries:
            session.info['audit_entries'] = audit_entries

    @event.listens_for(Session, 'after_flush')
    def after_flush(session, flush_context):
        if not AuditConfig.audit_write_enabled:
            return
        entries = session.info.pop('audit_entries', [])
        if not entries:
            return
        session.info['audit_in_progress'] = True
        try:
            for entry in entries:
                pk_obj = entry.pop('pk_obj', None)
                if pk_obj is not None:
                    pk_pairs = _collect_pk(pk_obj)
                    if not _pk_has_none(pk_pairs):
                        entry['pk'] = _pk_to_str(pk_pairs)
                session.add(_build_write_audit(entry))
        finally:
            session.info['audit_in_progress'] = False

    @event.listens_for(Session, 'do_orm_execute')
    def after_execute(orm_execute_state):
        if not AuditConfig.audit_read_enabled:
            return
        if not orm_execute_state.is_select:
            return
        if orm_execute_state.is_column_load or orm_execute_state.is_relationship_load:
            return
        if orm_execute_state.execution_options.get('audit_disabled'):
            return
        if AuditConfig.audit_read_sample_rate < 1.0:
            if random.random() > AuditConfig.audit_read_sample_rate:
                return

        tables = _extract_table_names(orm_execute_state.statement)
        if not tables:
            return

        sql_text = str(orm_execute_state.statement)
        max_len = getattr(AuditConfig, 'audit_max_value_length', 2000)
        if max_len and len(sql_text) > max_len:
            sql_text = sql_text[:max_len] + '...'

        for table in tables:
            if not _should_audit_table(table):
                continue
            ctx = get_audit_context()
            append_read_audit({
                'action': ACTION_READ,
                'table_name': table,
                'pk': '',
                'before_data': '',
                'after_data': '',
                'changed_fields': '',
                'query': sql_text,
                'operator_id': ctx.get('user_id') or '',
                'operator_name': ctx.get('user_name') or '',
                'operator_ip': ctx.get('ip') or '',
                'request_id': ctx.get('request_id') or '',
                'trace_id': ctx.get('trace_id') or '',
                'request_method': ctx.get('method') or '',
                'request_path': ctx.get('path') or '',
                'user_agent': ctx.get('user_agent') or '',
            })
