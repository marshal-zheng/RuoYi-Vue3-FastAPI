"""
协议仿真模型基类
定义所有协议模型的通用接口
"""
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Generator, List, Optional
import simpy


class BaseProtocolModel(ABC):
    """
    协议仿真模型基类
    所有具体协议模型必须继承此类并实现抽象方法
    """

    def __init__(
        self,
        env: simpy.Environment,
        model_id: str,
        config: Dict[str, Any],
        message_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        """
        初始化协议模型

        参数:
            env: SimPy 环境
            model_id: 模型唯一标识
            config: 模型配置参数
            message_callback: 消息发送回调函数
        """
        self.env = env
        self.model_id = model_id
        self.config = config
        self.message_callback = message_callback
        self._stopped = False
        self._processes: List[simpy.Process] = []

    @abstractmethod
    def start_processes(self) -> List[simpy.Process]:
        """
        启动协议仿真进程
        子类必须实现此方法，返回创建的 SimPy 进程列表
        """
        pass

    @abstractmethod
    def emit_message(self, message: Dict[str, Any]) -> None:
        """
        发送协议报文
        子类实现具体的报文封装逻辑
        """
        pass

    def stop(self) -> None:
        """停止所有进程"""
        self._stopped = True

    def inject_fault(self, fault_type: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """
        注入故障
        子类可覆盖此方法实现协议特定的故障注入

        参数:
            fault_type: 故障类型（error_frame, disconnect, delay 等）
            params: 故障参数

        返回:
            是否成功注入
        """
        return False

    def get_status(self) -> Dict[str, Any]:
        """获取模型状态"""
        return {
            "model_id": self.model_id,
            "stopped": self._stopped,
            "process_count": len(self._processes),
        }

    def _notify_message(self, message: Dict[str, Any]) -> None:
        """调用回调函数通知消息发送"""
        if self.message_callback and not self._stopped:
            self.message_callback(message)








