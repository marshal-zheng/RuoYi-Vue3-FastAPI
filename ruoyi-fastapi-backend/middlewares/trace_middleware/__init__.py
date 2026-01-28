from fastapi import FastAPI
from .ctx import TraceCtx, get_request_id
from .middle import TraceASGIMiddleware

__all__ = ('TraceASGIMiddleware', 'TraceCtx', 'get_request_id')

__version__ = '0.1.0'


def add_trace_middleware(app: FastAPI):
    """
    添加trace中间件

    :param app: FastAPI对象
    :return:
    """
    app.add_middleware(TraceASGIMiddleware)
