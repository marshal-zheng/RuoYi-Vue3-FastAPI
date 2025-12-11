"""
仿真引擎核心
集成 SimPy 仿真运行器，支持协议模型
"""
import uuid
import time
import random
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from module_admin.service.alarm_detector import AlarmDetector
from module_admin.service.data_injection_strategy import (
    PayloadGenerator,
    IncrementStrategy,
    CycleStrategy,
)
from module_admin.service.fault_injector import FaultInjector
from module_admin.service.event_trigger import EventTriggerService
from module_admin.service.simulation_runner import SimulationRunner
from module_admin.service.protocol_models import (
    CANBusModel,
    LANModel,
    MIL1553BModel,
    RS485Model,
    BaseProtocolModel,
)
from module_admin.service.alarm_detector import AlarmDetector


class SimulationEngine:
    """
    仿真引擎
    集成 SimPy 运行器，管理仿真会话、生成报文、计算带宽
    """

    def __init__(
        self,
        session_id: str,
        topology_data: Dict[str, Any],
        injection_strategy: str = 'random',
        injection_params: Dict[str, Any] = None,
        fault_injector: Optional[FaultInjector] = None,
        event_service: Optional[EventTriggerService] = None,
        speed: float = 1.0,
        duration_limit: Optional[float] = None,
    ):
        """
        初始化仿真引擎
        
        参数:
            session_id: 会话ID
            topology_data: 拓扑数据，包含nodes和edges
            injection_strategy: 全局数据注入策略
            injection_params: 策略参数
            speed: 仿真速度（0.5x-4x）
            duration_limit: 仿真时长限制（秒）
        """
        self.session_id = session_id
        self.topology_data = topology_data
        self.injection_strategy = injection_strategy
        self.injection_params = injection_params or {}
        self.status = 'created'  # created/running/paused/stopped
        self.start_timestamp = None
        self.current_timestamp = None
        
        # 仿真数据缓存
        self.messages = []  # 报文列表
        self.bandwidth_data = []  # 带宽数据列表
        self.alarms = []  # 告警列表
        
        # 增量数据追踪（用于WebSocket增量推送）
        self._last_pushed_msg_index = 0
        self._last_pushed_bw_index = 0
        self._last_pushed_alarm_index = 0
        
        # 数据清理配置
        self._max_messages = 1000  # 最多保留1000条报文
        # 10分钟窗口：tick=0.1s 时每秒约10点，放宽至6000
        self._max_bandwidth_points = 6000
        # 运行期统计与节流
        self._port_stats: Dict[str, Dict[str, int]] = {}  # sent/dropped/collision
        self._last_drop_alarm_at: Dict[str, float] = {}
        self._last_congestion_alarm_at: Dict[str, float] = {}
        
        # 解析拓扑数据
        self.nodes = {}  # {node_id: node_data}
        self.edges = []  # 边列表
        self.port_configs = {}  # {node_id:port_id: config}
        self.edge_routes: Dict[str, List[Dict[str, Any]]] = {}
        
        self._parse_topology()

        # 初始化告警检测
        self._detect_initial_alarms()

        # 初始化报文内容生成器（使用全局策略）
        self.payload_generator = PayloadGenerator(default_strategy=self.injection_strategy)

        # 故障与事件
        self.fault_injector = fault_injector or FaultInjector()
        self.event_service = event_service or EventTriggerService()
        
        # 创建 SimPy 仿真运行器
        self.runner = SimulationRunner(
            session_id=session_id,
            topology_data=topology_data,
            tick_callback=self._on_simpy_tick,
            speed=speed,
            duration=duration_limit,
            tick_interval=0.1
        )

        # 协议模型实例
        self.protocol_models: List[BaseProtocolModel] = []
        self._init_protocol_models()

    def _parse_topology(self):
        """解析拓扑数据"""
        # 解析节点
        for node in self.topology_data.get('nodes', []):
            node_id = node.get('id')
            if node_id:
                self.nodes[node_id] = node
                
                # 解析端口配置
                node_data = node.get('data', {})
                ports = node_data.get('ports', [])
                for port in ports:
                    port_id = port.get('id')
                    if port_id:
                        key = f"{node_id}:{port_id}"
                        self.port_configs[key] = {
                            'node_id': node_id,
                            'port_id': port_id,
                            'port_name': port.get('name', port_id),
                            'protocol_type': port.get('type', 'LAN'),
                            'params': port.get('params', {}),
                            'message_config': port.get('message_config', {})
                        }
        
        # 解析边
        self.edges = self.topology_data.get('edges', [])
        # 构建源到目的的路由表，便于协议回调派发
        for edge in self.edges:
            source_node = edge.get('source') or edge.get('sourceId')
            source_port = edge.get('sourcePort') or edge.get('sourcePortId')
            target_node = edge.get('target') or edge.get('targetId')
            target_port = edge.get('targetPort') or edge.get('targetPortId')
            if not all([source_node, source_port, target_node, target_port]):
                continue
            source_key = f"{source_node}:{source_port}"
            self.edge_routes.setdefault(source_key, []).append(
                {
                    'target_node': target_node,
                    'target_port': target_port,
                    'edge': edge,
                }
            )

    def _get_node_name(self, node_id: str) -> str:
        """根据节点ID获取显示名称"""
        node = self.nodes.get(node_id, {})
        data = node.get('data', {}) if isinstance(node, dict) else {}
        return (
            data.get('label')
            or data.get('name')
            or node.get('label')
            or node.get('name')
            or node_id
        )

    def _protocol_size_profile(self, protocol_type: str) -> Dict[str, Optional[int]]:
        """按协议提供默认/上下限帧长"""
        pt = (protocol_type or '').upper()
        profiles = {
            '1553B': {'default': 32, 'min': 4, 'max': 64},
            'CAN': {'default': 16, 'min': 8, 'max': 64},  # CAN/CAN-FD 简化
            'RS422': {'default': 32, 'min': 1, 'max': 2048},
            'RS485': {'default': 32, 'min': 1, 'max': 2048},
            'LAN': {'default': 64, 'min': 64, 'max': 1518},  # 以太网帧 64~1518
        }
        return profiles.get(pt, {'default': 64, 'min': 1, 'max': None})

    def _get_protocol_params(self, protocol_type: str) -> Dict[str, Any]:
        """
        获取协议物理参数
        
        返回:
            bandwidth_bps: 带宽（bps）
            propagation_delay_us: 传播延迟（微秒/米）
            processing_delay_us: 处理延迟（微秒）
            bit_time_us: 每比特时间（微秒）
        """
        pt = (protocol_type or '').upper()
        params = {
            '1553B': {
                'bandwidth_bps': 1_000_000,      # 1 Mbps
                'propagation_delay_us': 5.0,     # ~5μs/m (电缆传播)
                'processing_delay_us': 4.0,      # RT响应时间 4-12μs
                'bit_time_us': 1.0,              # 1μs/bit
            },
            'CAN': {
                'bandwidth_bps': 500_000,        # 500 Kbps (标准CAN)
                'propagation_delay_us': 5.0,
                'processing_delay_us': 10.0,     # CAN控制器处理
                'bit_time_us': 2.0,              # 2μs/bit @ 500Kbps
            },
            'RS422': {
                'bandwidth_bps': 10_000_000,     # 10 Mbps (最大)
                'propagation_delay_us': 5.0,
                'processing_delay_us': 2.0,      # UART处理
                'bit_time_us': 0.1,
            },
            'RS485': {
                'bandwidth_bps': 10_000_000,
                'propagation_delay_us': 5.0,
                'processing_delay_us': 2.0,
                'bit_time_us': 0.1,
            },
            'LAN': {
                'bandwidth_bps': 100_000_000,    # 100 Mbps
                'propagation_delay_us': 5.0,
                'processing_delay_us': 50.0,     # 交换机/网卡处理
                'bit_time_us': 0.01,
            },
        }
        return params.get(pt, {
            'bandwidth_bps': 10_000_000,
            'propagation_delay_us': 5.0,
            'processing_delay_us': 10.0,
            'bit_time_us': 0.1,
        })

    def _calculate_latency(
        self,
        protocol_type: str,
        size_bytes: int,
        port_params: Dict[str, Any],
        edge_data: Dict[str, Any],
    ) -> float:
        """
        计算真实传输时延（秒）
        
        时延组成:
        1. 传输时延 = 报文大小 / 带宽
        2. 传播时延 = 链路长度 × 传播速度
        3. 处理时延 = 协议固有处理时间
        4. 排队时延 = 基于当前负载的随机抖动
        
        参数:
            protocol_type: 协议类型
            size_bytes: 报文大小（字节）
            port_params: 端口配置参数
            edge_data: 边/链路数据
            
        返回:
            总时延（秒）
        """
        proto_params = self._get_protocol_params(protocol_type)
        
        # 1. 传输时延 (Transmission Delay)
        # 使用端口配置的带宽或协议默认带宽
        bandwidth_bps = (
            port_params.get('bandwidth_bps')
            or (port_params.get('bandwidth', 0) * 1_000_000)  # Mbps -> bps
            or (port_params.get('maxBandwidthMbps', 0) * 1_000_000)
            or proto_params['bandwidth_bps']
        )
        transmission_delay_s = (size_bytes * 8) / bandwidth_bps
        
        # 2. 传播时延 (Propagation Delay)
        # 链路长度（米），默认10米
        link_length_m = (
            edge_data.get('length', 0)
            or edge_data.get('cable_length', 0)
            or port_params.get('cable_length', 10)
        )
        propagation_delay_s = (link_length_m * proto_params['propagation_delay_us']) / 1_000_000
        
        # 3. 处理时延 (Processing Delay)
        processing_delay_s = proto_params['processing_delay_us'] / 1_000_000
        
        # 4. 排队时延 (Queuing Delay) - 基于负载的随机抖动
        # 模拟网络负载波动，负载越高抖动越大
        base_jitter_us = random.uniform(1, 20)  # 1-20μs 基础抖动
        queuing_delay_s = base_jitter_us / 1_000_000
        
        # 总时延
        total_latency = (
            transmission_delay_s
            + propagation_delay_s
            + processing_delay_s
            + queuing_delay_s
        )
        
        return total_latency

    def _apply_default_frame_length(
        self,
        message_config: Dict[str, Any],
        protocol_type: str,
        port_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """为不同协议补齐默认帧长，优先使用端口/业务配置"""
        if not isinstance(message_config, dict):
            return {}

        cfg = dict(message_config)
        header = dict(cfg.get('header') or {})

        size_profile = self._protocol_size_profile(protocol_type)
        frame_length = (
            header.get('frameLength')
            or header.get('frame_length')
            or (port_params or {}).get('byte_count')
            or size_profile.get('default')
        )

        # 按协议上下限约束
        min_len = size_profile.get('min') or 1
        max_len = size_profile.get('max')
        if frame_length < min_len:
            frame_length = min_len
        if max_len and frame_length > max_len:
            frame_length = max_len

        header['frameLength'] = frame_length

        cfg['header'] = header
        return cfg

    def _detect_initial_alarms(self):
        """检测初始告警"""
        alarms = AlarmDetector.detect_all_alarms(self.topology_data)
        for alarm in alarms:
            alarm['session_id'] = self.session_id
            self.alarms.append(alarm)

    def _init_protocol_models(self):
        """
        根据拓扑初始化协议模型并注册消息回调
        """
        # 将端口按协议分组
        grouped_ports: Dict[str, List[Dict[str, Any]]] = {}
        for key, cfg in self.port_configs.items():
            protocol = (cfg.get('protocol_type') or 'LAN').upper()
            cfg = dict(cfg)
            cfg['source_key'] = key
            grouped_ports.setdefault(protocol, []).append(cfg)

        for protocol, port_list in grouped_ports.items():
            if protocol == 'CAN':
                model = self._build_can_model(port_list)
            elif protocol in ('RS485', 'RS422'):
                model = self._build_rs485_model(port_list)
            elif protocol == '1553B':
                model = self._build_1553b_model(port_list)
            else:
                model = self._build_lan_model(port_list)

            if model:
                self.protocol_models.append(model)
                model.start_processes()

    def _make_payload_supplier(
        self,
        protocol_type: str,
        source_node: str,
        source_port: str,
        message_config: Dict[str, Any],
        port_params: Dict[str, Any],
    ) -> Callable[[float], Dict[str, Any]]:
        """
        创建协议专用的负载生成器，复用现有 PayloadGenerator
        """
        cfg = self._apply_default_frame_length(
            message_config or {},
            protocol_type,
            port_params,
        )
        # 选择一个目标用于上下文（若有多个目标，则取首个）
        targets = self.edge_routes.get(f"{source_node}:{source_port}", [])
        target = targets[0] if targets else {}

        def _supplier(sim_time: float) -> Dict[str, Any]:
            context = {
                'session_id': self.session_id,
                'elapsed_time': sim_time,
                'tick_count': int(sim_time / 0.1),
                'source_node': source_node,
                'source_port': source_port,
                'target_node': target.get('target_node'),
                'target_port': target.get('target_port'),
                **self.injection_params,
            }
            result = self.payload_generator.generate_payload(cfg, context)
            payload_hex = result.get('payload_hex', '')
            payload_bytes = bytes.fromhex(payload_hex) if payload_hex else b''
            size_profile = self._protocol_size_profile(protocol_type)
            min_len = size_profile.get('min') or 1
            max_len = size_profile.get('max')
            size_bytes = len(payload_bytes) if payload_bytes else cfg.get('header', {}).get('frameLength') or size_profile.get('default')
            if max_len:
                size_bytes = min(size_bytes, max_len)
            size_bytes = max(size_bytes, min_len)
            return {
                'payload_hex': payload_hex,
                'field_values': result.get('field_values', {}),
                'fill_strategy': cfg.get('fillStrategy', 'random'),
                'size_bytes': size_bytes,
            }

        return _supplier

    def _build_can_model(self, ports: List[Dict[str, Any]]) -> Optional[BaseProtocolModel]:
        """构建 CAN 总线模型"""
        device_configs = []
        for idx, port in enumerate(ports):
            node_id = port.get('node_id')
            port_id = port.get('port_id')
            params = port.get('params', {}) or {}
            message_cfg = port.get('message_config', {}) or {}
            header_cfg = message_cfg.get('header', {}) or {}
            interval = max(0.05, (params.get('frequency', 200)) / 1000)

            supplier = self._make_payload_supplier(
                'CAN',
                node_id,
                port_id,
                message_cfg,
                params,
            )

            device_configs.append(
                {
                    'device_id': port.get('source_key'),
                    'messages': [
                        {
                            'can_id': header_cfg.get('canId') or header_cfg.get('can_id') or 0x100 + idx,
                            'dlc': header_cfg.get('frameLength') or header_cfg.get('frame_length') or 8,
                            'extended': header_cfg.get('extended', False),
                            'interval': interval,
                            'payload_supplier': supplier,
                        }
                    ],
                }
            )

        if not device_configs:
            return None

        return CANBusModel(
            env=self.runner.env,
            model_id=f"{self.session_id}-CAN",
            config={'devices': device_configs, 'baud_rate': 500000},
            message_callback=self._handle_protocol_message,
        )

    def _build_rs485_model(self, ports: List[Dict[str, Any]]) -> Optional[BaseProtocolModel]:
        """构建 RS485 半双工模型"""
        device_configs = []
        for idx, port in enumerate(ports):
            node_id = port.get('node_id')
            port_id = port.get('port_id')
            params = port.get('params', {}) or {}
            message_cfg = port.get('message_config', {}) or {}
            header_cfg = message_cfg.get('header', {}) or {}
            interval = max(0.05, (params.get('frequency', 200)) / 1000)

            supplier = self._make_payload_supplier(
                'RS485',
                node_id,
                port_id,
                message_cfg,
                params,
            )

            device_configs.append(
                {
                    'device_id': port.get('source_key'),
                    'frames': [
                        {
                            'header': header_cfg.get('header') or header_cfg.get('frameHeader') or 'AA55',
                            'interval': interval,
                            'payload_supplier': supplier,
                        }
                    ],
                }
            )

        if not device_configs:
            return None

        return RS485Model(
            env=self.runner.env,
            model_id=f"{self.session_id}-RS485",
            config={'devices': device_configs, 'baud_rate': 9600},
            message_callback=self._handle_protocol_message,
        )

    def _build_lan_model(self, ports: List[Dict[str, Any]]) -> Optional[BaseProtocolModel]:
        """构建 LAN/以太网模型"""
        device_configs = []
        for idx, port in enumerate(ports):
            node_id = port.get('node_id')
            port_id = port.get('port_id')
            params = port.get('params', {}) or {}
            message_cfg = port.get('message_config', {}) or {}
            header_cfg = message_cfg.get('header', {}) or {}
            interval = max(0.01, (params.get('frequency', 200)) / 1000)

            supplier = self._make_payload_supplier(
                'LAN',
                node_id,
                port_id,
                message_cfg,
                params,
            )

            device_configs.append(
                {
                    'device_id': port.get('source_key'),
                    'packets': [
                        {
                            'src_mac': header_cfg.get('srcMac') or header_cfg.get('src_mac') or f'00:00:00:00:{idx:02X}:01',
                            'dst_mac': header_cfg.get('dstMac') or header_cfg.get('dst_mac') or f'00:00:00:00:{idx:02X}:02',
                            'src_ip': header_cfg.get('srcIp') or header_cfg.get('src_ip') or '192.168.1.1',
                            'dst_ip': header_cfg.get('dstIp') or header_cfg.get('dst_ip') or '192.168.1.2',
                            'interval': interval,
                            'payload_supplier': supplier,
                        }
                    ],
                }
            )

        if not device_configs:
            return None

        return LANModel(
            env=self.runner.env,
            model_id=f"{self.session_id}-LAN",
            config={'devices': device_configs, 'bandwidth': 100_000_000},
            message_callback=self._handle_protocol_message,
        )

    def _build_1553b_model(self, ports: List[Dict[str, Any]]) -> Optional[BaseProtocolModel]:
        """构建 1553B 模型（简化：将端口映射为 RT）"""
        rt_addresses = []
        schedule = []
        for idx, port in enumerate(ports):
            rt_addr = idx + 1
            rt_addresses.append(rt_addr)
            params = port.get('params', {}) or {}
            message_cfg = port.get('message_config', {}) or {}
            header_cfg = message_cfg.get('header', {}) or {}
            interval = max(0.01, (params.get('frequency', 200)) / 1000)
            supplier = self._make_payload_supplier(
                '1553B',
                port.get('node_id'),
                port.get('port_id'),
                message_cfg,
                params,
            )
            schedule.append(
                {
                    'rt_address': rt_addr,
                    'sub_address': header_cfg.get('subAddress', 1),
                    'tr_bit': header_cfg.get('trBit', False),
                    'word_count': header_cfg.get('wordCount', 1),
                    'interval': interval,
                    'payload_supplier': supplier,
                }
            )

        if not rt_addresses:
            return None

        return MIL1553BModel(
            env=self.runner.env,
            model_id=f"{self.session_id}-1553B",
            config={'rt_addresses': rt_addresses, 'schedule': schedule},
            message_callback=self._handle_protocol_message,
        )

    async def start(self):
        """启动仿真"""
        if self.status == 'running':
            return
        
        self.status = 'running'
        self.start_timestamp = time.time()
        self.current_timestamp = self.start_timestamp
        
        # 启动 SimPy 仿真运行器（在独立线程中运行）
        self.runner.start()

    async def stop(self):
        """停止仿真"""
        if self.status == 'stopped':
            return
        
        self.status = 'stopped'
        
        # 停止 SimPy 仿真运行器
        self.runner.stop()
        # 停止协议模型
        for model in self.protocol_models:
            model.stop()
        
        # 清理数据填充策略的状态
        IncrementStrategy.reset_counters(self.session_id)
        CycleStrategy.reset_indices(self.session_id)

    async def pause(self):
        """暂停仿真"""
        if self.status != 'running':
            return
        self.status = 'paused'
        self.runner.pause()

    async def resume(self):
        """继续仿真"""
        if self.status not in ['running', 'paused']:
            return
        self.status = 'running'
        self.runner.resume()

    def set_speed(self, speed: float):
        """设置仿真速度（0.5x-4x）"""
        self.runner.set_speed(speed)

    async def step_once(self):
        """单步执行一个时间片"""
        self.status = 'paused'
        self.runner.step_once()

    def set_duration(self, duration: Optional[float]):
        """设置自动停止时长（秒）"""
        self.runner.set_duration(duration)

    def _on_simpy_tick(self, simpy_time: float):
        """
        SimPy tick 回调
        每个仿真时间片调用一次，用于生成报文和计算带宽
        
        参数:
            simpy_time: SimPy 环境当前时间（仿真时间）
        """
        # 更新当前时间戳
        self.current_timestamp = self.start_timestamp + simpy_time
        
        # 若未绑定协议模型，兼容旧路径生成报文
        if not self.protocol_models:
            messages = self._generate_messages(simpy_time)
            self.messages.extend(messages)

        # 计算带宽
        bandwidth_data = self._calculate_bandwidth(simpy_time)
        self.bandwidth_data.extend(bandwidth_data)
        
        # 定期清理旧数据，防止内存泄漏
        self._cleanup_old_data()

    def _handle_protocol_message(self, proto_msg: Dict[str, Any]):
        """
        协议模型消息回调：将协议事件映射为通用报文并派发到拓扑链路
        """
        source_key = proto_msg.get('device_id') or proto_msg.get('source_key')
        if not source_key:
            return

        routes = self.edge_routes.get(source_key, [])
        if not routes:
            return

        if ':' in source_key:
            source_node, source_port = source_key.split(':', 1)
        else:
            source_node, source_port = source_key, ''

        sim_time = proto_msg.get('timestamp', self.runner.env.now)
        send_timestamp = (self.start_timestamp or time.time()) + sim_time
        payload_hex = proto_msg.get('payload_hex', '')
        size_bytes = proto_msg.get('size_bytes')
        if not size_bytes and payload_hex:
            size_bytes = max(1, len(payload_hex) // 2)
        size_bytes = size_bytes or proto_msg.get('dlc') or proto_msg.get('data_length') or 1

        port_config = self.port_configs.get(source_key, {}) or {}
        port_params = port_config.get('params', {}) or {}
        protocol_type = proto_msg.get('protocol_type') or port_config.get('protocol_type', 'LAN')

        for route in routes:
            target_node = route.get('target_node')
            target_port = route.get('target_port')
            edge = route.get('edge', {})
            edge_id = edge.get('id', f"{source_node}-{target_node}")

            # 故障注入：断链/丢包/延迟/限速/篡改
            fault_effect = self.fault_injector.apply_effects(
                self.session_id,
                edge_id,
                {
                    'payload_hex': payload_hex,
                    'sender_node_id': source_node,
                    'receiver_node_id': target_node,
                    'sender_port_id': source_port,
                    'receiver_port_id': target_port,
                    'protocol_type': protocol_type,
                },
            )
            fault_reasons = fault_effect.get('reasons', [])
            if fault_effect.get('drop'):
                self._record_drop(source_key)
                self._emit_drop_alarm(edge_id, source_node, target_node, fault_reasons)
                continue
            extra_delay = fault_effect.get('delay', 0.0)
            payload_hex = fault_effect.get('payload_hex', payload_hex)
            is_error_frame = proto_msg.get('is_error_frame', False) or fault_effect.get('error_frame', False)

            real_latency = self._calculate_latency(
                protocol_type=protocol_type,
                size_bytes=size_bytes,
                port_params=port_params,
                edge_data=edge,
            )

            message = {
                'message_id': str(uuid.uuid4()),
                'session_id': self.session_id,
                'sender_node_id': source_node,
                'sender_node_name': self._get_node_name(source_node),
                'sender_port_id': source_port,
                'sender_port_name': port_config.get('port_name', source_port),
                'receiver_node_id': target_node,
                'receiver_node_name': self._get_node_name(target_node),
                'receiver_port_id': target_port,
                'receiver_port_name': self.port_configs.get(f"{target_node}:{target_port}", {}).get(
                    'port_name', target_port
                ),
                'protocol_type': protocol_type,
                'size_bytes': size_bytes,
                'send_timestamp': send_timestamp,
                'receive_timestamp': send_timestamp + real_latency + extra_delay,
                'create_time': datetime.now(),
                'payload_hex': payload_hex,
                'field_values': proto_msg.get('field_values', {}),
                'fill_strategy': proto_msg.get('fill_strategy', self.injection_strategy),
                'error_frame': is_error_frame,
                'fault_reasons': fault_reasons,
            }

            self.messages.append(message)

            # 记录统计
            self._record_send(source_key)

        # 如果是协议事件（如碰撞），生成告警
        if proto_msg.get('event_type') == 'collision':
            self._emit_collision_alarm(proto_msg, source_node)

    def _generate_messages(self, simpy_time: float) -> List[Dict[str, Any]]:
        """
        生成报文（基于 SimPy 时间）
        
        参数:
            simpy_time: SimPy 环境当前时间（仿真时间，秒）
            
        返回:
            报文列表
        """
        messages = []
        tick_interval = 0.1  # 100ms
        
        for edge in self.edges:
            # 兼容两种字段格式
            source_node = edge.get('source') or edge.get('sourceId')
            source_port = edge.get('sourcePort') or edge.get('sourcePortId')
            target_node = edge.get('target') or edge.get('targetId')
            target_port = edge.get('targetPort') or edge.get('targetPortId')
            
            if not all([source_node, source_port, target_node, target_port]):
                continue
            
            edge_id = edge.get('id', f"{source_node}-{target_node}")

            # 获取源端口配置
            source_key = f"{source_node}:{source_port}"
            port_config = self.port_configs.get(source_key)
            
            if not port_config:
                continue
            
            # 获取发送频率（毫秒）
            params = port_config.get('params', {})
            frequency_ms = params.get('frequency', 200)  # 默认200ms，增强可视化起伏
            
            # 判断是否应该发送报文（基于仿真时间）
            if simpy_time > 0 and int(simpy_time * 1000) % int(frequency_ms) < tick_interval * 1000:
                # 获取消息配置
                message_config = port_config.get('message_config', {})
                
                # 如果没有配置策略，使用全局策略
                if not message_config.get('fillStrategy'):
                    message_config['fillStrategy'] = self.injection_strategy
                    message_config['strategyParams'] = self.injection_params

                # 为不同协议设置默认帧长，避免固定64B
                message_config = self._apply_default_frame_length(
                    message_config,
                    port_config.get('protocol_type', 'LAN'),
                    params
                )
                
                # 构建生成上下文
                context = {
                    'session_id': self.session_id,
                    'elapsed_time': simpy_time,
                    'tick_count': int(simpy_time / tick_interval),
                    'source_node': source_node,
                    'source_port': source_port,
                    'target_node': target_node,
                    'target_port': target_port,
                    **self.injection_params,
                }
                
                # 生成报文内容
                payload_result = self.payload_generator.generate_payload(message_config, context)

                fault_effect = self.fault_injector.apply_effects(
                    self.session_id,
                    edge_id,
                    {
                        'payload_hex': payload_result.get('payload_hex', ''),
                        'sender_node_id': source_node,
                        'receiver_node_id': target_node,
                        'sender_port_id': source_port,
                        'receiver_port_id': target_port,
                        'protocol_type': port_config.get('protocol_type', 'LAN'),
                    },
                )
                fault_reasons = fault_effect.get('reasons', [])
                if fault_effect.get('drop'):
                    self._record_drop(source_key)
                    self._emit_drop_alarm(edge_id, source_node, target_node, fault_reasons)
                    continue
                extra_delay = fault_effect.get('delay', 0.0)
                is_error_frame = fault_effect.get('error_frame', False)
                payload_hex = fault_effect.get('payload_hex', payload_result.get('payload_hex', ''))

                # 计算实际报文大小：优先 payload 长度，其次帧长/业务配置，并按协议上下限修正
                payload_size = len(payload_result.get('payload', b''))
                header_cfg = message_config.get('header') or {}
                header_frame_length = header_cfg.get('frameLength')
                size_profile = self._protocol_size_profile(port_config.get('protocol_type', 'LAN'))
                default_size = (
                    header_frame_length
                    or params.get('byte_count')
                    or size_profile.get('default')
                )
                min_len = size_profile.get('min') or 1
                max_len = size_profile.get('max')

                if payload_size > 0:
                    actual_size = payload_size
                else:
                    actual_size = default_size
                    if max_len:
                        actual_size = min(actual_size, max_len)
                actual_size = max(actual_size, min_len)
                
                # 计算真实时延
                protocol_type = port_config.get('protocol_type', 'LAN')
                real_latency = self._calculate_latency(
                    protocol_type=protocol_type,
                    size_bytes=actual_size,
                    port_params=params,
                    edge_data=edge,
                )
                
                # 生成报文
                message = {
                    'message_id': str(uuid.uuid4()),
                    'session_id': self.session_id,
                    'sender_node_id': source_node,
                    'sender_node_name': self._get_node_name(source_node),
                    'sender_port_id': source_port,
                    'sender_port_name': port_config.get('port_name', source_port),
                    'receiver_node_id': target_node,
                    'receiver_node_name': self._get_node_name(target_node),
                    'receiver_port_id': target_port,
                    'receiver_port_name': self.port_configs.get(f"{target_node}:{target_port}", {}).get(
                        'port_name', target_port
                    ),
                    'protocol_type': protocol_type,
                    'size_bytes': actual_size,
                    'send_timestamp': self.current_timestamp,
                    'receive_timestamp': self.current_timestamp + real_latency + extra_delay,
                    'create_time': datetime.now(),
                    'payload_hex': payload_hex,
                    'field_values': payload_result.get('field_values', {}),
                    'fill_strategy': message_config.get('fillStrategy', 'random'),
                    'error_frame': is_error_frame,
                    'fault_reasons': fault_reasons,
                }
                messages.append(message)
        
        return messages

    def _calculate_bandwidth(self, simpy_time: float) -> List[Dict[str, Any]]:
        """
        计算带宽（基于 SimPy 时间）
        
        参数:
            simpy_time: SimPy 环境当前时间（仿真时间，秒）
            
        返回:
            带宽数据列表
        """
        bandwidth_data = []
        tick_interval = 0.1  # 100ms
        # 根据当前速度动态调整统计窗口，速度越快窗口越短，最短0.25s
        runner_speed = self.runner.get_status().get("speed", 1.0) if self.runner else 1.0
        clamped_speed = max(0.5, min(float(runner_speed or 1.0), 4.0))
        window_span = max(0.25, 1.0 / clamped_speed)
        
        # 统计每个端口的报文数量和大小
        port_stats = {}  # {node_id:port_id: {count, total_bytes}}
        
        # 只统计最近 window_span 内的报文（滑动窗口）
        recent_messages = [
            msg for msg in self.messages
            if self.current_timestamp - msg['send_timestamp'] <= window_span
        ]
        
        # 窗口时长
        window_start = max(self.start_timestamp, self.current_timestamp - window_span)
        window_seconds = max(tick_interval, window_span)
        
        for msg in recent_messages:
            sender_key = f"{msg['sender_node_id']}:{msg['sender_port_id']}"
            if sender_key not in port_stats:
                port_stats[sender_key] = {'count': 0, 'total_bytes': 0}
            port_stats[sender_key]['count'] += 1
            port_stats[sender_key]['total_bytes'] += msg['size_bytes']
        
        # 计算每个端口的带宽
        for port_key, stats in port_stats.items():
            node_id, port_id = port_key.split(':', 1)
            port_config = self.port_configs.get(port_key)
            
            if not port_config:
                continue
            
            # 可视化带宽上限（Mbps），用于负载率显示优先级：
            # 1) vizBandwidthMbps（仅影响展示）
            # 2) maxBandwidthMbps / bandwidth（物理/配置值）
            # 3) 默认 0.2 Mbps（保证曲线有足够起伏）
            params = port_config.get('params', {}) or {}
            max_bandwidth_mbps = (
                params.get('vizBandwidthMbps')
                or params.get('maxBandwidthMbps')
                or params.get('bandwidth')
                or 0.2
            )

            # 计算即时带宽（加入轻微抖动模拟真实网络波动）
            base_bandwidth = (stats['total_bytes'] * 8) / (1_000_000 * window_seconds)
            jitter = random.uniform(0.85, 1.2)
            bandwidth_mbps = round(base_bandwidth * jitter, 4)
            load_percent = round(min(100, (bandwidth_mbps / max_bandwidth_mbps) * 100), 2)
            
            bandwidth_data.append({
                'session_id': self.session_id,
                'node_id': node_id,
                'port_id': port_id,
                'protocol_type': port_config.get('protocol_type', 'LAN'),
                'timestamp': self.current_timestamp,
                'bandwidth_mbps': bandwidth_mbps,
                'load_percent': load_percent,
                'message_count': stats['count'],
                'create_time': datetime.now()
            })

            # 拥塞/超限告警
            self._detect_congestion_and_alarm(port_key, bandwidth_mbps, max_bandwidth_mbps, load_percent)
        
        return bandwidth_data

    def get_messages(self, start_time: Optional[float] = None, end_time: Optional[float] = None) -> List[Dict[str, Any]]:
        """获取报文列表"""
        messages = self.messages
        if start_time:
            messages = [m for m in messages if m['send_timestamp'] >= start_time]
        if end_time:
            messages = [m for m in messages if m['send_timestamp'] <= end_time]
        return messages

    def get_bandwidth_data(self, port_id: Optional[str] = None, start_time: Optional[float] = None, end_time: Optional[float] = None) -> List[Dict[str, Any]]:
        """获取带宽数据"""
        data = self.bandwidth_data
        if port_id:
            data = [d for d in data if d['port_id'] == port_id]
        if start_time:
            data = [d for d in data if d['timestamp'] >= start_time]
        if end_time:
            data = [d for d in data if d['timestamp'] <= end_time]
        return data

    def get_alarms(self, alarm_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取告警列表"""
        alarms = self.alarms
        if alarm_type:
            alarms = [a for a in alarms if a['alarm_type'] == alarm_type]
        return alarms

    def get_status(self) -> Dict[str, Any]:
        """获取仿真状态（集成 SimPy 运行器状态）"""
        runner_status = self.runner.get_status()
        
        return {
            'session_id': self.session_id,
            'status': self.status,
            'start_timestamp': self.start_timestamp,
            'current_timestamp': self.current_timestamp,
            'elapsed_time': self.current_timestamp - self.start_timestamp if self.start_timestamp else 0,
            'simpy_time': runner_status.get('env_now', 0),
            'speed': runner_status.get('speed', 1.0),
            'message_count': len(self.messages),
            'bandwidth_data_count': len(self.bandwidth_data),
            'alarm_count': len(self.alarms)
        }

    def _cleanup_old_data(self):
        """清理旧数据，防止内存泄漏"""
        # 清理超出限制的报文
        if len(self.messages) > self._max_messages:
            # 调整推送索引
            remove_count = len(self.messages) - self._max_messages
            self._last_pushed_msg_index = max(0, self._last_pushed_msg_index - remove_count)
            self.messages = self.messages[-self._max_messages:]
        
        # 清理超出限制的带宽数据
        if len(self.bandwidth_data) > self._max_bandwidth_points:
            remove_count = len(self.bandwidth_data) - self._max_bandwidth_points
            self._last_pushed_bw_index = max(0, self._last_pushed_bw_index - remove_count)
            self.bandwidth_data = self.bandwidth_data[-self._max_bandwidth_points:]

    def get_new_messages(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取增量报文数据（未推送过的）"""
        new_messages = self.messages[self._last_pushed_msg_index:]
        # 更新索引
        self._last_pushed_msg_index = len(self.messages)
        # 限制返回数量
        return new_messages[-limit:] if len(new_messages) > limit else new_messages

    def get_new_bandwidth_data(self) -> List[Dict[str, Any]]:
        """获取增量带宽数据（未推送过的）"""
        new_data = self.bandwidth_data[self._last_pushed_bw_index:]
        # 更新索引
        self._last_pushed_bw_index = len(self.bandwidth_data)
        return new_data

    def get_new_alarms(self) -> List[Dict[str, Any]]:
        """获取增量告警数据（未推送过的）"""
        new_alarms = self.alarms[self._last_pushed_alarm_index:]
        # 更新索引
        self._last_pushed_alarm_index = len(self.alarms)
        return new_alarms

    # ==================== 运行期告警辅助 ====================
    def _push_alarm(self, alarm: Dict[str, Any]) -> None:
        """追加告警并带上会话信息"""
        alarm = dict(alarm)
        alarm['session_id'] = self.session_id
        alarm['create_time'] = datetime.now()
        self.alarms.append(alarm)

    def _record_send(self, port_key: str) -> None:
        stats = self._port_stats.setdefault(port_key, {'sent': 0, 'dropped': 0, 'collision': 0})
        stats['sent'] += 1

    def _record_drop(self, port_key: str) -> None:
        stats = self._port_stats.setdefault(port_key, {'sent': 0, 'dropped': 0, 'collision': 0})
        stats['dropped'] += 1

    def _record_collision(self, port_key: str) -> None:
        stats = self._port_stats.setdefault(port_key, {'sent': 0, 'dropped': 0, 'collision': 0})
        stats['collision'] += 1

    def _emit_drop_alarm(self, edge_id: str, source_node: str, target_node: str, reasons: list = None) -> None:
        """
        发送丢包/故障告警
        @param reasons: 故障原因列表，如 ['disconnect'], ['packet_loss'], ['bandwidth_limit'] 等
        """
        now = self.current_timestamp or time.time()
        last = self._last_drop_alarm_at.get(edge_id, 0)
        # 节流：同一链路2秒内只告警一次
        if now - last < 2:
            return
        self._last_drop_alarm_at[edge_id] = now
        
        reasons = reasons or []
        primary_reason = reasons[0] if reasons else 'packet_loss'
        
        reason_label_map = {
            'packet_loss': '丢包',
            'disconnect': '链路断开',
            'bandwidth_limit': '限速丢弃',
            'device_failure': '设备故障',
            'noise_frame': '噪声帧',
            'payload_corrupt': '数据篡改',
        }
        
        # 主因标签
        primary_label = reason_label_map.get(primary_reason, '丢包')
        # 如果有多个原因，附加提示
        if len(reasons) > 1:
            message = f'链路 {edge_id} {primary_label}（共{len(reasons)}种故障）'
        else:
            message = f'链路 {edge_id} {primary_label}'
        
        alarm = {
            'alarm_id': str(uuid.uuid4()),
            'alarm_type': primary_reason,
            'severity': 'warning',
            'message': message,
            'timestamp': now,
            'details': {
                'edge_id': edge_id,
                'source_node': source_node,
                'target_node': target_node,
                'reasons': reasons,  # 全量原因数组
                'primary_reason': primary_reason,
            }
        }
        self._push_alarm(alarm)

    def _emit_collision_alarm(self, proto_msg: Dict[str, Any], source_node: str) -> None:
        port_key = proto_msg.get('device_id')
        self._record_collision(port_key or '')
        alarm = AlarmDetector.detect_collision(
            device_ids=proto_msg.get('collision_devices', [source_node]) if isinstance(proto_msg.get('collision_devices'), list) else [source_node],
            collision_time=self.current_timestamp or time.time(),
            bus_id=proto_msg.get('model_id')
        )
        self._push_alarm(alarm)

    def _detect_congestion_and_alarm(self, port_key: str, bandwidth_mbps: float, limit_mbps: float, load_percent: float) -> None:
        alarms = AlarmDetector.detect_bandwidth_alarm(
            port_id=port_key,
            bandwidth_mbps=bandwidth_mbps,
            limit_mbps=limit_mbps
        )
        now = self.current_timestamp or time.time()
        if not alarms:
            return
        # 节流：同一端口1秒内只推一次拥塞/超限
        last = self._last_congestion_alarm_at.get(port_key, 0)
        if now - last < 1:
            return
        self._last_congestion_alarm_at[port_key] = now
        for alarm in alarms:
            self._push_alarm(alarm)
