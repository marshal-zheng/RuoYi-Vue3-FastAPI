"""
告警检测服务
检测拓扑配置中的问题并生成告警
"""
from typing import List, Dict, Any, Optional
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

    # ==================== 运行期检测 ====================

    @staticmethod
    def check_load_status(load_percent: float) -> (str, List[Dict[str, Any]]):
        """
        根据负载率返回状态并生成必要的拥塞告警
        """
        alarms = []
        status = 'normal'

        if load_percent > 95:
            status = 'danger'
            alarms.append({
                'alarm_id': str(uuid.uuid4()),
                'alarm_type': 'congestion',
                'severity': 'error',
                'message': f'总线负载率 {load_percent:.1f}% 超过95%，存在拥塞风险',
                'timestamp': datetime.now().timestamp(),
            })
        elif load_percent > 80:
            status = 'warning'

        return status, alarms

    @staticmethod
    def detect_bandwidth_alarm(port_id: str, bandwidth_mbps: float, limit_mbps: float) -> List[Dict[str, Any]]:
        """
        检测带宽超限告警
        """
        alarms = []
        if limit_mbps <= 0:
            return alarms

        load_percent = (bandwidth_mbps / limit_mbps) * 100
        status, congestion_alarms = AlarmDetector.check_load_status(load_percent)
        alarms.extend(congestion_alarms)

        if load_percent > 100:
            alarms.append({
                'alarm_id': str(uuid.uuid4()),
                'alarm_type': 'bandwidth_exceed',
                'severity': 'warning' if status == 'warning' else 'error',
                'message': f'端口 {port_id} 带宽 {bandwidth_mbps:.2f}Mbps 超过物理上限 {limit_mbps:.2f}Mbps',
                'timestamp': datetime.now().timestamp(),
            })
        return alarms

    @staticmethod
    def detect_value_overflow(field_name: str, value: float, min_value: float, max_value: float) -> Optional[Dict[str, Any]]:
        """
        检测数值是否超范围
        """
        if value < min_value or value > max_value:
            return {
                'alarm_id': str(uuid.uuid4()),
                'alarm_type': 'value_overflow',
                'severity': 'warning',
                'message': f'{field_name} 当前值 {value} 超出范围 {min_value}-{max_value}',
                'timestamp': datetime.now().timestamp(),
                'details': {'field': field_name, 'value': value, 'range': [min_value, max_value]}
            }
        return None

    @staticmethod
    def detect_collision(
        device_ids: List[str],
        collision_time: float,
        bus_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        检测报文冲突告警

        参数:
            device_ids: 冲突的设备ID列表
            collision_time: 冲突发生时间
            bus_id: 总线标识

        返回:
            冲突告警
        """
        return {
            'alarm_id': str(uuid.uuid4()),
            'alarm_type': 'collision',
            'severity': 'error',
            'affected_nodes': device_ids,
            'message': f'检测到报文冲突：设备 {", ".join(device_ids)} 同时竞争总线',
            'timestamp': collision_time,
            'details': {
                'bus_id': bus_id,
                'collision_devices': device_ids,
                'collision_count': len(device_ids)
            }
        }

    @staticmethod
    def detect_packet_loss(
        port_id: str,
        sent_count: int,
        received_count: int,
        threshold: float = 0.01
    ) -> Optional[Dict[str, Any]]:
        """
        检测丢包告警

        参数:
            port_id: 端口标识
            sent_count: 发送报文数
            received_count: 接收确认数
            threshold: 丢包率阈值（默认1%）

        返回:
            丢包告警（如果超过阈值）
        """
        if sent_count <= 0:
            return None

        loss_count = sent_count - received_count
        loss_rate = loss_count / sent_count

        if loss_rate >= threshold:
            return {
                'alarm_id': str(uuid.uuid4()),
                'alarm_type': 'packet_loss',
                'severity': 'warning' if loss_rate < 0.05 else 'error',
                'message': f'端口 {port_id} 丢包率 {loss_rate*100:.2f}%（{loss_count}/{sent_count}）',
                'timestamp': datetime.now().timestamp(),
                'details': {
                    'port_id': port_id,
                    'sent_count': sent_count,
                    'received_count': received_count,
                    'loss_count': loss_count,
                    'loss_rate': loss_rate
                }
            }
        return None

    @staticmethod
    def detect_protocol_mismatch(
        source_protocol: str,
        target_protocol: str,
        edge_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        检测协议不兼容告警

        参数:
            source_protocol: 源端口协议类型
            target_protocol: 目标端口协议类型
            edge_id: 连接边标识

        返回:
            协议不兼容告警
        """
        if source_protocol != target_protocol:
            return {
                'alarm_id': str(uuid.uuid4()),
                'alarm_type': 'protocol_mismatch',
                'severity': 'error',
                'message': f'协议不兼容：{source_protocol} 无法连接 {target_protocol}',
                'timestamp': datetime.now().timestamp(),
                'details': {
                    'edge_id': edge_id,
                    'source_protocol': source_protocol,
                    'target_protocol': target_protocol
                }
            }
        return None

    @staticmethod
    def detect_unconfigured_port(
        node_id: str,
        port_id: str,
        port_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        检测未配置协议的端口

        参数:
            node_id: 节点标识
            port_id: 端口标识
            port_name: 端口名称

        返回:
            未配置告警
        """
        return {
            'alarm_id': str(uuid.uuid4()),
            'alarm_type': 'unconfigured_port',
            'severity': 'warning',
            'affected_nodes': [node_id],
            'message': f'端口 {port_name or port_id} 未配置协议',
            'timestamp': datetime.now().timestamp(),
            'details': {
                'node_id': node_id,
                'port_id': port_id,
                'port_name': port_name
            }
        }

    @staticmethod
    def validate_topology(topology_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        验证拓扑配置完整性

        检查:
        1. 至少两个设备节点
        2. 至少一条连接
        3. 未配置协议的端口
        4. 协议不兼容的连接

        返回:
            验证告警列表
        """
        alarms = []
        nodes = topology_data.get('nodes', [])
        edges = topology_data.get('edges', [])

        # 检查节点数量
        if len(nodes) < 2:
            alarms.append({
                'alarm_id': str(uuid.uuid4()),
                'alarm_type': 'insufficient_nodes',
                'severity': 'error',
                'message': f'拓扑中至少需要2个设备节点，当前只有 {len(nodes)} 个',
                'timestamp': datetime.now().timestamp(),
            })

        # 检查连接数量
        if len(edges) < 1:
            alarms.append({
                'alarm_id': str(uuid.uuid4()),
                'alarm_type': 'no_connection',
                'severity': 'error',
                'message': '拓扑中至少需要1条连接',
                'timestamp': datetime.now().timestamp(),
            })

        # 构建端口协议映射
        port_protocols = {}
        for node in nodes:
            node_id = node.get('id')
            node_data = node.get('data', {})
            ports = node_data.get('ports', [])

            for port in ports:
                port_id = port.get('id')
                protocol = port.get('type') or port.get('protocol_type')
                key = f"{node_id}:{port_id}"
                port_protocols[key] = protocol

                # 检查未配置协议的端口
                if not protocol:
                    alarms.append(AlarmDetector.detect_unconfigured_port(
                        node_id, port_id, port.get('name')
                    ))

        # 检查协议兼容性
        for edge in edges:
            source_key = f"{edge.get('source') or edge.get('sourceId')}:{edge.get('sourcePort') or edge.get('sourcePortId')}"
            target_key = f"{edge.get('target') or edge.get('targetId')}:{edge.get('targetPort') or edge.get('targetPortId')}"

            source_protocol = port_protocols.get(source_key)
            target_protocol = port_protocols.get(target_key)

            if source_protocol and target_protocol:
                mismatch_alarm = AlarmDetector.detect_protocol_mismatch(
                    source_protocol, target_protocol, edge.get('id')
                )
                if mismatch_alarm:
                    alarms.append(mismatch_alarm)

        return alarms

    @staticmethod
    def sort_alarms_by_severity(alarms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        按严重程度排序告警（error > warning > info）

        参数:
            alarms: 告警列表

        返回:
            排序后的告警列表
        """
        severity_order = {'error': 0, 'critical': 0, 'warning': 1, 'info': 2}
        return sorted(alarms, key=lambda a: severity_order.get(a.get('severity', 'info'), 3))

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
