"""
故障注入服务
管理链路断开、设备故障、丢包和延迟注入
"""
import random
import time
import uuid
from typing import Dict, List, Optional


class FaultInjector:
    """
    维护每个会话的故障状态，并提供便捷的查询接口
    """

    def __init__(self):
        # {session_id: {fault_id: fault_data}}
        self._faults: Dict[str, Dict[str, dict]] = {}

    def inject_fault(self, session_id: str, fault_type: str, target_id: str, params: Optional[dict] = None) -> dict:
        """注册新的故障，返回故障描述"""
        params = params or {}
        fault_id = str(uuid.uuid4())
        fault = {
            "fault_id": fault_id,
            "session_id": session_id,
            "fault_type": fault_type,
            "target_id": target_id,
            "params": params,
            "status": "active",
            "create_time": time.time(),
        }
        if session_id not in self._faults:
            self._faults[session_id] = {}
        self._faults[session_id][fault_id] = fault
        return fault

    def clear_fault(self, session_id: str, fault_id: str) -> bool:
        """清除故障"""
        if session_id in self._faults and fault_id in self._faults[session_id]:
            self._faults[session_id][fault_id]["status"] = "cleared"
            return True
        return False

    def list_faults(self, session_id: str) -> List[dict]:
        """列出当前会话故障"""
        return list(self._faults.get(session_id, {}).values())

    def should_drop(self, session_id: str, edge_id: str) -> bool:
        """根据丢包率判定是否丢弃报文"""
        for fault in self._faults.get(session_id, {}).values():
            if fault["status"] != "active":
                continue
            if fault["fault_type"] == "packet_loss" and fault["target_id"] == edge_id:
                rate = float(fault.get("params", {}).get("loss_rate", 0))
                return random.random() < max(0.0, min(rate, 1.0))
        return False

    def get_delay(self, session_id: str, edge_id: str) -> float:
        """获取需要附加的延迟（秒）"""
        for fault in self._faults.get(session_id, {}).values():
            if fault["status"] != "active":
                continue
            if fault["fault_type"] == "delay" and fault["target_id"] == edge_id:
                delay_ms = float(fault.get("params", {}).get("delay_ms", 0))
                return max(0.0, delay_ms / 1000.0)
        return 0.0

    def is_disconnected(self, session_id: str, edge_id: str) -> bool:
        """链路是否被断开"""
        for fault in self._faults.get(session_id, {}).values():
            if fault["status"] != "active":
                continue
            if fault["fault_type"] == "disconnect" and fault["target_id"] == edge_id:
                return True
        return False

    def is_device_failed(self, session_id: str, node_id: str) -> bool:
        """设备是否故障"""
        for fault in self._faults.get(session_id, {}).values():
            if fault["status"] != "active":
                continue
            if fault["fault_type"] == "device_failure" and fault["target_id"] == node_id:
                return True
        return False
