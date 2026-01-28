"""
审计上下文
用于在请求范围内传递审计信息并暂存读审计日志
"""
import contextvars
from typing import Any, Dict, List


_AUDIT_CONTEXT: contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar('audit-context', default={})
_READ_AUDIT_BUFFER: contextvars.ContextVar[List[Dict[str, Any]]] = contextvars.ContextVar('audit-read-buffer', default=[])


def set_audit_context(context: Dict[str, Any]):
    """设置审计上下文"""
    _AUDIT_CONTEXT.set(context or {})
    _READ_AUDIT_BUFFER.set([])


def get_audit_context() -> Dict[str, Any]:
    """获取审计上下文"""
    return _AUDIT_CONTEXT.get() or {}


def append_read_audit(entry: Dict[str, Any]):
    """追加读审计记录到缓冲区"""
    buffer = _READ_AUDIT_BUFFER.get()
    if buffer is None:
        buffer = []
        _READ_AUDIT_BUFFER.set(buffer)
    buffer.append(entry)


def pop_read_audits() -> List[Dict[str, Any]]:
    """获取并清空读审计缓冲区"""
    buffer = _READ_AUDIT_BUFFER.get() or []
    _READ_AUDIT_BUFFER.set([])
    return buffer
