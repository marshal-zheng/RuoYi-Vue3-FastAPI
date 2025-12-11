"""
RS422/RS485 协议仿真模型
实现半双工总线通信
"""
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, Generator, List, Optional

import simpy

from module_admin.service.protocol_models.base_protocol import BaseProtocolModel


class RS485Model(BaseProtocolModel):
    """
    RS485 半双工总线仿真模型

    特点:
    - 使用 simpy.Resource(capacity=1) 模拟总线独占
    - 支持冲突检测和退避机制
    - 根据波特率计算传输时间
    """

    # 默认波特率
    DEFAULT_BAUD_RATE = 9600
    # 退避时间（秒）
    BACKOFF_TIME = 0.001

    def __init__(
        self,
        env: simpy.Environment,
        model_id: str,
        config: Dict[str, Any],
        message_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        super().__init__(env, model_id, config, message_callback)
        # 总线资源（独占）
        self.bus = simpy.Resource(env, capacity=1)
        # 波特率
        self.baud_rate = config.get("baud_rate", self.DEFAULT_BAUD_RATE)
        # 设备配置列表
        self.device_configs = config.get("devices", [])
        # 冲突计数
        self._collision_count = 0
        # 冲突回调
        self._collision_callback: Optional[Callable[[Dict[str, Any]], None]] = None

    def start_processes(self) -> List[simpy.Process]:
        """启动设备发送进程"""
        self._processes = []
        for device_cfg in self.device_configs:
            proc = self.env.process(self._device_process(device_cfg))
            self._processes.append(proc)
        return self._processes

    def _device_process(self, device_config: Dict[str, Any]) -> Generator:
        """设备发送进程"""
        device_id = device_config.get("device_id", "unknown")
        frames = device_config.get("frames", [])

        while not self._stopped:
            for frame in frames:
                if self._stopped:
                    break

                payload_info = {}
                supplier = frame.get("payload_supplier")
                if callable(supplier):
                    payload_info = supplier(self.env.now) or {}

                data_override = payload_info.get("payload_hex")
                if data_override:
                    frame = dict(frame)
                    frame["data"] = data_override

                # 检查总线是否忙
                if self.bus.count > 0:
                    # 总线忙，记录冲突
                    self._emit_collision(device_id)
                    yield self.env.timeout(self.BACKOFF_TIME)
                    continue

                # 申请总线
                with self.bus.request() as req:
                    yield req

                    # 计算传输时间（10位/字节：1起始 + 8数据 + 1停止）
                    data = frame.get("data", b"")
                    if isinstance(data, str):
                        data = bytes.fromhex(data) if data else b""
                    size_bytes = payload_info.get("size_bytes", len(data))
                    if payload_info.get("payload_hex") and not data:
                        data = bytes.fromhex(payload_info.get("payload_hex"))
                    data_len = len(data)
                    tx_time = (max(size_bytes, data_len) * 10) / self.baud_rate

                    yield self.env.timeout(tx_time)

                    # 构建并发送帧
                    rs485_frame = self._build_frame(
                        device_id,
                        frame,
                        payload_hex=payload_info.get("payload_hex"),
                        field_values=payload_info.get("field_values"),
                        fill_strategy=payload_info.get("fill_strategy"),
                        size_bytes=payload_info.get("size_bytes"),
                    )
                    self._notify_message(rs485_frame)

                # 等待发送间隔
                interval = frame.get("interval", 0.1)
                yield self.env.timeout(interval)

    def _build_frame(
        self,
        device_id: str,
        frame_config: Dict[str, Any],
        payload_hex: Optional[str] = None,
        field_values: Optional[Dict[str, Any]] = None,
        fill_strategy: Optional[str] = None,
        size_bytes: Optional[int] = None,
    ) -> Dict[str, Any]:
        """构建 RS485 帧"""
        data = payload_hex if payload_hex is not None else frame_config.get("data", "")
        if isinstance(data, (bytes, bytearray)):
            data_hex = data.hex().upper()
        elif isinstance(data, list):
            data_hex = "".join(f"{b:02X}" for b in data)
        else:
            data_hex = str(data).upper()

        # 帧头（默认 0xAA55）
        header = frame_config.get("header", "AA55")
        # 数据长度
        data_len = size_bytes if size_bytes is not None else (len(bytes.fromhex(data_hex)) if data_hex else 0)

        # 计算校验和（简单累加）
        checksum = sum(bytes.fromhex(data_hex)) & 0xFF if data_hex else 0

        # 完整帧：帧头 + 长度 + 数据 + 校验
        full_frame = f"{header}{data_len:02X}{data_hex}{checksum:02X}"

        return {
            "message_id": str(uuid.uuid4()),
            "model_id": self.model_id,
            "protocol_type": "RS485",
            "device_id": device_id,
            "timestamp": self.env.now,
            "header": header,
            "data_length": data_len,
            "data_hex": data_hex,
            "checksum": checksum,
            "payload_hex": full_frame,
            "is_error": False,
            "field_values": field_values or {},
            "fill_strategy": fill_strategy or frame_config.get("fill_strategy"),
            "create_time": datetime.now(),
        }

    def _emit_collision(self, device_id: str) -> None:
        """发送冲突事件"""
        self._collision_count += 1
        collision_event = {
            "message_id": str(uuid.uuid4()),
            "model_id": self.model_id,
            "protocol_type": "RS485",
            "event_type": "collision",
            "device_id": device_id,
            "timestamp": self.env.now,
            "collision_count": self._collision_count,
            "create_time": datetime.now(),
        }

        if self._collision_callback:
            self._collision_callback(collision_event)
        self._notify_message(collision_event)

    def emit_message(self, message: Dict[str, Any]) -> None:
        """发送协议报文"""
        self._notify_message(message)

    def set_collision_callback(
        self, callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """设置冲突回调"""
        self._collision_callback = callback

    def get_collision_count(self) -> int:
        """获取冲突计数"""
        return self._collision_count

    def get_status(self) -> Dict[str, Any]:
        """获取模型状态"""
        base_status = super().get_status()
        base_status.update(
            {
                "baud_rate": self.baud_rate,
                "device_count": len(self.device_configs),
                "collision_count": self._collision_count,
                "bus_busy": self.bus.count > 0,
            }
        )
        return base_status








