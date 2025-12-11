"""
MIL-STD-1553B 协议仿真模型
实现 BC（总线控制器）和 RT（远程终端）进程
"""
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, Generator, List, Optional

import simpy

from module_admin.service.protocol_models.base_protocol import BaseProtocolModel


class MIL1553BModel(BaseProtocolModel):
    """
    1553B 协议仿真模型

    特点:
    - BC 主导调度，按指令帧列表顺序发送
    - RT 监听并响应 BC 指令
    - 使用 simpy.Resource(capacity=1) 模拟总线独占
    - 模拟 12-32μs 响应时间
    """

    # 协议时序参数（秒）
    COMMAND_WORD_TIME = 0.00002  # 20μs 命令字传输时间
    RESPONSE_GAP_MIN = 0.000012  # 12μs 最小响应间隙
    RESPONSE_GAP_MAX = 0.000032  # 32μs 最大响应间隙
    STATUS_WORD_TIME = 0.00002  # 20μs 状态字传输时间
    DATA_WORD_TIME = 0.00002  # 20μs 每个数据字传输时间

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
        # RT 数据存储
        self.rt_store = simpy.Store(env)
        # 主帧周期（默认 20ms）
        self.major_frame_time = config.get("major_frame_time", 0.02)
        # 调度表
        self.schedule = config.get("schedule", [])
        # RT 地址列表
        self.rt_addresses = config.get("rt_addresses", [])
        # 错误帧注入队列
        self._error_frames: List[Dict[str, Any]] = []

    def start_processes(self) -> List[simpy.Process]:
        """启动 BC 和 RT 进程"""
        self._processes = []
        # 启动 BC 进程
        bc_proc = self.env.process(self._bc_process())
        self._processes.append(bc_proc)

        # 为每个 RT 地址启动 RT 进程
        for rt_addr in self.rt_addresses:
            rt_proc = self.env.process(self._rt_process(rt_addr))
            self._processes.append(rt_proc)

        return self._processes

    def _bc_process(self) -> Generator:
        """BC 进程 - 按调度表发送指令"""
        while not self._stopped:
            for frame in self.schedule:
                if self._stopped:
                    break

                payload_info = {}
                supplier = frame.get("payload_supplier")
                if callable(supplier):
                    payload_info = supplier(self.env.now) or {}

                if payload_info:
                    frame = dict(frame)
                    if payload_info.get("payload_hex"):
                        try:
                            frame["data"] = [int(payload_info["payload_hex"][:4], 16)]
                        except Exception:
                            frame["data"] = frame.get("data", [0x0000])
                    frame["field_values"] = payload_info.get("field_values")
                    frame["fill_strategy"] = payload_info.get("fill_strategy")

                # 申请总线独占
                with self.bus.request() as req:
                    yield req

                    # 发送命令字
                    yield self.env.timeout(self.COMMAND_WORD_TIME)
                    cmd_msg = self._build_command_word(frame)
                    self._notify_message(cmd_msg)

                    # 将命令放入 RT 存储
                    self.rt_store.put(frame)

                    # 等待 RT 响应间隙
                    response_gap = frame.get(
                        "response_gap",
                        (self.RESPONSE_GAP_MIN + self.RESPONSE_GAP_MAX) / 2,
                    )
                    yield self.env.timeout(response_gap)

                    # 检查是否需要注入错误帧
                    if self._error_frames:
                        error = self._error_frames.pop(0)
                        self._notify_message(error)

                # 帧间隔（用于分隔同一主帧内的调度项）
                interval = frame.get("interval", 0)
                if interval:
                    yield self.env.timeout(interval)

            # 主帧周期等待
            yield self.env.timeout(self.major_frame_time)

    def _rt_process(self, rt_address: int) -> Generator:
        """RT 进程 - 监听并响应"""
        while not self._stopped:
            # 等待匹配的命令
            command = yield self.rt_store.get(
                lambda x: x.get("rt_address") == rt_address
            )

            # 生成状态字响应
            yield self.env.timeout(self.RESPONSE_GAP_MIN)
            status_msg = self._build_status_word(rt_address, command)
            self._notify_message(status_msg)

            # 如果是 RT->BC 传输，发送数据字
            if command.get("tr_bit"):
                word_count = command.get("word_count", 1)
                for _ in range(word_count):
                    yield self.env.timeout(self.DATA_WORD_TIME)
                    data_msg = self._build_data_word(rt_address, command)
                    self._notify_message(data_msg)

    def _build_command_word(self, frame: Dict[str, Any]) -> Dict[str, Any]:
        """构建命令字消息"""
        rt_address = frame.get("rt_address", 0)
        sub_address = frame.get("sub_address", 0)
        tr_bit = frame.get("tr_bit", False)
        word_count = frame.get("word_count", 1)

        # 编码命令字（16位）
        command_word = (
            ((rt_address & 0x1F) << 11)
            | ((1 if tr_bit else 0) << 10)
            | ((sub_address & 0x1F) << 5)
            | (word_count & 0x1F)
        )

        return {
            "message_id": str(uuid.uuid4()),
            "model_id": self.model_id,
            "protocol_type": "1553B",
            "frame_type": "command_word",
            "timestamp": self.env.now,
            "rt_address": rt_address,
            "sub_address": sub_address,
            "tr_bit": tr_bit,
            "word_count": word_count,
            "raw_word": command_word,
            "payload_hex": f"{command_word:04X}",
            "field_values": frame.get("field_values", {}),
            "fill_strategy": frame.get("fill_strategy"),
            "create_time": datetime.now(),
        }

    def _build_status_word(
        self, rt_address: int, command: Dict[str, Any]
    ) -> Dict[str, Any]:
        """构建状态字消息"""
        # 状态字（16位）：RT地址 + 状态位
        status_word = (rt_address & 0x1F) << 11

        return {
            "message_id": str(uuid.uuid4()),
            "model_id": self.model_id,
            "protocol_type": "1553B",
            "frame_type": "status_word",
            "timestamp": self.env.now,
            "rt_address": rt_address,
            "raw_word": status_word,
            "payload_hex": f"{status_word:04X}",
            "field_values": command.get("field_values", {}),
            "fill_strategy": command.get("fill_strategy"),
            "create_time": datetime.now(),
        }

    def _build_data_word(
        self, rt_address: int, command: Dict[str, Any]
    ) -> Dict[str, Any]:
        """构建数据字消息"""
        # 模拟数据内容
        data = command.get("data", [0x0000])
        data_word = data[0] if data else 0x0000

        return {
            "message_id": str(uuid.uuid4()),
            "model_id": self.model_id,
            "protocol_type": "1553B",
            "frame_type": "data_word",
            "timestamp": self.env.now,
            "rt_address": rt_address,
            "raw_word": data_word,
            "payload_hex": f"{data_word:04X}",
            "field_values": command.get("field_values", {}),
            "fill_strategy": command.get("fill_strategy"),
            "size_bytes": 2,
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
                    "protocol_type": "1553B",
                    "frame_type": "error_frame",
                    "timestamp": self.env.now,
                    "is_error": True,
                    "error_type": "injected",
                    "payload_hex": "FFFF",
                    "create_time": datetime.now(),
                }
                self._error_frames.append(error_frame)
            return True

        return False








