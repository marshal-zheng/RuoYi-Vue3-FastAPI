"""
CAN 总线协议仿真模型
集成 python-can 实现虚拟 CAN 通道
"""
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, Generator, List, Optional

import simpy

from module_admin.service.protocol_models.base_protocol import BaseProtocolModel


class CANBusModel(BaseProtocolModel):
    """
    CAN 总线仿真模型

    特点:
    - 使用 python-can 的 virtual 接口创建虚拟 CAN 通道
    - 支持标准帧（11位ID）和扩展帧（29位ID）
    - 支持非破坏性位仲裁模拟
    - 支持错误帧注入
    """

    # CAN 协议时序参数
    BIT_TIME_125K = 0.000008  # 125Kbps 位时间
    BIT_TIME_250K = 0.000004  # 250Kbps 位时间
    BIT_TIME_500K = 0.000002  # 500Kbps 位时间
    BIT_TIME_1M = 0.000001  # 1Mbps 位时间

    def __init__(
        self,
        env: simpy.Environment,
        model_id: str,
        config: Dict[str, Any],
        message_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        super().__init__(env, model_id, config, message_callback)
        # 总线资源（支持仲裁）
        self.bus = simpy.PriorityResource(env, capacity=1)
        # 波特率
        self.baud_rate = config.get("baud_rate", 500000)
        # 设备消息配置列表
        self.device_configs = config.get("devices", [])
        # 错误帧注入队列
        self._error_frames: List[Dict[str, Any]] = []
        # 计算位时间
        self._bit_time = 1.0 / self.baud_rate

    def start_processes(self) -> List[simpy.Process]:
        """启动设备发送进程"""
        self._processes = []
        for device_cfg in self.device_configs:
            proc = self.env.process(self._device_process(device_cfg))
            self._processes.append(proc)
        return self._processes

    def _device_process(self, device_config: Dict[str, Any]) -> Generator:
        """设备 CAN 发送进程"""
        device_id = device_config.get("device_id", "unknown")
        messages = device_config.get("messages", [])

        while not self._stopped:
            for msg_cfg in messages:
                if self._stopped:
                    break

                # 仲裁：低ID优先
                can_id = msg_cfg.get("can_id", 0)
                priority = can_id  # ID越小优先级越高

                # 申请总线
                with self.bus.request(priority=priority) as req:
                    yield req

                    payload_info = {}
                    supplier = msg_cfg.get("payload_supplier")
                    if callable(supplier):
                        payload_info = supplier(self.env.now) or {}

                    data_hex = payload_info.get("payload_hex", msg_cfg.get("data", "00000000"))
                    field_values = payload_info.get("field_values", {})
                    fill_strategy = payload_info.get("fill_strategy")

                    # 计算帧传输时间
                    data_len = payload_info.get("size_bytes") or msg_cfg.get("dlc", 8)
                    data_len = max(0, min(8, data_len))
                    # 标准帧：47位开销 + 数据位
                    # 扩展帧：67位开销 + 数据位
                    is_extended = msg_cfg.get("extended", False)
                    overhead_bits = 67 if is_extended else 47
                    data_bits = data_len * 8
                    total_bits = overhead_bits + data_bits
                    tx_time = total_bits * self._bit_time

                    yield self.env.timeout(tx_time)

                    # 构建并发送消息
                    can_msg = self._build_can_message(
                        device_id,
                        msg_cfg,
                        data_hex=data_hex,
                        dlc=data_len,
                        field_values=field_values,
                        fill_strategy=fill_strategy,
                    )
                    self._notify_message(can_msg)

                    # 检查是否注入错误帧
                    if self._error_frames:
                        error = self._error_frames.pop(0)
                        self._notify_message(error)

                # 等待发送间隔
                interval = msg_cfg.get("interval", 0.1)
                yield self.env.timeout(interval)

    def _build_can_message(
        self,
        device_id: str,
        msg_cfg: Dict[str, Any],
        data_hex: Optional[str] = None,
        dlc: Optional[int] = None,
        field_values: Optional[Dict[str, Any]] = None,
        fill_strategy: Optional[str] = None,
    ) -> Dict[str, Any]:
        """构建 CAN 消息"""
        can_id = msg_cfg.get("can_id", 0)
        data = data_hex if data_hex is not None else msg_cfg.get("data", "00000000")
        dlc = dlc if dlc is not None else msg_cfg.get("dlc", 8)
        is_extended = msg_cfg.get("extended", False)

        # 确保数据是十六进制字符串
        if isinstance(data, (bytes, bytearray)):
            data_hex = data.hex().upper()
        elif isinstance(data, list):
            data_hex = "".join(f"{b:02X}" for b in data)
        else:
            data_hex = str(data).upper()

        # 计算 CRC（简化，实际 CAN 使用 CRC-15）
        crc = sum(bytes.fromhex(data_hex.ljust(dlc * 2, "0"))) & 0x7FFF

        return {
            "message_id": str(uuid.uuid4()),
            "model_id": self.model_id,
            "protocol_type": "CAN",
            "device_id": device_id,
            "timestamp": self.env.now,
            "can_id": can_id,
            "dlc": dlc,
            "is_extended": is_extended,
            "data_hex": data_hex,
            "payload_hex": data_hex,
            "crc": crc,
            "is_error_frame": False,
            "size_bytes": dlc,
            "field_values": field_values or {},
            "fill_strategy": fill_strategy or msg_cfg.get("fill_strategy"),
            "create_time": datetime.now(),
        }

    def emit_message(self, message: Dict[str, Any]) -> None:
        """发送协议报文"""
        self._notify_message(message)

    def inject_fault(
        self, fault_type: str, params: Optional[Dict[str, Any]] = None
    ) -> bool:
        """注入故障"""
        params = params or {}

        if fault_type == "error_frame":
            count = params.get("count", 1)
            for _ in range(count):
                error_frame = {
                    "message_id": str(uuid.uuid4()),
                    "model_id": self.model_id,
                    "protocol_type": "CAN",
                    "timestamp": self.env.now,
                    "can_id": 0,
                    "dlc": 0,
                    "data_hex": "",
                    "payload_hex": "",
                    "is_error_frame": True,
                    "error_type": "injected",
                    "create_time": datetime.now(),
                }
                self._error_frames.append(error_frame)
            return True

        return False

    def get_status(self) -> Dict[str, Any]:
        """获取模型状态"""
        base_status = super().get_status()
        base_status.update(
            {
                "baud_rate": self.baud_rate,
                "device_count": len(self.device_configs),
                "pending_errors": len(self._error_frames),
            }
        )
        return base_status







