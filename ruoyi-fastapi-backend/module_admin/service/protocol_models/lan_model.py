"""
LAN/以太网协议仿真模型
模拟交换机缓冲和排队延迟
"""
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, Generator, List, Optional

import simpy

from module_admin.service.protocol_models.base_protocol import BaseProtocolModel


class LANModel(BaseProtocolModel):
    """
    LAN/以太网仿真模型

    特点:
    - 使用 simpy.Store 模拟交换机缓冲区
    - 模拟排队延迟和处理延迟
    - 支持多播和广播
    """

    # 以太网参数
    MIN_FRAME_SIZE = 64  # 最小帧大小（字节）
    MAX_FRAME_SIZE = 1518  # 最大帧大小（字节）
    PREAMBLE_SIZE = 8  # 前导码大小
    IFG_TIME = 0.0000096  # 帧间隔（9.6μs，100Mbps）

    def __init__(
        self,
        env: simpy.Environment,
        model_id: str,
        config: Dict[str, Any],
        message_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        super().__init__(env, model_id, config, message_callback)
        # 交换机缓冲区
        self.switch_buffer = simpy.Store(env, capacity=config.get("buffer_size", 1000))
        # 链路带宽（bps）
        self.bandwidth = config.get("bandwidth", 100_000_000)  # 默认100Mbps
        # 处理延迟（秒）
        self.processing_delay = config.get("processing_delay", 0.00001)  # 10μs
        # 设备配置
        self.device_configs = config.get("devices", [])
        # 丢包计数
        self._drop_count = 0

    def start_processes(self) -> List[simpy.Process]:
        """启动发送和转发进程"""
        self._processes = []

        # 启动设备发送进程
        for device_cfg in self.device_configs:
            proc = self.env.process(self._device_process(device_cfg))
            self._processes.append(proc)

        # 启动交换机转发进程
        switch_proc = self.env.process(self._switch_process())
        self._processes.append(switch_proc)

        return self._processes

    def _device_process(self, device_config: Dict[str, Any]) -> Generator:
        """设备发送进程"""
        device_id = device_config.get("device_id", "unknown")
        packets = device_config.get("packets", [])

        while not self._stopped:
            for pkt_cfg in packets:
                if self._stopped:
                    break

                payload_info = {}
                supplier = pkt_cfg.get("payload_supplier")
                if callable(supplier):
                    payload_info = supplier(self.env.now) or {}

                if payload_info.get("payload_hex"):
                    pkt_cfg = dict(pkt_cfg)
                    pkt_cfg["payload"] = payload_info.get("payload_hex")

                # 构建以太网帧
                eth_frame = self._build_ethernet_frame(
                    device_id,
                    pkt_cfg,
                    field_values=payload_info.get("field_values"),
                    fill_strategy=payload_info.get("fill_strategy"),
                    size_bytes=payload_info.get("size_bytes"),
                )

                # 放入交换机缓冲区
                if len(self.switch_buffer.items) < self.switch_buffer.capacity:
                    self.switch_buffer.put(eth_frame)
                else:
                    # 缓冲区满，丢包
                    self._drop_count += 1
                    self._notify_drop(eth_frame)

                # 等待发送间隔
                interval = pkt_cfg.get("interval", 0.01)
                yield self.env.timeout(interval)

    def _switch_process(self) -> Generator:
        """交换机转发进程"""
        while not self._stopped:
            # 从缓冲区取帧
            frame = yield self.switch_buffer.get()

            # 处理延迟
            yield self.env.timeout(self.processing_delay)

            # 计算传输时间
            frame_size = frame.get("size_bytes", self.MIN_FRAME_SIZE)
            tx_time = (frame_size * 8) / self.bandwidth

            yield self.env.timeout(tx_time)

            # 转发帧
            self._notify_message(frame)

            # 帧间隔
            yield self.env.timeout(self.IFG_TIME)

    def _build_ethernet_frame(
        self,
        device_id: str,
        pkt_config: Dict[str, Any],
        field_values: Optional[Dict[str, Any]] = None,
        fill_strategy: Optional[str] = None,
        size_bytes: Optional[int] = None,
    ) -> Dict[str, Any]:
        """构建以太网帧"""
        # MAC 地址
        src_mac = pkt_config.get("src_mac", "00:00:00:00:00:01")
        dst_mac = pkt_config.get("dst_mac", "00:00:00:00:00:02")

        # IP 地址（如果有）
        src_ip = pkt_config.get("src_ip", "192.168.1.1")
        dst_ip = pkt_config.get("dst_ip", "192.168.1.2")

        # 端口号（如果有）
        src_port = pkt_config.get("src_port", 12345)
        dst_port = pkt_config.get("dst_port", 80)

        # 负载数据
        payload = pkt_config.get("payload", "")
        if isinstance(payload, (bytes, bytearray)):
            payload_hex = payload.hex().upper()
        elif isinstance(payload, list):
            payload_hex = "".join(f"{b:02X}" for b in payload)
        else:
            payload_hex = str(payload).upper()

        # 计算帧大小
        payload_len = len(bytes.fromhex(payload_hex)) if payload_hex else 0
        # 以太网头（14字节） + IP头（20字节） + TCP/UDP头（8-20字节） + 负载 + FCS（4字节）
        header_size = 14 + 20 + 8  # 简化计算
        frame_size = max(self.MIN_FRAME_SIZE, header_size + (size_bytes if size_bytes is not None else payload_len) + 4)

        # 计算 FCS（简化为 CRC32 低4字节）
        fcs = sum(bytes.fromhex(payload_hex)) & 0xFFFFFFFF if payload_hex else 0

        return {
            "message_id": str(uuid.uuid4()),
            "model_id": self.model_id,
            "protocol_type": "LAN",
            "device_id": device_id,
            "timestamp": self.env.now,
            "src_mac": src_mac,
            "dst_mac": dst_mac,
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "src_port": src_port,
            "dst_port": dst_port,
            "payload_hex": payload_hex,
            "size_bytes": frame_size,
            "fcs": fcs,
            "is_error": False,
            "field_values": field_values or {},
            "fill_strategy": fill_strategy or pkt_config.get("fill_strategy"),
            "create_time": datetime.now(),
        }

    def _notify_drop(self, frame: Dict[str, Any]) -> None:
        """通知丢包事件"""
        drop_event = {
            "message_id": str(uuid.uuid4()),
            "model_id": self.model_id,
            "protocol_type": "LAN",
            "event_type": "packet_drop",
            "timestamp": self.env.now,
            "dropped_frame_id": frame.get("message_id"),
            "drop_count": self._drop_count,
            "create_time": datetime.now(),
        }
        self._notify_message(drop_event)

    def emit_message(self, message: Dict[str, Any]) -> None:
        """发送协议报文"""
        self._notify_message(message)

    def get_drop_count(self) -> int:
        """获取丢包计数"""
        return self._drop_count

    def get_buffer_usage(self) -> int:
        """获取缓冲区使用量"""
        return len(self.switch_buffer.items)

    def get_status(self) -> Dict[str, Any]:
        """获取模型状态"""
        base_status = super().get_status()
        base_status.update(
            {
                "bandwidth": self.bandwidth,
                "device_count": len(self.device_configs),
                "buffer_usage": self.get_buffer_usage(),
                "buffer_capacity": self.switch_buffer.capacity,
                "drop_count": self._drop_count,
            }
        )
        return base_status


# Backward-compatible alias
LANProtocol = LANModel






