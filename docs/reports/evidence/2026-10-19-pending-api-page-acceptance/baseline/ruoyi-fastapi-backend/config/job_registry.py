"""
任务函数注册表 - 安全替代 eval()

Google 工程标准：
- 使用白名单机制代替 eval()
- 所有可执行的任务函数必须显式注册
- 提供类型安全的函数查找
"""
from typing import Dict, Callable, Any
from utils.log_util import logger


class JobFunctionRegistry:
    """
    任务函数注册表
    
    用于安全地管理和查找定时任务函数，替代 eval() 的不安全实现
    """
    
    _registry: Dict[str, Callable] = {}
    
    @classmethod
    def register(cls, name: str):
        """
        装饰器：注册任务函数
        
        Usage:
            @JobFunctionRegistry.register('my_task')
            async def my_task():
                pass
        """
        def decorator(func: Callable) -> Callable:
            cls._registry[name] = func
            logger.info(f"Registered job function: {name}")
            return func
        return decorator
    
    @classmethod
    def register_function(cls, name: str, func: Callable):
        """
        直接注册任务函数
        
        Args:
            name: 函数名称（用于查找）
            func: 函数对象
        """
        cls._registry[name] = func
        logger.info(f"Registered job function: {name}")
    
    @classmethod
    def get(cls, name: str) -> Callable:
        """
        获取已注册的任务函数
        
        Args:
            name: 函数名称
        
        Returns:
            函数对象
        
        Raises:
            ValueError: 如果函数未注册
        """
        if name not in cls._registry:
            raise ValueError(
                f"Job function '{name}' not registered. "
                f"Available functions: {list(cls._registry.keys())}"
            )
        return cls._registry[name]
    
    @classmethod
    def exists(cls, name: str) -> bool:
        """检查函数是否已注册"""
        return name in cls._registry
    
    @classmethod
    def list_all(cls) -> list:
        """列出所有已注册的函数"""
        return list(cls._registry.keys())
    
    @classmethod
    def unregister(cls, name: str):
        """注销函数"""
        if name in cls._registry:
            del cls._registry[name]
            logger.info(f"Unregistered job function: {name}")


# 使用示例
"""
# 1. 注册任务函数（使用装饰器）
from config.job_registry import JobFunctionRegistry

@JobFunctionRegistry.register('send_email')
async def send_email_task():
    print("Sending email...")

@JobFunctionRegistry.register('cleanup_logs')
def cleanup_logs_task():
    print("Cleaning up logs...")

# 2. 在 scheduler 中使用
from config.job_registry import JobFunctionRegistry

# 安全地获取函数（不使用 eval）
try:
    job_func = JobFunctionRegistry.get(job_info.invoke_target)
    scheduler.add_job(func=job_func, ...)
except ValueError as e:
    logger.error(f"Invalid job function: {e}")

# 3. 批量注册现有任务函数
from module_task import task_functions

for name, func in task_functions.items():
    JobFunctionRegistry.register_function(name, func)
"""
