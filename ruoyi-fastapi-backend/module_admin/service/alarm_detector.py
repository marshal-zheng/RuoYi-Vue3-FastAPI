"""
告警检测服务
检测拓扑配置中的问题并生成告警
"""
from typing import List, Dict, Any
from datetime import datetime
import uuid


class AlarmDetector:
    """
    告警检测器
    基于拓扑数据进行静态分析，检测配置问题
    """

    @staticmethod
    def detect_loopback(topology_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        检测回环连接
        
        回环：一个端口连接到同一设备的另一个端口
        
        参数:
            topology_data: 拓扑数据，包含nodes和edges
            
        返回:
            告警列表
        """
        alarms = []
        edges = topology_data.get('edges', [])
        
        for edge in edges:
            # 兼容两种字段格式
            source_node = edge.get('source') or edge.get('sourceId')
            target_node = edge.get('target') or edge.get('targetId')
            
            # 检查源节点和目标节点是否相同
            if source_node and target_node and source_node == target_node:
                alarm = {
                    'alarm_id': str(uuid.uuid4()),
                    'alarm_type': 'loopback',
                    'severity': 'warning',
                    'affected_nodes': [source_node],
                    'message': f'检测到回环连接：节点 {source_node} 连接到自身',
                    'timestamp': datetime.now().timestamp(),
                    'details': {
                        'edge_id': edge.get('id'),
                        'source_port': edge.get('sourcePort') or edge.get('sourcePortId'),
                        'target_port': edge.get('targetPort') or edge.get('targetPortId')
                    }
                }
                alarms.append(alarm)
        
        return alarms

    @staticmethod
    def detect_multi_connection(topology_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        检测多连接
        
        多连接：一个端口连接到多个其他端口
        
        参数:
            topology_data: 拓扑数据，包含nodes和edges
            
        返回:
            告警列表
        """
        alarms = []
        edges = topology_data.get('edges', [])
        
        # 统计每个端口的连接数
        port_connections = {}  # {node_id:port_id: [连接列表]}
        
        for edge in edges:
            # 兼容两种字段格式
            source_node = edge.get('source') or edge.get('sourceId')
            source_port = edge.get('sourcePort') or edge.get('sourcePortId')
            target_node = edge.get('target') or edge.get('targetId')
            target_port = edge.get('targetPort') or edge.get('targetPortId')
            
            if source_node and source_port:
                key = f"{source_node}:{source_port}"
                if key not in port_connections:
                    port_connections[key] = []
                port_connections[key].append({
                    'type': 'source',
                    'edge_id': edge.get('id'),
                    'connected_to': f"{target_node}:{target_port}"
                })
            
            if target_node and target_port:
                key = f"{target_node}:{target_port}"
                if key not in port_connections:
                    port_connections[key] = []
                port_connections[key].append({
                    'type': 'target',
                    'edge_id': edge.get('id'),
                    'connected_to': f"{source_node}:{source_port}"
                })
        
        # 检查是否有端口连接数大于1
        for port_key, connections in port_connections.items():
            if len(connections) > 1:
                node_id, port_id = port_key.split(':', 1)
                alarm = {
                    'alarm_id': str(uuid.uuid4()),
                    'alarm_type': 'multi_connection',
                    'severity': 'warning',
                    'affected_nodes': [node_id],
                    'message': f'检测到多连接：端口 {port_id} 连接到 {len(connections)} 个其他端口',
                    'timestamp': datetime.now().timestamp(),
                    'details': {
                        'port_id': port_id,
                        'connection_count': len(connections),
                        'connections': connections
                    }
                }
                alarms.append(alarm)
        
        return alarms

    @staticmethod
    def detect_all_alarms(topology_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        执行所有告警检测
        
        参数:
            topology_data: 拓扑数据
            
        返回:
            所有告警列表
        """
        all_alarms = []
        
        # 检测回环
        loopback_alarms = AlarmDetector.detect_loopback(topology_data)
        all_alarms.extend(loopback_alarms)
        
        # 检测多连接
        multi_conn_alarms = AlarmDetector.detect_multi_connection(topology_data)
        all_alarms.extend(multi_conn_alarms)
        
        return all_alarms

    @staticmethod
    def format_alarm_for_display(alarm: Dict[str, Any]) -> str:
        """
        格式化告警信息用于显示
        
        参数:
            alarm: 告警数据
            
        返回:
            格式化的告警消息
        """
        severity_icons = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'critical': '🔴'
        }
        
        severity = alarm.get('severity', 'info')
        icon = severity_icons.get(severity, '•')
        alarm_type = alarm.get('alarm_type', 'unknown')
        message = alarm.get('message', '')
        
        return f"{icon} [{alarm_type.upper()}] {message}"
