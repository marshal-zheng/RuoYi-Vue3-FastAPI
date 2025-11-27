"""
仿真引擎核心
使用asyncio实现定时任务，模拟报文传输
"""
import asyncio
import uuid
import time
import random
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
        
        # 增量数据追踪（用于WebSocket增量推送）
        self._last_pushed_msg_index = 0
        self._last_pushed_bw_index = 0
        self._last_pushed_alarm_index = 0
        
        # 数据清理配置
        self._max_messages = 1000  # 最多保留1000条报文
        self._max_bandwidth_points = 600  # 最多保留600个带宽点（10分钟，每秒1个）
        
        # 定时任务
        self.tick_task = None
        self.tick_interval = 0.5  # 500ms tick（降低频率，减少性能消耗）
        
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
        
        # 定期清理旧数据，防止内存泄漏
        self._cleanup_old_data()

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
            # 兼容两种字段格式：source/sourcePort 或 sourceId/sourcePortId
            source_node = edge.get('source') or edge.get('sourceId')
            source_port = edge.get('sourcePort') or edge.get('sourcePortId')
            target_node = edge.get('target') or edge.get('targetId')
            target_port = edge.get('targetPort') or edge.get('targetPortId')
            
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
        
        # 只统计最近1秒内的报文（用于滑动窗口带宽计算）
        recent_messages = [
            msg for msg in self.messages
            if self.current_timestamp - msg['send_timestamp'] <= 1.0
        ]
        # 窗口时长，避免除零并处理启动初期不足1秒的情况
        window_start = max(self.start_timestamp or self.current_timestamp, self.current_timestamp - 1.0)
        window_seconds = max(self.tick_interval, self.current_timestamp - window_start)
        
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
            
            # 使用实际统计的近1秒报文字节数计算即时带宽，并加入轻微抖动让曲线更贴近真实网络波动
            base_bandwidth = (stats['total_bytes'] * 8) / (1_000_000 * window_seconds)
            jitter = random.uniform(0.92, 1.08)
            bandwidth_mbps = base_bandwidth * jitter
            
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
