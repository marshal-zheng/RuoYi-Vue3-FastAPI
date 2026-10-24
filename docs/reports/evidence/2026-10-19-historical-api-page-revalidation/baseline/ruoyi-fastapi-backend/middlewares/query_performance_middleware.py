"""
查询性能监控中间件 - Google 工程标准

功能：
- 自动记录慢查询
- 统计查询性能指标
- N+1 查询检测
- 连接池监控
- 查询计划分析
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from sqlalchemy import event
from sqlalchemy.engine import Engine
from contextlib import contextmanager
from typing import Dict, List
from collections import defaultdict
import time
import json
from utils.log_util import logger


class QueryPerformanceMonitor:
    """查询性能监控器"""
    
    def __init__(self):
        self.queries: List[Dict] = []
        self.query_count = 0
        self.total_time = 0.0
        self.slow_query_threshold = 1.0  # 慢查询阈值（秒）
        
    def record_query(self, statement: str, parameters: dict, duration: float):
        """记录查询"""
        self.query_count += 1
        self.total_time += duration
        
        query_info = {
            'statement': statement,
            'parameters': parameters,
            'duration': duration,
            'is_slow': duration > self.slow_query_threshold
        }
        
        self.queries.append(query_info)
        
        # 慢查询告警
        if query_info['is_slow']:
            logger.warning(
                f"Slow query detected ({duration:.3f}s):\n"
                f"SQL: {statement}\n"
                f"Params: {parameters}"
            )
    
    def detect_n_plus_one(self) -> List[str]:
        """
        检测 N+1 查询问题
        
        Returns:
            可能存在 N+1 问题的查询列表
        """
        # 统计相似查询的数量
        query_patterns = defaultdict(int)
        for query in self.queries:
            # 移除参数，只保留查询模式
            pattern = self._normalize_query(query['statement'])
            query_patterns[pattern] += 1
        
        # 找出重复次数过多的查询（可能是 N+1）
        n_plus_one_candidates = []
        for pattern, count in query_patterns.items():
            if count > 10:  # 阈值：重复超过 10 次
                n_plus_one_candidates.append(
                    f"Query executed {count} times: {pattern[:100]}..."
                )
        
        return n_plus_one_candidates
    
    @staticmethod
    def _normalize_query(sql: str) -> str:
        """标准化查询（移除参数值）"""
        # 简单实现：移除数字和字符串字面量
        import re
        sql = re.sub(r'\d+', '?', sql)
        sql = re.sub(r"'[^']*'", '?', sql)
        return sql
    
    def get_summary(self) -> Dict:
        """获取性能摘要"""
        slow_queries = [q for q in self.queries if q['is_slow']]
        n_plus_one = self.detect_n_plus_one()
        
        return {
            'total_queries': self.query_count,
            'total_time': round(self.total_time, 3),
            'avg_time': round(self.total_time / self.query_count, 3) if self.query_count > 0 else 0,
            'slow_queries_count': len(slow_queries),
            'n_plus_one_detected': len(n_plus_one) > 0,
            'n_plus_one_patterns': n_plus_one,
            'queries': self.queries if len(self.queries) <= 50 else self.queries[:50]  # 限制返回数量
        }


class QueryPerformanceMiddleware(BaseHTTPMiddleware):
    """
    查询性能监控中间件
    
    为每个请求监控数据库查询性能
    """
    
    def __init__(self, app: ASGIApp, enable_detailed_logging: bool = False):
        super().__init__(app)
        self.enable_detailed_logging = enable_detailed_logging
        self._setup_sqlalchemy_events()
    
    def _setup_sqlalchemy_events(self):
        """设置 SQLAlchemy 事件监听"""
        
        @event.listens_for(Engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
            """查询开始前"""
            conn.info.setdefault('query_start_time', []).append(time.time())
            conn.info.setdefault('query_statements', []).append(statement)
        
        @event.listens_for(Engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, params, context, executemany):
            """查询结束后"""
            if 'query_start_time' in conn.info and conn.info['query_start_time']:
                duration = time.time() - conn.info['query_start_time'].pop()
                
                # 记录到当前请求的监控器
                if hasattr(conn.info, 'performance_monitor'):
                    conn.info.performance_monitor.record_query(statement, params, duration)
    
    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        # 创建性能监控器
        monitor = QueryPerformanceMonitor()
        
        # 将监控器附加到请求上下文
        request.state.query_monitor = monitor
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 处理请求
        response = await call_next(request)
        
        # 计算总耗时
        total_duration = time.time() - start_time
        
        # 获取性能摘要
        summary = monitor.get_summary()
        
        # 添加性能指标到响应头
        response.headers['X-Query-Count'] = str(summary['total_queries'])
        response.headers['X-Query-Time'] = str(summary['total_time'])
        response.headers['X-Total-Time'] = str(round(total_duration, 3))
        
        # 详细日志
        if self.enable_detailed_logging or summary['slow_queries_count'] > 0:
            logger.info(
                f"Request Performance:\n"
                f"  Path: {request.url.path}\n"
                f"  Method: {request.method}\n"
                f"  Total Time: {total_duration:.3f}s\n"
                f"  Query Count: {summary['total_queries']}\n"
                f"  Query Time: {summary['total_time']:.3f}s\n"
                f"  Slow Queries: {summary['slow_queries_count']}\n"
                f"  N+1 Detected: {summary['n_plus_one_detected']}"
            )
        
        # N+1 查询告警
        if summary['n_plus_one_detected']:
            logger.warning(
                f"N+1 Query Problem Detected:\n"
                f"  Path: {request.url.path}\n"
                f"  Patterns:\n" +
                "\n".join(f"    - {p}" for p in summary['n_plus_one_patterns'])
            )
        
        return response


class ConnectionPoolMonitor:
    """
    连接池监控器
    
    监控连接池状态，防止连接泄漏
    """
    
    @staticmethod
    def get_pool_status(engine) -> Dict:
        """获取连接池状态"""
        pool = engine.pool
        return {
            'size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'total_connections': pool.size() + pool.overflow(),
            'available_connections': pool.size() - pool.checkedout(),
        }
    
    @staticmethod
    async def monitor_pool_health(engine, threshold: float = 0.8):
        """
        监控连接池健康状态
        
        Args:
            engine: SQLAlchemy 引擎
            threshold: 告警阈值（使用率）
        """
        status = ConnectionPoolMonitor.get_pool_status(engine)
        usage_rate = status['checked_out'] / status['total_connections']
        
        if usage_rate > threshold:
            logger.warning(
                f"Connection pool usage high ({usage_rate:.1%}):\n"
                f"  Checked out: {status['checked_out']}\n"
                f"  Total: {status['total_connections']}\n"
                f"  Available: {status['available_connections']}"
            )
        
        return status


class QueryExplainAnalyzer:
    """
    查询计划分析器
    
    分析慢查询的执行计划，提供优化建议
    """
    
    @staticmethod
    async def explain_query(db, sql: str, params: dict = None) -> Dict:
        """
        分析查询执行计划
        
        Args:
            db: 数据库会话
            sql: SQL 语句
            params: 查询参数
        
        Returns:
            执行计划分析结果
        """
        # MySQL EXPLAIN
        explain_sql = f"EXPLAIN {sql}"
        result = await db.execute(explain_sql, params or {})
        rows = result.fetchall()
        
        # 分析执行计划
        issues = []
        for row in rows:
            # 检查是否使用索引
            if row.type == 'ALL':
                issues.append("Full table scan detected - consider adding index")
            
            # 检查是否使用临时表
            if 'Using temporary' in (row.Extra or ''):
                issues.append("Using temporary table - consider query optimization")
            
            # 检查是否使用文件排序
            if 'Using filesort' in (row.Extra or ''):
                issues.append("Using filesort - consider adding index for ORDER BY")
        
        return {
            'plan': [dict(row) for row in rows],
            'issues': issues,
            'has_issues': len(issues) > 0
        }


# 使用示例
"""
# 1. 在 FastAPI 应用中注册中间件
from middlewares.query_performance_middleware import QueryPerformanceMiddleware

app = FastAPI()
app.add_middleware(
    QueryPerformanceMiddleware,
    enable_detailed_logging=True  # 开发环境启用详细日志
)

# 2. 在请求处理中访问性能监控
@app.get("/users")
async def get_users(request: Request, db: AsyncSession = Depends(get_db)):
    users = await db.execute(select(User))
    
    # 获取查询性能摘要
    if hasattr(request.state, 'query_monitor'):
        summary = request.state.query_monitor.get_summary()
        print(f"Queries executed: {summary['total_queries']}")
    
    return users

# 3. 监控连接池
from middlewares.query_performance_middleware import ConnectionPoolMonitor

async def health_check():
    status = ConnectionPoolMonitor.get_pool_status(async_engine)
    return {"pool_status": status}

# 4. 分析慢查询
from middlewares.query_performance_middleware import QueryExplainAnalyzer

async def analyze_slow_query(db: AsyncSession):
    sql = "SELECT * FROM sys_user WHERE dept_id = :dept_id"
    analysis = await QueryExplainAnalyzer.explain_query(db, sql, {"dept_id": 100})
    
    if analysis['has_issues']:
        print("Query optimization needed:")
        for issue in analysis['issues']:
            print(f"  - {issue}")
"""
