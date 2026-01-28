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


class TraceCtx:
    @staticmethod
    def set_id():
        """设置请求ID"""
        _id = uuid4().hex
        CTX_REQUEST_ID.set(_id)
        return _id

    @staticmethod
    def get_id():
        """获取请求ID"""
        return CTX_REQUEST_ID.get()


# 便捷函数：用于统一错误处理系统
def get_request_id() -> str:
    """
    获取当前请求的 requestId
    
    用于统一错误处理系统的日志记录和响应追踪
    
    Returns:
        str: 当前请求的 requestId，如果不存在则返回空字符串
    """
    return TraceCtx.get_id()
