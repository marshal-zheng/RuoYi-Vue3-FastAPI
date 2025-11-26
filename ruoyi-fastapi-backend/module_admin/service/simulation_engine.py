"""
仿真引擎核心
使用asyncio实现定时任务，模拟报文传输
"""
import asyncio
import uuid
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from module_admin.service.bandwidth_calculator import BandwidthCalculator
from module_admin.service.alarm_detector import AlarmDetector


class SimulationEngine:
    """
    仿真引擎
    负责管理仿真会话、生成报文、计算带宽
    """

    def __init__(self, session_id: str, topology_data: Dict[str, Any]):
        """
        初始化仿真引擎
        
        参数:
            session_id: 会话ID
            topology_data: 拓扑数据，包含nodes和edges
        """
        self.session_id = session_id
        self.topology_data = topology_data
        self.status = 'created'  # created/running/stopped
        self.start_timestamp = None
        self.current_timestamp = None
        
        # 仿真数据缓存
        self.messages = []  # 报文列表
        self.bandwidth_data = []  # 带宽数据列表
        self.alarms = []  # 告警列表
        
        # 定时任务
        self.tick_task = None
        self.tick_interval = 0.1  # 100ms tick
        
        # 解析拓扑数据
        self.nodes = {}  # {node_id: node_data}
        self.edges = []  # 边列表
        self.port_configs = {}  # {node_id:port_id: config}
        
        self._parse_topology()
        
        # 初始化告警检测
        self._detect_initial_alarms()

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

    def _detect_initial_alarms(self):
        """检测初始告警"""
        alarms = AlarmDetector.detect_all_alarms(self.topology_data)
        for alarm in alarms:
            alarm['session_id'] = self.session_id
            self.alarms.append(alarm)

    async def start(self):
        """启动仿真"""
        if self.status == 'running':
            return
        
        self.status = 'running'
        self.start_timestamp = time.time()
        self.current_timestamp = self.start_timestamp
        
        # 启动定时任务
        self.tick_task = asyncio.create_task(self._run_tick_loop())

    async def stop(self):
        """停止仿真"""
        if self.status != 'running':
            return
        
        self.status = 'stopped'
        
        # 停止定时任务
        if self.tick_task:
            self.tick_task.cancel()
            try:
                await self.tick_task
            except asyncio.CancelledError:
                pass

    async def _run_tick_loop(self):
        """运行定时任务循环"""
        try:
            while self.status == 'running':
                await self._tick()
                await asyncio.sleep(self.tick_interval)
        except asyncio.CancelledError:
            pass

    async def _tick(self):
        """处理一个时间片"""
        self.current_timestamp = time.time()
        elapsed = self.current_timestamp - self.start_timestamp
        
        # 生成报文
        messages = self._generate_messages(elapsed)
        self.messages.extend(messages)
        
        # 计算带宽
        bandwidth_data = self._calculate_bandwidth(elapsed)
        self.bandwidth_data.extend(bandwidth_data)

    def _generate_messages(self, elapsed_time: float) -> List[Dict[str, Any]]:
        """
        生成报文
        
        参数:
            elapsed_time: 已经过的时间（秒）
            
        返回:
            报文列表
        """
        messages = []
        
        for edge in self.edges:
            source_node = edge.get('source')
            source_port = edge.get('sourcePort')
            target_node = edge.get('target')
            target_port = edge.get('targetPort')
            
            if not all([source_node, source_port, target_node, target_port]):
                continue
            
            # 获取源端口配置
            source_key = f"{source_node}:{source_port}"
            port_config = self.port_configs.get(source_key)
            
            if not port_config:
                continue
            
            # 获取发送频率（毫秒）
            params = port_config.get('params', {})
            frequency_ms = params.get('frequency', 1000)  # 默认1秒
            
            # 判断是否应该发送报文
            # 简化逻辑：每个频率周期发送一次
            if elapsed_time > 0 and int(elapsed_time * 1000) % int(frequency_ms) < self.tick_interval * 1000:
                # 生成报文
                message = {
                    'message_id': str(uuid.uuid4()),
                    'session_id': self.session_id,
                    'sender_node_id': source_node,
                    'sender_port_id': source_port,
                    'receiver_node_id': target_node,
                    'receiver_port_id': target_port,
                    'protocol_type': port_config.get('protocol_type', 'LAN'),
                    'size_bytes': params.get('byte_count', 100),  # 默认100字节
                    'send_timestamp': self.current_timestamp,
                    'receive_timestamp': self.current_timestamp + 0.001,  # 假设1ms延迟
                    'create_time': datetime.now()
                }
                messages.append(message)
        
        return messages

    def _calculate_bandwidth(self, elapsed_time: float) -> List[Dict[str, Any]]:
        """
        计算带宽
        
        参数:
            elapsed_time: 已经过的时间（秒）
            
        返回:
            带宽数据列表
        """
        bandwidth_data = []
        
        # 统计每个端口的报文数量和大小
        port_stats = {}  # {node_id:port_id: {count, total_bytes}}
        
        # 只统计最近1秒内的报文
        recent_messages = [
            msg for msg in self.messages
            if self.current_timestamp - msg['send_timestamp'] <= 1.0
        ]
        
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
            
            protocol_type = port_config.get('protocol_type', 'LAN')
            params = port_config.get('params', {})
            
            # 根据协议类型计算带宽
            if protocol_type == 'LAN':
                frequency_ms = params.get('frequency', 1000)
                byte_count = params.get('byte_count', 100)
                bandwidth_mbps = BandwidthCalculator.calculate_lan_bandwidth(frequency_ms, byte_count)
            elif protocol_type in ['RS422', 'RS485']:
                baud_rate = params.get('baud_rate', 115200)
                bandwidth_mbps = BandwidthCalculator.calculate_rs422_bandwidth(baud_rate)
            elif protocol_type == 'CAN':
                baud_rate = params.get('baud_rate', 500000)
                bandwidth_mbps = BandwidthCalculator.calculate_can_bandwidth(baud_rate)
            else:
                bandwidth_mbps = 0.0
            
            bandwidth_data.append({
                'session_id': self.session_id,
                'node_id': node_id,
                'port_id': port_id,
                'timestamp': self.current_timestamp,
                'bandwidth_mbps': bandwidth_mbps,
                'message_count': stats['count'],
                'create_time': datetime.now()
            })
        
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
        """获取仿真状态"""
        return {
            'session_id': self.session_id,
            'status': self.status,
            'start_timestamp': self.start_timestamp,
            'current_timestamp': self.current_timestamp,
            'elapsed_time': self.current_timestamp - self.start_timestamp if self.start_timestamp else 0,
            'message_count': len(self.messages),
            'bandwidth_data_count': len(self.bandwidth_data),
            'alarm_count': len(self.alarms)
        }
