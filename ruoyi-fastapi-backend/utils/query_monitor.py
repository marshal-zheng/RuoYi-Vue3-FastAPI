"""
查询性能监控 - P1-008~012 性能监控实现

功能：
- 慢查询监控和告警 (P1-009)
- N+1 查询检测 (P1-010)
- 连接池监控 (P1-011)
- 查询计划分析 (P1-012)
"""
import time
import logging
import re
from collections import defaultdict
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

logger = logging.getLogger(__name__)


class QueryPerformanceMonitor:
    """
    查询性能监控器
    
    监控 SQL 查询执行时间，记录慢查询
    """
    
    def __init__(self, threshold_ms: float = 100, log_all: bool = False):
        """
        初始化性能监控器
        
        Args:
            threshold_ms: 慢查询阈值（毫秒）
            log_all: 是否记录所有查询（默认只记录慢查询）
        """
        self.threshold_ms = threshold_ms
        self.log_all = log_all
        self.query_stats = {
            'total_queries': 0,
            'slow_queries': 0,
            'total_time': 0.0,
            'max_time': 0.0,
            'min_time': float('inf')
        }
    
    def setup(self, engine: AsyncEngine):
        """
        设置监控器到数据库引擎
        
        Args:
            engine: AsyncEngine 实例
        """
        # 获取同步引擎（用于事件监听）
        sync_engine = engine.sync_engine
        
        @event.listens_for(sync_engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """查询执行前"""
            conn.info.setdefault('query_start_time', []).append(time.time())
            conn.info.setdefault('query_statement', []).append(statement)
        
        @event.listens_for(sync_engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """查询执行后"""
            start_time = conn.info['query_start_time'].pop()
            total_time = time.time() - start_time
            total_time_ms = total_time * 1000
            
            # 更新统计
            self._update_stats(total_time_ms)
            
            # 记录日志
            if self.log_all or total_time_ms > self.threshold_ms:
                self._log_query(statement, parameters, total_time_ms)
    
    def _update_stats(self, time_ms: float):
        """更新查询统计"""
        self.query_stats['total_queries'] += 1
        self.query_stats['total_time'] += time_ms
        
        if time_ms > self.threshold_ms:
            self.query_stats['slow_queries'] += 1
        
        if time_ms > self.query_stats['max_time']:
            self.query_stats['max_time'] = time_ms
        
        if time_ms < self.query_stats['min_time']:
            self.query_stats['min_time'] = time_ms
    
    def _log_query(self, statement: str, parameters, time_ms: float):
        """记录查询日志"""
        level = logging.WARNING if time_ms > self.threshold_ms else logging.INFO
        
        # 格式化 SQL 语句（简化显示）
        formatted_sql = self._format_sql(statement)
        
        log_message = (
            f"\n{'=' * 80}\n"
            f"{'SLOW QUERY' if time_ms > self.threshold_ms else 'QUERY'}\n"
            f"Time: {time_ms:.2f}ms\n"
            f"SQL: {formatted_sql}\n"
            f"Params: {parameters}\n"
            f"{'=' * 80}"
        )
        
        logger.log(level, log_message)
    
    def _format_sql(self, sql: str, max_length: int = 500) -> str:
        """格式化 SQL 语句"""
        # 移除多余空白
        sql = ' '.join(sql.split())
        
        # 截断过长的 SQL
        if len(sql) > max_length:
            sql = sql[:max_length] + '...'
        
        return sql
    
    def get_stats(self) -> dict:
        """
        获取查询统计信息
        
        Returns:
            统计信息字典
        """
        stats = self.query_stats.copy()
        
        # 计算平均时间
        if stats['total_queries'] > 0:
            stats['avg_time'] = stats['total_time'] / stats['total_queries']
        else:
            stats['avg_time'] = 0.0
        
        # 计算慢查询占比
        if stats['total_queries'] > 0:
            stats['slow_query_rate'] = (stats['slow_queries'] / stats['total_queries']) * 100
        else:
            stats['slow_query_rate'] = 0.0
        
        return stats
    
    def reset_stats(self):
        """重置统计信息"""
        self.query_stats = {
            'total_queries': 0,
            'slow_queries': 0,
            'total_time': 0.0,
            'max_time': 0.0,
            'min_time': float('inf')
        }
    
    def print_stats(self):
        """打印统计信息"""
        stats = self.get_stats()
        
        print("\n" + "=" * 80)
        print("查询性能统计")
        print("=" * 80)
        print(f"总查询数: {stats['total_queries']}")
        print(f"慢查询数: {stats['slow_queries']}")
        print(f"慢查询占比: {stats['slow_query_rate']:.2f}%")
        print(f"平均耗时: {stats['avg_time']:.2f}ms")
        print(f"最大耗时: {stats['max_time']:.2f}ms")
        print(f"最小耗时: {stats['min_time']:.2f}ms" if stats['min_time'] != float('inf') else "最小耗时: N/A")
        print(f"总耗时: {stats['total_time']:.2f}ms")
        print("=" * 80 + "\n")


class QueryLogger:
    """
    查询日志记录器
    
    记录所有 SQL 查询到日志文件
    """
    
    def __init__(self, log_file: Optional[str] = None):
        """
        初始化查询日志记录器
        
        Args:
            log_file: 日志文件路径（可选）
        """
        self.log_file = log_file
        if log_file:
            # 配置文件日志
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    def setup(self, engine: AsyncEngine):
        """
        设置日志记录器到数据库引擎
        
        Args:
            engine: AsyncEngine 实例
        """
        sync_engine = engine.sync_engine
        
        @event.listens_for(sync_engine, "before_cursor_execute")
        def log_query(conn, cursor, statement, parameters, context, executemany):
            logger.debug(
                f"Executing query:\nSQL: {statement}\nParams: {parameters}"
            )


class ConnectionPoolMonitor:
    """
    连接池监控器
    
    监控数据库连接池状态
    """
    
    def __init__(self):
        """初始化连接池监控器"""
        self.events = {
            'connect': 0,
            'checkout': 0,
            'checkin': 0,
            'close': 0,
            'detach': 0,
            'invalidate': 0
        }
    
    def setup(self, engine: AsyncEngine):
        """
        设置监控器到数据库引擎
        
        Args:
            engine: AsyncEngine 实例
        """
        from sqlalchemy.pool import Pool
        
        @event.listens_for(Pool, "connect")
        def receive_connect(dbapi_conn, connection_record):
            self.events['connect'] += 1
            logger.info("数据库连接已建立")
        
        @event.listens_for(Pool, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            self.events['checkout'] += 1
            logger.debug("连接从池中取出")
        
        @event.listens_for(Pool, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            self.events['checkin'] += 1
            logger.debug("连接归还到池中")
        
        @event.listens_for(Pool, "close")
        def receive_close(dbapi_conn, connection_record):
            self.events['close'] += 1
            logger.info("数据库连接已关闭")
        
        @event.listens_for(Pool, "detach")
        def receive_detach(dbapi_conn, connection_record):
            self.events['detach'] += 1
            logger.warning("连接已从池中分离")
        
        @event.listens_for(Pool, "invalidate")
        def receive_invalidate(dbapi_conn, connection_record, exception):
            self.events['invalidate'] += 1
            logger.error(f"连接已失效: {exception}")
    
    def get_stats(self) -> dict:
        """
        获取连接池统计信息
        
        Returns:
            统计信息字典
        """
        return self.events.copy()
    
    def print_stats(self):
        """打印连接池统计"""
        print("\n" + "=" * 80)
        print("连接池统计")
        print("=" * 80)
        for event_name, count in self.events.items():
            print(f"{event_name}: {count}")
        print("=" * 80 + "\n")


@dataclass
class NPlusOneDetector:
    """
    N+1 查询检测器 (P1-010)
    
    检测重复执行的相似查询，可能表示 N+1 问题
    """
    
    threshold: int = 5  # 相似查询重复次数阈值
    window_size: int = 100  # 检测窗口大小
    query_patterns: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    recent_queries: List[str] = field(default_factory=list)
    detected_patterns: List[Dict[str, Any]] = field(default_factory=list)
    
    def record_query(self, sql: str):
        """记录查询并检测 N+1"""
        pattern = self._normalize_query(sql)
        self.query_patterns[pattern] += 1
        self.recent_queries.append(pattern)
        
        # 维护窗口大小
        if len(self.recent_queries) > self.window_size:
            old_pattern = self.recent_queries.pop(0)
            self.query_patterns[old_pattern] -= 1
            if self.query_patterns[old_pattern] <= 0:
                del self.query_patterns[old_pattern]
        
        # 检测 N+1
        if self.query_patterns[pattern] >= self.threshold:
            self._record_n_plus_one(pattern, self.query_patterns[pattern])
    
    def _normalize_query(self, sql: str) -> str:
        """标准化查询（移除参数值）"""
        # 移除数字参数
        sql = re.sub(r'\b\d+\b', '?', sql)
        # 移除字符串参数
        sql = re.sub(r"'[^']*'", '?', sql)
        sql = re.sub(r'"[^"]*"', '?', sql)
        # 移除多余空白
        sql = ' '.join(sql.split())
        return sql
    
    def _record_n_plus_one(self, pattern: str, count: int):
        """记录检测到的 N+1 问题"""
        # 避免重复记录同一模式
        for existing in self.detected_patterns:
            if existing['pattern'] == pattern:
                existing['count'] = count
                return
        
        self.detected_patterns.append({
            'pattern': pattern[:200] + '...' if len(pattern) > 200 else pattern,
            'count': count,
            'timestamp': time.time()
        })
        
        logger.warning(
            f"N+1 查询检测: 相似查询重复 {count} 次\n"
            f"模式: {pattern[:200]}..."
        )
    
    def get_detected(self) -> List[Dict[str, Any]]:
        """获取检测到的 N+1 问题"""
        return self.detected_patterns
    
    def reset(self):
        """重置检测器"""
        self.query_patterns.clear()
        self.recent_queries.clear()
        self.detected_patterns.clear()


class QueryExplainAnalyzer:
    """
    查询计划分析器 (P1-012)
    
    分析慢查询的执行计划，提供优化建议
    """
    
    def __init__(self):
        self.analyzed_queries: List[Dict[str, Any]] = []
    
    async def analyze(self, db: AsyncSession, sql: str) -> Dict[str, Any]:
        """
        分析查询执行计划
        
        Args:
            db: 数据库会话
            sql: SQL 语句
        
        Returns:
            执行计划分析结果
        """
        # 只分析 SELECT 语句
        if not sql.strip().upper().startswith('SELECT'):
            return {'error': 'Only SELECT queries can be analyzed'}
        
        explain_sql = f"EXPLAIN {sql}"
        result = await db.execute(text(explain_sql))
        rows = result.fetchall()
        
        issues = []
        recommendations = []
        
        for row in rows:
            row_dict = dict(row._mapping) if hasattr(row, '_mapping') else {}
            
            # 检查全表扫描
            scan_type = row_dict.get('type', row_dict.get('Type', ''))
            if scan_type == 'ALL':
                issues.append('全表扫描 (Full Table Scan)')
                recommendations.append('建议为 WHERE 条件字段添加索引')
            
            # 检查临时表
            extra = row_dict.get('Extra', row_dict.get('extra', ''))
            if 'Using temporary' in extra:
                issues.append('使用临时表 (Using temporary)')
                recommendations.append('考虑优化 GROUP BY 或 DISTINCT 操作')
            
            # 检查文件排序
            if 'Using filesort' in extra:
                issues.append('使用文件排序 (Using filesort)')
                recommendations.append('为 ORDER BY 字段添加索引')
            
            # 检查索引使用
            if scan_type in ('index', 'ref', 'range', 'eq_ref'):
                pass  # 正常使用索引
        
        analysis = {
            'sql': sql[:500] + '...' if len(sql) > 500 else sql,
            'issues': issues,
            'recommendations': recommendations,
            'has_issues': len(issues) > 0,
            'timestamp': time.time()
        }
        
        self.analyzed_queries.append(analysis)
        
        # 只保留最近 50 条分析
        if len(self.analyzed_queries) > 50:
            self.analyzed_queries = self.analyzed_queries[-50:]
        
        return analysis
    
    def get_recent_analyses(self) -> List[Dict[str, Any]]:
        """获取最近的分析结果"""
        return self.analyzed_queries


class EnhancedQueryPerformanceMonitor(QueryPerformanceMonitor):
    """
    增强的查询性能监控器
    
    集成 N+1 检测和查询计划分析
    """
    
    def __init__(
        self,
        threshold_ms: float = 100,
        log_all: bool = False,
        n_plus_one_threshold: int = 5,
        auto_analyze_slow: bool = True,
        n_plus_one_enabled: bool = False,
    ):
        super().__init__(threshold_ms, log_all)
        self.n_plus_one_detector = NPlusOneDetector(threshold=n_plus_one_threshold)
        self.explain_analyzer = QueryExplainAnalyzer()
        self.auto_analyze_slow = auto_analyze_slow
        self.slow_queries: List[Dict[str, Any]] = []
        # 默认关闭 N+1 检测，避免在日常开发/测试中产生大量告警
        self.n_plus_one_enabled = n_plus_one_enabled
    
    def setup(self, engine: AsyncEngine):
        """设置监控器到数据库引擎"""
        sync_engine = engine.sync_engine
        
        @event.listens_for(sync_engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault('query_start_time', []).append(time.time())
            conn.info.setdefault('query_statement', []).append(statement)
        
        @event.listens_for(sync_engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            start_time = conn.info['query_start_time'].pop()
            total_time = time.time() - start_time
            total_time_ms = total_time * 1000
            
            # 更新统计
            self._update_stats(total_time_ms)
            
            # N+1 检测（可配置，默认关闭）
            if self.n_plus_one_enabled:
                self.n_plus_one_detector.record_query(statement)
            
            # 记录慢查询
            if total_time_ms > self.threshold_ms:
                self.slow_queries.append({
                    'sql': statement[:500],
                    'time_ms': total_time_ms,
                    'parameters': str(parameters)[:200],
                    'timestamp': time.time()
                })
                # 只保留最近 100 条慢查询
                if len(self.slow_queries) > 100:
                    self.slow_queries = self.slow_queries[-100:]
            
            # 记录日志
            if self.log_all or total_time_ms > self.threshold_ms:
                self._log_query(statement, parameters, total_time_ms)
    
    def get_stats(self) -> dict:
        """获取增强的统计信息"""
        stats = super().get_stats()
        stats['n_plus_one_detected'] = len(self.n_plus_one_detector.get_detected())
        stats['n_plus_one_patterns'] = self.n_plus_one_detector.get_detected()
        stats['recent_slow_queries'] = self.slow_queries[-10:]  # 最近 10 条
        return stats
    
    def reset_stats(self):
        """重置所有统计"""
        super().reset_stats()
        self.n_plus_one_detector.reset()
        self.slow_queries.clear()


class ConnectionPoolHealthChecker:
    """
    连接池健康检查器 (P1-011)
    
    监控连接池状态并提供健康检查
    """
    
    def __init__(self, warning_threshold: float = 0.8, critical_threshold: float = 0.95):
        """
        初始化健康检查器
        
        Args:
            warning_threshold: 警告阈值（使用率）
            critical_threshold: 严重阈值（使用率）
        """
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
    
    def check_health(self, engine: AsyncEngine) -> Dict[str, Any]:
        """
        检查连接池健康状态
        
        Returns:
            健康状态信息
        """
        pool = engine.sync_engine.pool
        
        size = pool.size()
        checkedout = pool.checkedout()
        overflow = pool.overflow()
        
        total_capacity = size + (pool._max_overflow if hasattr(pool, '_max_overflow') else 0)
        usage_rate = checkedout / total_capacity if total_capacity > 0 else 0
        
        # 确定健康状态
        if usage_rate >= self.critical_threshold:
            status = 'critical'
            message = f'连接池使用率过高 ({usage_rate:.1%})'
        elif usage_rate >= self.warning_threshold:
            status = 'warning'
            message = f'连接池使用率较高 ({usage_rate:.1%})'
        else:
            status = 'healthy'
            message = '连接池状态正常'
        
        return {
            'status': status,
            'message': message,
            'pool_size': size,
            'checked_out': checkedout,
            'overflow': overflow,
            'total_capacity': total_capacity,
            'usage_rate': round(usage_rate * 100, 2),
            'available': total_capacity - checkedout
        }
    
    async def wait_for_connection(
        self,
        engine: AsyncEngine,
        timeout: float = 5.0
    ) -> bool:
        """
        等待可用连接
        
        Args:
            engine: 数据库引擎
            timeout: 超时时间（秒）
        
        Returns:
            是否获取到连接
        """
        start = time.time()
        while time.time() - start < timeout:
            health = self.check_health(engine)
            if health['available'] > 0:
                return True
            await asyncio.sleep(0.1)
        return False


# 全局实例（可选使用）
_enhanced_monitor: Optional[EnhancedQueryPerformanceMonitor] = None
_pool_health_checker: Optional[ConnectionPoolHealthChecker] = None


def get_enhanced_monitor() -> Optional[EnhancedQueryPerformanceMonitor]:
    """获取增强监控器实例"""
    return _enhanced_monitor


def get_pool_health_checker() -> Optional[ConnectionPoolHealthChecker]:
    """获取连接池健康检查器实例"""
    return _pool_health_checker


def setup_enhanced_monitoring(
    engine: AsyncEngine,
    threshold_ms: float = 100,
    n_plus_one_threshold: int = 5,
    n_plus_one_enabled: bool = False,
) -> tuple:
    """
    设置增强监控
    
    Args:
        engine: 数据库引擎
        threshold_ms: 慢查询阈值
        n_plus_one_threshold: N+1 检测阈值
    
    Returns:
        (EnhancedQueryPerformanceMonitor, ConnectionPoolHealthChecker)
    """
    global _enhanced_monitor, _pool_health_checker
    
    _enhanced_monitor = EnhancedQueryPerformanceMonitor(
        threshold_ms=threshold_ms,
        n_plus_one_threshold=n_plus_one_threshold,
        n_plus_one_enabled=n_plus_one_enabled,
    )
    _enhanced_monitor.setup(engine)
    
    _pool_health_checker = ConnectionPoolHealthChecker()
    
    return _enhanced_monitor, _pool_health_checker


# 需要导入 asyncio
import asyncio


# 使用示例
"""
from config.database import async_engine
from utils.query_monitor import (
    EnhancedQueryPerformanceMonitor,
    ConnectionPoolHealthChecker,
    setup_enhanced_monitoring
)

# 1. 快速设置（推荐）
monitor, health_checker = setup_enhanced_monitoring(
    async_engine,
    threshold_ms=100,
    n_plus_one_threshold=5
)

# 2. 查看统计信息
stats = monitor.get_stats()
print(f"慢查询占比: {stats['slow_query_rate']:.2f}%")
print(f"检测到 N+1 问题: {stats['n_plus_one_detected']}")

# 3. 检查连接池健康
health = health_checker.check_health(async_engine)
print(f"连接池状态: {health['status']}")
print(f"使用率: {health['usage_rate']}%")

# 4. 分析慢查询
from utils.query_monitor import QueryExplainAnalyzer
analyzer = QueryExplainAnalyzer()
analysis = await analyzer.analyze(db, "SELECT * FROM sys_user WHERE dept_id = 1")
if analysis['has_issues']:
    print("优化建议:", analysis['recommendations'])
"""
