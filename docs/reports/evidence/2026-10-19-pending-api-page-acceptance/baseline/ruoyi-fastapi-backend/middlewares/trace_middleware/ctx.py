# -*- coding: utf-8 -*-
"""
@author: peng
@file: ctx.py
@time: 2025/1/17  16:57

Trace Context - 请求追踪上下文
支持统一错误处理系统的 requestId 追踪
"""

import contextvars
from uuid import uuid4

CTX_REQUEST_ID: contextvars.ContextVar[str] = contextvars.ContextVar('request-id', default='')
CTX_TRACE_ID: contextvars.ContextVar[str] = contextvars.ContextVar('trace-id', default='')


class TraceCtx:
    @staticmethod
    def set_request_id(value: str | None = None):
        """设置请求 ID。"""
        request_id = (value or '').strip() or uuid4().hex
        CTX_REQUEST_ID.set(request_id)
        return request_id

    @staticmethod
    def get_request_id():
        """获取请求 ID。"""
        return CTX_REQUEST_ID.get()

    @staticmethod
    def set_trace_id(value: str | None = None):
        """设置 trace ID。"""
        trace_id = (value or '').strip()
        CTX_TRACE_ID.set(trace_id)
        return trace_id

    @staticmethod
    def get_trace_id():
        """获取 trace ID。"""
        return CTX_TRACE_ID.get()

    @staticmethod
    def set_id(value: str | None = None):
        """兼容旧调用，等价于设置 request ID。"""
        return TraceCtx.set_request_id(value)

    @staticmethod
    def get_id():
        """兼容旧调用，等价于读取 request ID。"""
        return TraceCtx.get_request_id()


# 便捷函数：用于统一错误处理系统
def get_request_id() -> str:
    """
    获取当前请求的 requestId
    
    用于统一错误处理系统的日志记录和响应追踪
    
    Returns:
        str: 当前请求的 requestId，如果不存在则返回空字符串
    """
    return TraceCtx.get_request_id()


def get_trace_id() -> str:
    """获取当前 traceId。"""
    return TraceCtx.get_trace_id()
