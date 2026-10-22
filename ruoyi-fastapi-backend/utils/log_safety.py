"""Small boundary helpers for diagnostic logs and document-free audit payloads."""

import json
from collections.abc import Mapping

from sqlalchemy.exc import SQLAlchemyError

DOCUMENT_OMITTED = '[document content omitted]'
REMARK_FIELDS = frozenset({'remark', 'remarktext', 'remark_text'})


def database_exception(error):
    """Find a database failure without rendering any exception or SQL parameters."""
    pending, seen = [error], set()
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        if isinstance(current, SQLAlchemyError):
            return current
        if isinstance(current, BaseExceptionGroup):
            pending.extend(current.exceptions)
        pending.extend(
            related
            for related in (getattr(current, '__cause__', None), getattr(current, '__context__', None))
            if isinstance(related, BaseException)
        )
    return None


def safe_exception_summary(error):
    database_error = database_exception(error)
    if database_error is None:
        return f'{type(error).__name__}: {error}'
    original = getattr(database_error, 'orig', None)
    codes = [getattr(original, 'errno', None), getattr(original, 'sqlite_errorcode', None)]
    codes.extend(getattr(original, 'args', ())[:1])
    code = next((value for value in codes if type(value) is int), None)
    return type(database_error).__name__ + (f' (db_code={code})' if code is not None else '')


def log_safe_exception(bound_logger, message, error):
    if database_exception(error) is not None:
        # A Loguru exception record would render SQL/params again, even when
        # its message is safe. Database diagnostics intentionally have no trace.
        bound_logger.error(f'{message}: {safe_exception_summary(error)}')
    else:
        bound_logger.opt(exception=(type(error), error, error.__traceback__)).error(message)


def _document(value):
    if isinstance(value, str) and value.lstrip().startswith('{') and len(value) <= 262144:
        try:
            value = json.loads(value)
        except (ValueError, RecursionError):
            return False
    return isinstance(value, Mapping) and (
        (value.get('version') == 2 and 'body' in value)
        or (value.get('format') in ('json', 'html', 'markdown') and 'content' in value)
        or (value.get('type') == 'doc' and 'content' in value)
    )


def _redact_json_text(value, mask_fields, depth):
    if len(value) > 262144:
        return '[oversized audit value omitted]'
    try:
        decoded = json.loads(value)
    except (ValueError, RecursionError):
        return value
    sanitized = redact_document_data(decoded, mask_fields=mask_fields, _depth=depth + 1)
    return value if sanitized == decoded else json.dumps(sanitized, ensure_ascii=False)


def redact_document_data(value, *, mask_fields=(), _depth=0):
    """Keep operation identity/ordinary values while omitting document bodies."""
    if _depth > 32:
        return '[deep audit value omitted]'
    if isinstance(value, str) and value.lstrip().startswith(('{', '[')):
        return _redact_json_text(value, mask_fields, _depth)
    if _document(value):
        return DOCUMENT_OMITTED
    if isinstance(value, Mapping):
        protected = REMARK_FIELDS | {str(field).lower() for field in mask_fields}
        derived = {name for key, item in value.items() if _document(item) for name in (f'{key}Text', f'{key}_text')}
        return {
            key: (item if item is None or item == '' else DOCUMENT_OMITTED)
            if str(key).lower() in protected or key in derived
            else redact_document_data(item, mask_fields=mask_fields, _depth=_depth + 1)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact_document_data(item, mask_fields=mask_fields, _depth=_depth + 1) for item in value]
    return value
