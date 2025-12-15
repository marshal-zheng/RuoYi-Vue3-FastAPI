"""
Word/Excel 文档导出工具
使用HTML转Word的方式生成Word文档，并支持导出附录Excel压缩包
"""
import base64
import io
import json
import re
import zipfile
from typing import Optional, List
from xml.etree import ElementTree as ET
from xml.dom import minidom

from openpyxl import Workbook
from openpyxl.cell.cell import MergedCell
try:
    from PIL import Image  # type: ignore
except Exception:  # Pillow 可能未安装，忽略
    Image = None
from openpyxl.styles import Alignment, Border, Font, Side

# 默认的接口控制文件模板
DEFAULT_ICD_TEMPLATE = """<h2 style="text-align: center;"><span style="font-family: 黑体;">接口控制文件示列</span></h2><p><br></p><h1><span style="font-family: 黑体;">1 范围</span></h1><p style="text-indent: 28pt;"><span style="font-family: 宋体;">……</span></p><h1><span style="font-family: 黑体;">2 引用文件</span></h1><p style="text-indent: 28pt;"><span style="font-family: 宋体;">……</span></p><h1><span style="font-family: 黑体;">3 术语定义</span></h1><p style="text-align: justify;"><span style="font-family: 宋体;">……</span></p><p style="text-align: justify;"><br></p><h1><span style="font-family: 黑体;">4 信息交联关系</span></h1><p style="text-align: justify;"><span style="font-size: 16px; font-family: 宋体;"> &nbsp; &nbsp; &nbsp; &nbsp;信息交联关系见</span><span style="font-size: 16px;">图1</span><span style="font-size: 16px; font-family: 宋体;">。</span></p><p style="text-align: justify;"><br></p><p style="text-align: center;"><span style="font-size: 16px; font-family: 宋体;">${image}</span></p><p style="text-align: center;"><span style="font-size: 16px; font-family: 宋体;">图 1 &nbsp;信息交换关系</span></p><p style="text-align: left;"><br></p><p style="text-align: left;"><span style="font-size: 16px; font-family: 宋体;"> &nbsp; &nbsp; &nbsp; &nbsp;</span></p><p><span style="font-size: 16px; font-family: 宋体;"> &nbsp; &nbsp;系统</span><span style="font-size: 16px;">各部件</span><span style="font-size: 16px; font-family: 宋体;">的</span><span style="font-size: 16px;">通信速率和通信周期</span><span style="font-size: 16px; font-family: 宋体;">见</span><span style="font-size: 16px;">表</span><span style="font-size: 16px; font-family: 宋体;">1所示</span><span style="font-size: 16px;">。</span></p><p><br></p><p style="text-align: center;"><span style="font-family: 宋体;">表</span>1<span style="font-family: 宋体;"> 部件通信速率及通信周期</span></p><p style="text-align: center;"><span style="font-family: 宋体;">${table}</span></p><p style="text-align: left;"><br></p><h1><span style="font-family: 黑体;">5 通信</span><span style="font-family: 宋体;">要求</span></h1><h2><span style="font-family: 黑体;"> &nbsp; &nbsp;5.1 主要</span><span style="font-family: Arial;">数据类型</span><span style="font-family: 黑体;">说明</span></h2><p> &nbsp; &nbsp; &nbsp;<span style="font-family: 宋体;">……</span></p><h2><span style="font-family: 黑体;"> &nbsp; 5.2 </span><span style="font-family: 宋体;">信息帧格式要求</span></h2><p> &nbsp; &nbsp; &nbsp;<span style="font-family: 宋体;">……</span></p><h2><span style="font-family: 黑体;"> &nbsp; 5.3 RS</span><span style="font-family: Arial;">422</span><span style="font-family: 黑体;">要求</span></h2><p> &nbsp; &nbsp; &nbsp;<span style="font-family: 宋体;">……</span></p><h2><span style="font-family: 黑体;"> &nbsp; 5.4 </span><span style="font-family: 宋体;">以太网要求</span></h2><p> &nbsp; &nbsp; &nbsp;<span style="font-family: 宋体;">……</span></p><h2><span style="font-family: 黑体;"> &nbsp; 5.5 </span><span style="font-family: 宋体;">帧类别与对应端口号</span></h2><p> &nbsp; &nbsp; &nbsp;<span style="font-family: 宋体;">……</span></p><h2><span style="font-family: 黑体;"> &nbsp; 5.6 节点号</span><span style="font-family: Arial;">定义</span></h2><p><span style="font-family: 宋体;"> &nbsp; &nbsp; &nbsp;……</span></p><h2><span style="font-family: 黑体;"> &nbsp; 5.7 异常情况处理</span></h2><p> &nbsp; &nbsp; <span style="font-family: 宋体;">……</span></p><p><br></p><p><br></p>${Appendix}<p><br></p>"""

# 附录序号映射 (0->A, 1->B, ...)
APPENDIX_LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

# 字典值到中文标签的兜底映射（用于旧数据缺少 label 的情况）
METHOD_LABEL_MAP = {
    # 以太网
    'udp_unicast': 'UDP单播',
    'udp_multicast': 'UDP组播',
    'udp_broadcast': 'UDP广播',
    'tcp': 'TCP',
    # RS422
    'asynchronous': '异步传输',
    'synchronous': '同步传输',
    # CAN
    'can_standard': 'CAN标准帧',
    'can_extended': 'CAN扩展帧',
    # 1553B
    'bc_to_rt': 'BC->RT',
    'rt_to_bc': 'RT->BC',
    'rt_to_rt': 'RT->RT',
}

ERROR_HANDLING_LABEL_MAP = {
    'none': '不判断',
    'timeout_retry': '超时重传',
    'crc_check': 'CRC校验',
    'parity_check': '奇偶校验',
    'timeout_retry_3_100ms': '超时重传 3 次, 100ms',
    'default': '默认处理',
}


def get_appendix_letter(index: int) -> str:
    """获取附录字母序号"""
    if index < 26:
        return APPENDIX_LETTERS[index]
    # 超过26个用 AA, AB 等
    first = index // 26 - 1
    second = index % 26
    return APPENDIX_LETTERS[first] + APPENDIX_LETTERS[second]


def _ensure_dict(data):
    if isinstance(data, dict):
        return data
    if isinstance(data, str):
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return {}
    return {}


def _ensure_list(data):
    if isinstance(data, list):
        return data
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
    return []


def generate_protocol_table_html(
    appendix_letter: str,
    table_index: int,
    sender: str,
    receiver: str,
    protocol_name: str,
    header: dict,
    fields: list,
    notes: str = ''
) -> str:
    """
    生成单个协议表格的HTML
    
    Args:
        appendix_letter: 附录字母 (A, B, C...)
        table_index: 表格序号 (1, 2, 3...)
        sender: 发送方设备名
        receiver: 接收方设备名
        protocol_name: 协议名称
        header: 协议头信息
        fields: 协议字段列表
    
    Returns:
        表格HTML字符串
    """
    header = _ensure_dict(header)
    fields = _ensure_list(fields)
    # 表格标题: 表 A.1 发送给部件X的XXX指令
    table_title = f"表 {appendix_letter}.{table_index} 发送给{receiver}的{protocol_name}"
    
    # 获取表头信息
    def pick_header_value(primary_key: str, *aliases: str) -> str:
        keys = (primary_key,) + aliases
        label_keys = []

        # 常见的 label 命名：xxxLabel / xxx_label
        def add_label_variants(key: str):
            if not key:
                return
            label_keys.append(f'{key}Label')
            label_keys.append(f'{key}_label')

        add_label_variants(primary_key)
        for alias in aliases:
            add_label_variants(alias)

        # 先看 label，再看实际值；允许 0
        for k in label_keys:
            if header.get(k) not in (None, ''):
                return str(header.get(k))
        for key in keys:
            if header.get(key) not in (None, ''):
                return str(header.get(key))
        return ''

    def pick_first_present(*values) -> str:
        for v in values:
            if v not in (None, ''):
                return str(v)
        return ''

    sender_text = header.get('sender') or sender or ''
    receiver_text = header.get('receiver') or receiver or ''
    frequency = pick_header_value('frequency')
    baud_rate = pick_header_value('baudRate', 'speed')
    method = pick_header_value('method')
    duration = pick_header_value('duration', 'sendDuration')
    port = pick_header_value('port', 'portNo', 'portNumber')
    frame_length = pick_header_value('frameLength')
    error_handling = pick_header_value('errorHandling', 'errorHandle')
    # 兜底：老数据没有 label 时，用内置映射将字典值转中文
    if method in METHOD_LABEL_MAP:
        method = METHOD_LABEL_MAP[method]
    if error_handling in ERROR_HANDLING_LABEL_MAP:
        error_handling = ERROR_HANDLING_LABEL_MAP[error_handling]
    protocol_type_text = pick_first_present(
        header.get('protocolLabel'),
        header.get('protocolTypeLabel'),
        header.get('protocolType'),
        header.get('busTypeLabel'),
        header.get('busType'),
        protocol_name,
    )

    # 发送时长/端口号列动态标题和值
    duration_or_port_label = '端口号' if port else '发送时长/ms'
    duration_or_port_value = port or duration
    type_cell_style = "writing-mode: vertical-rl; text-orientation: upright; text-align: center;"
    # 信息行数量（发送方、接收方、传输频率、传输方式、帧长度）
    type_rowspan = 5
    
    # 构建表格（头信息 + 字段信息）HTML，合并为一张表以保持连续边框
    table_html = f'''
<p style="text-align: center;"><span style="font-family: 宋体; font-weight: bold;">{table_title}</span></p>
<table border="1" cellspacing="0" cellpadding="4" style="width: 100%; border-collapse: collapse; font-family: 宋体; font-size: 10.5pt; border: 1pt solid #000;">
  <tr>
    <td style="width: 8%; {type_cell_style} border: 1pt solid #000; vertical-align: middle;" rowspan="{type_rowspan}">{protocol_type_text}</td>
    <td style="width: 15%; border: 1pt solid #000;" colspan="2">发送方</td>
    <td style="border: 1pt solid #000;" colspan="6">{sender_text}</td>
  </tr>
  <tr>
    <td style="border: 1pt solid #000;" colspan="2">接收方</td>
    <td style="border: 1pt solid #000;" colspan="6">{receiver_text}</td>
  </tr>
  <tr>
    <td style="border: 1pt solid #000;" colspan="2">传输频率</td>
    <td style="border: 1pt solid #000;" colspan="2">单次</td>
    <td style="border: 1pt solid #000;" colspan="2">传输速率/bps</td>
    <td style="border: 1pt solid #000;" colspan="2">{baud_rate}</td>
  </tr>
  <tr>
    <td style="border: 1pt solid #000;" colspan="2">传输方式</td>
    <td style="border: 1pt solid #000;" colspan="2">{method}</td>
    <td style="border: 1pt solid #000;" colspan="2">{duration_or_port_label}</td>
    <td style="border: 1pt solid #000;" colspan="2">{duration_or_port_value}</td>
  </tr>
  <tr>
    <td style="border: 1pt solid #000;" colspan="2">帧长度/Byte</td>
    <td style="border: 1pt solid #000;" colspan="2">{frame_length}</td>
    <td style="border: 1pt solid #000;" colspan="2">错误处理</td>
    <td style="border: 1pt solid #000;" colspan="2">{error_handling}</td>
  </tr>
  <tr>
    <td style="width: 5%; text-align: center; border: 1pt solid #000;">序号</td>
    <td style="width: 15%; text-align: center; border: 1pt solid #000;">信息名称</td>
    <td style="width: 8%; text-align: center; border: 1pt solid #000;">字节数</td>
    <td style="width: 10%; text-align: center; border: 1pt solid #000;">字节序号</td>
    <td style="width: 30%; text-align: center; border: 1pt solid #000;">值域及含义</td>
    <td style="width: 10%; text-align: center; border: 1pt solid #000;">量纲</td>
    <td style="width: 10%; text-align: center; border: 1pt solid #000;">数据类型</td>
    <td style="width: 10%; text-align: center; border: 1pt solid #000;">比例尺</td>
    <td style="width: 12%; text-align: center; border: 1pt solid #000;">备注</td>
  </tr>
'''
    
    # 添加字段行
    for idx, field in enumerate(fields, 1):
        name = field.get('name', '') or field.get('fieldName', '') or ''
        byte_count = field.get('byteCount', '') or ''
        byte_index = (
            field.get('byteSequence', '')
            or field.get('byteIndex', '')
            or field.get('byteNo', '')
            or ''
        )
        value_range = field.get('valueRange', '') or field.get('valueMeaning', '') or ''
        if isinstance(value_range, list):
            value_range_html = '<br>'.join(str(item) for item in value_range if item not in (None, ''))
        else:
            value_range_html = str(value_range).replace('\n', '<br>')
        unit = field.get('unitLabel', '') or field.get('unit', '') or field.get('dimension', '') or ''
        data_type = field.get('dataType', '') or ''
        scale = field.get('scale', '') or field.get('ratio', '') or ''
        remark = field.get('remark', '') or field.get('note', '') or ''

        table_html += f'''
  <tr>
    <td style="text-align: center; border: 1pt solid #000;">{idx}</td>
    <td style="border: 1pt solid #000;">{name}</td>
    <td style="text-align: center; border: 1pt solid #000;">{byte_count}</td>
    <td style="text-align: center; border: 1pt solid #000;">{byte_index}</td>
    <td style="border: 1pt solid #000;" colspan="2">{value_range_html if unit == '' else f'{value_range_html} ({unit})' if value_range_html else unit}</td>
    <td style="text-align: center; border: 1pt solid #000;">{data_type}</td>
    <td style="text-align: center; border: 1pt solid #000;">{scale}</td>
    <td style="border: 1pt solid #000;">{remark}</td>
  </tr>
'''
    
    # 添加附注行
    notes = header.get('notes', '') if isinstance(header, dict) else ''
    notes_html = notes.replace('\n', '<br>') if notes else ''
    table_html += f'''
  <tr>
    <td style="border: 1pt solid #000;">附注</td>
    <td style="border: 1pt solid #000;" colspan="8">{notes_html or '&nbsp;'}</td>
  </tr>
</table>
<p><br></p>
'''
    
    return table_html


def generate_appendix_html(appendix_letter: str, device_name: str, protocols: list) -> str:
    """
    生成单个设备的附录HTML
    
    Args:
        appendix_letter: 附录字母 (A, B, C...)
        device_name: 设备名称
        protocols: 该设备的协议列表
    
    Returns:
        附录HTML字符串
    """
    if not protocols:
        return ''
    
    # 附录标题
    appendix_html = f'''
<h2 style="text-align: center;"><span style="font-family: 黑体;">附 录 {appendix_letter}</span></h2>
<p style="text-align: center;"><span style="font-family: 黑体;">（规范性附录）</span></p>
<p style="text-align: center;"><span style="font-family: 黑体;">{device_name}发送的信息</span></p>
<p><br></p>
'''
    
    # 生成每个协议的表格
    for idx, protocol in enumerate(protocols, 1):
        sender = protocol.get('sender', device_name)
        receiver = protocol.get('receiver', '')
        protocol_name = (
            protocol.get('name')
            or protocol.get('protocolName')
            or protocol.get('interfaceName')
            or '协议'
        )
        header = protocol.get('header', {}) or {}
        fields = protocol.get('fields', []) or []
        notes = protocol.get('notes', '') or header.get('notes', '') or ''
        
        appendix_html += generate_protocol_table_html(
            appendix_letter,
            idx,
            sender,
            receiver,
            protocol_name,
            header,
            fields,
            notes
        )
    
    return appendix_html


def extract_protocols_from_topology(topology_data: dict) -> list:
    """
    从拓扑数据中提取所有设备及其协议
    
    Args:
        topology_data: 拓扑数据
    
    Returns:
        设备协议列表 [{'deviceName': '...', 'protocols': [...]}]
    """
    if not topology_data:
        return []

    def get_port_key_variants(port_id: str | int | None):
        """生成端口ID的多种变体，用于匹配不同存储格式"""
        if port_id is None:
            return []
        text = str(port_id)
        variants = [text]
        if text.startswith('port-'):
            variants.append(text.replace('port-', '', 1))
        return list(dict.fromkeys([v for v in variants if v]))

    def build_port_peer_map() -> dict:
        """
        构建端口->对端设备名列表的映射，优先使用 graph 中的边信息，
        其次使用拓扑摘要 edges。
        """
        port_peer = {}

        def register(port_id, peer_name):
            for key in get_port_key_variants(port_id):
                if not key:
                    continue
                if key not in port_peer:
                    port_peer[key] = []
                if peer_name and peer_name not in port_peer[key]:
                    port_peer[key].append(peer_name)

        # 从 graph cells 中解析
        graph_data = topology_data.get('graph', {}) or {}
        cells = graph_data.get('cells', []) or []
        node_name_by_id = {}

        for cell in cells:
            if isinstance(cell, dict) and cell.get('shape') != 'edge':
                data = cell.get('data') or {}
                node_name = data.get('name') or data.get('label') or data.get('deviceName') or ''
                if node_name and cell.get('id'):
                    node_name_by_id[str(cell.get('id'))] = node_name

        for cell in cells:
            if not isinstance(cell, dict) or cell.get('shape') != 'edge':
                continue
            source = cell.get('source') or {}
            target = cell.get('target') or {}
            s_cell, t_cell = source.get('cell'), target.get('cell')
            s_port, t_port = source.get('port'), target.get('port')
            s_name = node_name_by_id.get(str(s_cell), '')
            t_name = node_name_by_id.get(str(t_cell), '')
            if s_port and t_name:
                register(s_port, t_name)
            if t_port and s_name:
                register(t_port, s_name)

        # 兜底使用拓扑摘要 edges
        summary_edges = topology_data.get('edges', []) or []
        for edge in summary_edges:
            s_cell = edge.get('sourceId')
            t_cell = edge.get('targetId')
            s_port = edge.get('sourcePortId')
            t_port = edge.get('targetPortId')
            s_name = node_name_by_id.get(str(s_cell), '')
            t_name = node_name_by_id.get(str(t_cell), '')
            if s_port and t_name:
                register(s_port, t_name)
            if t_port and s_name:
                register(t_port, s_name)

        return port_peer

    port_peer_map = build_port_peer_map()

    def normalize_message_config(raw_config):
        """标准化协议信息，返回 {'header': {...}, 'fields': [...]}"""
        candidate = _ensure_dict(raw_config)
        if not candidate:
            return {}

        header = candidate.get('header')
        fields = candidate.get('fields')

        if header is None:
            # header 直接平铺在最外层的情况
            header_keys = {
                'sender',
                'receiver',
                'frequency',
                'frequencyLabel',
                'baudRate',
                'speed',
                'speedLabel',
                'method',
                'methodLabel',
                'duration',
                'sendDuration',
                'frameLength',
                'errorHandling',
                'errorHandle',
                'errorHandleLabel',
                'errorHandlingLabel',
            }
            header = {k: candidate.get(k) for k in header_keys if k in candidate}

        header = _ensure_dict(header)
        fields = _ensure_list(fields)

        # 若字段列表为空，但 candidate 本身是字段数组
        if not fields and isinstance(candidate, list):
            fields = candidate

        if header or fields:
            return {'header': header, 'fields': fields}
        return {}

    def collect_from_cells(cells: list) -> dict:
        """从节点列表中提取设备协议，返回 {deviceName: [protocols]}"""
        result = {}

        for cell in cells:
            if not isinstance(cell, dict):
                continue
            # 只处理包含节点数据的项
            cell_data = cell.get('data') if isinstance(cell, dict) else None
            if cell.get('shape') == 'edge' or not cell_data:
                continue

            data = cell_data or {}
            device_name = data.get('name') or data.get('label') or data.get('deviceName') or ''
            if not device_name:
                continue

            ports = data.get('ports', []) or []
            protocols = []

            for port in ports:
                port_keys = (
                    get_port_key_variants(port.get('id'))
                    + get_port_key_variants(port.get('interfaceId'))
                    + get_port_key_variants(port.get('portId'))
                )
                first_port_key = port_keys[0] if port_keys else None
                message_config = (
                    port.get('messageConfig')
                    or port.get('message')
                    or port.get('protocolConfig')
                    or port.get('protocol_config')
                    or port.get('message_config')
                    or {}
                )
                message_config = normalize_message_config(message_config)
                if not message_config:
                    continue

                header = message_config.get('header', {}) or {}
                fields = message_config.get('fields', []) or []

                # 只有有字段的协议才添加
                if fields:
                    # 保存协议/总线类型信息，便于导出展示
                    header.setdefault('busType', port.get('interfaceType') or port.get('busType') or '')
                    header.setdefault('protocolType', port.get('protocolType') or header.get('busType'))
                    header.setdefault('protocolLabel', port.get('interfaceName') or header.get('protocolType'))

                    protocol_name = (
                        port.get('protocolName')
                        or port.get('interfaceName')
                        or message_config.get('name')
                        or message_config.get('protocolName')
                        or '协议'
                    )
                    sender = header.get('sender') or device_name

                    # 获取所有可能的对端列表
                    peer_list = (
                        port.get('peerDeviceNames')
                        or port_peer_map.get(first_port_key)
                        or []
                    )
                    # 如果 header 中已有 receiver 则只使用这个
                    explicit_receiver = header.get('receiver')
                    if explicit_receiver:
                        peer_list = [explicit_receiver]
                    # 若无对端信息，则回退单个空元素，后续会被过滤
                    if not peer_list:
                        peer_list = ['']

                    for peer_receiver in peer_list:
                        receiver = peer_receiver or ''
                        # 将兜底结果写回 header 副本
                        header_copy = dict(header)
                        header_copy['sender'] = sender
                        header_copy['receiver'] = receiver

                        # 发送方或接收方缺失时跳过该协议
                        if not sender or not receiver:
                            continue

                        protocols.append({
                            'name': protocol_name,
                            'sender': sender,
                            'receiver': receiver,
                            'header': header_copy,
                            'fields': fields,
                        })

            if protocols:
                if device_name not in result:
                    result[device_name] = []
                result[device_name].extend(protocols)

        return result

    # 优先从图数据中提取
    graph_data = topology_data.get('graph', {}) or {}
    devices_map = collect_from_cells(graph_data.get('cells', []) or [])

    # 如果图数据中未能提取到协议，尝试使用节点摘要数据作为兜底
    if not devices_map:
        devices_map = collect_from_cells(topology_data.get('nodes', []) or [])

    return [
        {
            'deviceName': name,
            'protocols': protocols,
        }
        for name, protocols in devices_map.items()
        if protocols
    ]


def generate_all_appendices_html(topology_data: dict) -> str:
    """
    生成所有附录的HTML
    
    Args:
        topology_data: 拓扑数据
    
    Returns:
        所有附录的HTML字符串
    """
    devices = extract_protocols_from_topology(topology_data)
    
    if not devices:
        return '<h2 style="text-align: center;"><span style="font-family: 黑体;">附录</span></h2><p style="text-align: center;">暂无协议数据</p>'
    
    all_appendices_html = ''
    
    for idx, device in enumerate(devices):
        appendix_letter = get_appendix_letter(idx)
        device_name = device.get('deviceName', '')
        protocols = device.get('protocols', [])
        
        all_appendices_html += generate_appendix_html(appendix_letter, device_name, protocols)
    
    return all_appendices_html


def generate_word_document(
    content: str,
    orientation: str = 'portrait',
    page_size: str = 'A4'
) -> str:
    """
    生成Word文档的完整HTML结构
    """
    page_sizes = {
        'A4': {'width': 11906, 'height': 16838},
        'Letter': {'width': 12240, 'height': 15840},
    }
    
    size = page_sizes.get(page_size, page_sizes['A4'])
    page_width = size['height'] if orientation == 'landscape' else size['width']
    page_height = size['width'] if orientation == 'landscape' else size['height']
    
    return f'''<!DOCTYPE html>
<html xmlns:o="urn:schemas-microsoft-com:office:office"
      xmlns:w="urn:schemas-microsoft-com:office:word"
      xmlns="http://www.w3.org/TR/REC-html40">
<head>
  <meta charset="utf-8">
  <meta name="ProgId" content="Word.Document">
  <meta name="Generator" content="Microsoft Word 15">
  <meta name="Originator" content="Microsoft Word 15">
  <title>Document</title>
  <!--[if gte mso 9]>
  <xml>
    <w:WordDocument>
      <w:View>Print</w:View>
      <w:Zoom>100</w:Zoom>
      <w:DoNotOptimizeForBrowser/>
    </w:WordDocument>
  </xml>
  <![endif]-->
  <style>
    @page {{
      size: {page_width}twip {page_height}twip;
      margin: 2.54cm 3.18cm 2.54cm 3.18cm;
      mso-header-margin: 1.5cm;
      mso-footer-margin: 1.75cm;
      mso-paper-source: 0;
    }}
    
    body {{
      font-family: "宋体", SimSun, serif;
      font-size: 12pt;
      line-height: 1.5;
    }}
    
    h1 {{
      font-family: "黑体", SimHei, sans-serif;
      font-size: 16pt;
      font-weight: bold;
      margin-top: 12pt;
      margin-bottom: 6pt;
    }}
    
    h2 {{
      font-family: "黑体", SimHei, sans-serif;
      font-size: 14pt;
      font-weight: bold;
      margin-top: 12pt;
      margin-bottom: 6pt;
    }}
    
    p {{
      margin-top: 0;
      margin-bottom: 6pt;
    }}
    
    table {{
      border-collapse: collapse;
      width: 100%;
    }}
    
    td, th {{
      border: 1px solid black;
      padding: 5pt;
    }}
    
    img {{
      max-width: 100%;
    }}
  </style>
</head>
<body>
{content}
</body>
</html>'''


def replace_template_placeholders(template: str, data: dict) -> str:
    """替换模板中的占位符"""
    result = template
    for key, value in data.items():
        placeholder = re.compile(r'\$\{' + re.escape(key) + r'\}')
        result = placeholder.sub(str(value) if value else '', result)
    return result


def _safe_text(value) -> str:
    """将不同类型的值转换为可写入 XML 的字符串"""
    if value in (None, ''):
        return ''
    if isinstance(value, (list, dict)):
        try:
            return json.dumps(value, ensure_ascii=False)
        except TypeError:
            return str(value)
    return str(value)


def _format_xml_tag(key: str) -> str:
    """将任意 key 转换为 PascalCase 的 XML 标签"""
    if not key:
        return 'Value'
    token_pattern = re.compile(r'[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+')
    tokens = token_pattern.findall(key)
    if not tokens:
        cleaned = re.sub(r'[^0-9A-Za-z]+', ' ', key).strip()
        tokens = cleaned.split()
    if not tokens:
        tokens = [key]
    return ''.join(token.capitalize() for token in tokens)


def _append_child(parent: ET.Element, tag: str, value=None) -> ET.Element:
    child = ET.SubElement(parent, tag)
    text = _safe_text(value)
    if text:
        child.text = text
    return child


def _prettify_xml(element: ET.Element) -> bytes:
    rough = ET.tostring(element, encoding='utf-8')
    parsed = minidom.parseString(rough)
    return parsed.toprettyxml(indent='  ', encoding='utf-8')


def collect_summary_rows(topology_data: Optional[dict]) -> List[dict]:
    """
    提取通信概览数据，供多种导出格式复用
    """
    devices = extract_protocols_from_topology(topology_data or {}) if topology_data else []
    rows = []
    for device in devices:
        protocols = device.get('protocols') or []
        for proto in protocols:
            header = proto.get('header', {}) or {}
            sender = proto.get('sender') or header.get('sender') or ''
            receiver = proto.get('receiver') or header.get('receiver') or ''
            if not sender or not receiver:
                continue
            comm_type = (
                header.get('protocolLabel')
                or header.get('protocolTypeLabel')
                or header.get('protocolType')
                or header.get('busTypeLabel')
                or header.get('busType')
                or proto.get('name')
                or proto.get('protocolName')
                or ''
            )
            baud = header.get('baudRate') or header.get('speed') or ''
            method = header.get('methodLabel') or header.get('method') or ''
            if method in METHOD_LABEL_MAP:
                method = METHOD_LABEL_MAP[method]
            rows.append({
                'sender': sender,
                'receiver': receiver,
                'comm_type': comm_type,
                'baud': baud,
                'method': method,
                'remark': header.get('remark') or '',
            })
    return rows


def generate_summary_table_html(topology_data: Optional[dict]) -> str:
    """
    生成通信速率及通信周期表格HTML（替换模板中的 ${table}）
    列：序号、来源、目的、通信类型、波特率、传输类型、备注
    """
    rows = collect_summary_rows(topology_data)
    if not rows:
        return '<p style="text-align: center;">（暂无通信数据）</p>'

    # 构建HTML表格
    table_html = ['<table border="1" cellspacing="0" cellpadding="5" style="width:100%; border-collapse: collapse; font-family: 宋体; font-size: 10.5pt;">']
    table_html.append(
        '<tr style="background-color: #f5f5f5;">'
        '<td style="width:6%; text-align:center;">序号</td>'
        '<td style="width:16%; text-align:center;">来源</td>'
        '<td style="width:16%; text-align:center;">目的</td>'
        '<td style="width:16%; text-align:center;">通信类型</td>'
        '<td style="width:16%; text-align:center;">波特率（bps）</td>'
        '<td style="width:16%; text-align:center;">传输类型</td>'
        '<td style="width:14%; text-align:center;">备注</td>'
        '</tr>'
    )
    for idx, r in enumerate(rows, 1):
        bg = '#e8f4e8' if idx % 2 == 0 else ''
        table_html.append(
            f'<tr style="background-color:{bg};">'
            f'<td style="text-align:center;">{idx}</td>'
            f'<td style="text-align:center;">{r["sender"]}</td>'
            f'<td style="text-align:center;">{r["receiver"]}</td>'
            f'<td style="text-align:center;">{r["comm_type"]}</td>'
            f'<td style="text-align:center;">{r["baud"]}</td>'
            f'<td style="text-align:center;">{r["method"]}</td>'
            f'<td style="text-align:center;">{r["remark"]}</td>'
            '</tr>'
        )
    table_html.append('</table>')
    return ''.join(table_html)


def export_html_to_word(
    html_content: Optional[str] = None,
    template_data: Optional[dict] = None,
    orientation: str = 'portrait',
    page_size: str = 'A4'
) -> bytes:
    """将HTML内容导出为Word文档"""
    content = html_content or DEFAULT_ICD_TEMPLATE
    
    if template_data:
        content = replace_template_placeholders(content, template_data)
    
    word_document = generate_word_document(content, orientation, page_size)
    return word_document.encode('utf-8')


def generate_protocol_excel(protocol: dict, appendix_letter: str, table_index: int) -> bytes:
    """生成单个协议的 Excel 文件字节"""
    wb = Workbook()
    ws = wb.active
    ws.title = f"{appendix_letter}.{table_index}"

    header = protocol.get('header', {}) or {}
    sender = protocol.get('sender') or header.get('sender') or ''
    receiver = protocol.get('receiver') or header.get('receiver') or ''
    protocol_name = protocol.get('name') or protocol.get('protocolName') or ''

    def pick_header_value(primary_key: str, *aliases: str) -> str:
        keys = (primary_key,) + aliases
        label_keys = []
        for k in keys:
            label_keys.append(f'{k}Label')
            label_keys.append(f'{k}_label')
        for lk in label_keys:
            if header.get(lk) not in (None, ''):
                return str(header.get(lk))
        for key in keys:
            if header.get(key) not in (None, ''):
                return str(header.get(key))
        return ''

    frequency = pick_header_value('frequency')
    baud_rate = pick_header_value('baudRate', 'speed')
    method = pick_header_value('method')
    if method in METHOD_LABEL_MAP:
        method = METHOD_LABEL_MAP[method]
    duration = pick_header_value('duration', 'sendDuration')
    port = pick_header_value('port', 'portNo', 'portNumber')
    frame_length = pick_header_value('frameLength')
    error_handling = pick_header_value('errorHandling', 'errorHandle')
    if error_handling in ERROR_HANDLING_LABEL_MAP:
        error_handling = ERROR_HANDLING_LABEL_MAP[error_handling]
    protocol_type_text = (
        pick_header_value('protocolLabel', 'protocolTypeLabel')
        or pick_header_value('protocolType', 'busTypeLabel', 'busType')
        or protocol_name
    )

    duration_or_port_label = '端口号' if port else '发送时长/ms'
    duration_or_port_value = port or duration

    title = f"表 {appendix_letter}.{table_index} 发送给{receiver}的{protocol_name}"
    ws.append([title])
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=9)
    ws['A1'].font = Font(bold=True, size=12)
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')

    # 基础信息表，保持与 Word 风格一致：第一列为协议类型纵向合并，后续列按标签/值排列
    start_row = 2
    type_rowspan = 5
    # 在类型列放置文本
    ws.cell(row=start_row, column=1, value=protocol_type_text)
    ws.merge_cells(start_row=start_row, start_column=1, end_row=start_row + type_rowspan - 1, end_column=1)
    ws.cell(row=start_row, column=1).alignment = Alignment(text_rotation=90, horizontal='center', vertical='center')

    # 行2：发送方
    ws.append(['', '发送方', sender] + [''] * 6)
    ws.merge_cells(start_row=start_row, start_column=3, end_row=start_row, end_column=9)
    # 行3：接收方
    ws.append(['', '接收方', receiver] + [''] * 6)
    ws.merge_cells(start_row=start_row + 1, start_column=3, end_row=start_row + 1, end_column=9)
    # 行4：传输频率/速率
    ws.append(['', '传输频率', frequency, '传输速率/bps', baud_rate] + [''] * 4)
    # 行5：传输方式/端口或发送时长
    ws.append(['', '传输方式', method, duration_or_port_label, duration_or_port_value] + [''] * 4)
    # 行6：帧长度/错误处理
    ws.append(['', '帧长度/Byte', frame_length, '错误处理', error_handling] + [''] * 4)

    # 空行
    ws.append([])

    # 字段表头
    field_headers = ['序号', '信息名称', '字节数', '字节序号', '值域及含义', '量纲', '数据类型', '比例尺', '备注']
    ws.append(field_headers)

    fields = protocol.get('fields', []) or []
    for idx, field in enumerate(fields, 1):
        name = field.get('name', '') or field.get('fieldName', '') or ''
        byte_count = field.get('byteCount', '') or ''
        byte_index = (
            field.get('byteSequence', '')
            or field.get('byteIndex', '')
            or field.get('byteNo', '')
            or ''
        )
        value_range = field.get('valueRange', '') or field.get('valueMeaning', '') or ''
        if isinstance(value_range, list):
            value_range_text = '\n'.join(str(item) for item in value_range if item not in (None, ''))
        else:
            value_range_text = str(value_range)
        unit = field.get('unitLabel', '') or field.get('unit', '') or field.get('dimension', '') or ''
        data_type = field.get('dataType', '') or ''
        scale = field.get('scale', '') or field.get('ratio', '') or ''
        remark = field.get('remark', '') or field.get('note', '') or ''

        merged_value = value_range_text if unit == '' else f"{value_range_text} ({unit})" if value_range_text else unit

        ws.append([
            idx,
            name,
            byte_count,
            byte_index,
            merged_value,
            '',  # 将值域+量纲合并到同一个单元格（E:F）
            data_type,
            scale,
            remark,
        ])

        # 合并值域及含义与量纲的单元格，保持与 Word 一致
        current_row = ws.max_row
        ws.merge_cells(start_row=current_row, start_column=5, end_row=current_row, end_column=6)

    # 附注
    notes = header.get('notes', '') if isinstance(header, dict) else ''
    note_text = notes.replace('\n', '\n') if notes else ''
    ws.append(['附注', note_text] + [''] * 7)
    ws.merge_cells(start_row=ws.max_row, start_column=2, end_row=ws.max_row, end_column=9)

    # 样式：列宽、边框、对齐，尽量贴合 Word 模板
    column_widths = [6, 18, 10, 14, 30, 10, 12, 10, 15]
    for col_idx, width in enumerate(column_widths, 1):
        ws.column_dimensions[chr(64 + col_idx)].width = width

    thin = Border(
        left=Side(style='thin', color='000000'),
        right=Side(style='thin', color='000000'),
        top=Side(style='thin', color='000000'),
        bottom=Side(style='thin', color='000000'),
    )

    # 填充所有空白单元格并加边框
    for row_idx in range(1, ws.max_row + 1):
        for col_idx in range(1, 10):
            cell = ws.cell(row=row_idx, column=col_idx)
            if isinstance(cell, MergedCell):
                # 仅调整边框对齐，不修改值
                real_cell = ws._cells.get((row_idx, col_idx))
                target = real_cell if real_cell else cell
                target.border = thin
                target.alignment = Alignment(
                    wrap_text=True,
                    vertical='center',
                    horizontal='center' if row_idx in (1, start_row) else target.alignment.horizontal if target.alignment else None,
                )
                continue
            if cell.value is None:
                cell.value = ''
            cell.border = thin
            cell.alignment = Alignment(
                wrap_text=True,
                vertical='center',
                horizontal='center' if row_idx in (1, start_row) else cell.alignment.horizontal if cell.alignment else None,
            )

    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()


def export_version_to_excel(topology_data: Optional[dict] = None) -> bytes:
    """
    根据版本拓扑数据导出Excel压缩包（每个协议一张单独的 Excel）
    """
    devices = extract_protocols_from_topology(topology_data or {}) if topology_data else []
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        if not devices:
            # 仍返回合法 ZIP，方便解压工具识别
            zf.writestr('说明.txt', '暂无协议数据，未生成附录表。')
        else:
            for dev_idx, device in enumerate(devices):
                appendix_letter = get_appendix_letter(dev_idx)
                protocols = device.get('protocols', []) or []
                for idx, protocol in enumerate(protocols, 1):
                    excel_bytes = generate_protocol_excel(protocol, appendix_letter, idx)
                    proto_name = protocol.get('name') or f'协议{idx}'
                    safe_name = re.sub(r'[\\\\/:*?"<>|]+', '_', proto_name)
                    filename = f"附录{appendix_letter}-{idx}-{safe_name}.xlsx"
                    zf.writestr(filename, excel_bytes)

    zip_buffer.seek(0)
    data = zip_buffer.getvalue()

    # 兜底：若出现异常导致空内容或非 ZIP 头，返回仅含说明的合法 ZIP，避免解压失败
    if not data or not data.startswith(b'PK'):
        safe_buffer = io.BytesIO()
        with zipfile.ZipFile(safe_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('说明.txt', '附录表生成异常或无数据，请检查拓扑与协议信息后重试。')
        safe_buffer.seek(0)
        data = safe_buffer.getvalue()

    return data


def generate_image_html(image_base64: Optional[str] = None) -> str:
    """
    生成图片的HTML标签
    
    Args:
        image_base64: 图片的base64编码字符串（不含data:前缀）
    
    Returns:
        HTML img标签字符串，如果没有图片则返回占位文本
    """
    if not image_base64:
        return '（图片占位）'

    # 若图片为横向且安装了 Pillow，自动旋转 90 度以竖向适配
    def rotate_if_needed(b64: str) -> str:
        if not Image:
            return b64
        try:
            img_bytes = base64.b64decode(b64)
            with Image.open(io.BytesIO(img_bytes)) as im:
                width, height = im.size
                if width > height:
                    # 逆时针旋转 90 度
                    im = im.rotate(-90, expand=True)
                    buf = io.BytesIO()
                    im.save(buf, format='PNG')
                    return base64.b64encode(buf.getvalue()).decode('utf-8')
        except Exception:
            return b64
        return b64

    image_base64 = rotate_if_needed(image_base64)

    # 构建data URI
    data_uri = f'data:image/png;base64,{image_base64}'
    
    # 在 Word 中限制尺寸并保持等比缩放，旋转 90 度以适配竖向，避免跨页/超出可视区域
    wrapper_style = (
        'width:100%;'
        'display:flex;'
        'align-items:center;'
        'justify-content:center;'
        'margin:4pt auto;'
    )
    img_style = (
        'display:block;'
        'max-width:9cm;'
        'max-height:12cm;'
        'object-fit:contain;'
        'height:auto;'
        'border:1pt solid #e6e6e6;'
        'padding:4pt;'
        'box-sizing:border-box;'
        'background:#fafafa;'
        'transform:rotate(90deg);'
        'transform-origin:center center;'
    )
    return f'<div style="{wrapper_style}"><img src="{data_uri}" style="{img_style}" alt="信息交联关系图" /></div>'


def export_version_to_word(
    topology_data: Optional[dict] = None,
    image_base64: Optional[str] = None
) -> bytes:
    """
    根据版本拓扑数据导出Word文档
    """
    # 生成附录HTML
    appendix_html = generate_all_appendices_html(topology_data) if topology_data else ''
    
    # 通信概览表（替换 ${table}）
    summary_table_html = generate_summary_table_html(topology_data)
    
    # 生成图片HTML（替换 ${image}）
    image_html = generate_image_html(image_base64)

    template_data = {
        'image': image_html,
        'table': summary_table_html,
        'Appendix': appendix_html if appendix_html else '<h2 style="text-align: center;"><span style="font-family: 黑体;">附录</span></h2>',
    }
    
    return export_html_to_word(
        html_content=DEFAULT_ICD_TEMPLATE,
        template_data=template_data
    )


def export_version_to_xml(
    version_detail: Optional[dict] = None,
    topology_data: Optional[dict] = None
) -> bytes:
    """
    根据版本详情与拓扑数据导出 XML 接口控制文件
    """
    detail = version_detail or {}
    root = ET.Element('InterfaceControlDocument')

    version_info = ET.SubElement(root, 'VersionInfo')
    _append_child(version_info, 'VersionId', detail.get('version_id') or detail.get('versionId'))
    _append_child(version_info, 'ProjectId', detail.get('project_id') or detail.get('projectId'))
    _append_child(version_info, 'VersionNumber', detail.get('version_number') or detail.get('versionNumber'))
    _append_child(version_info, 'VersionName', detail.get('version_name') or detail.get('versionName'))
    _append_child(version_info, 'Description', detail.get('description'))
    _append_child(version_info, 'Creator', detail.get('create_by') or detail.get('createBy'))
    _append_child(version_info, 'CreateTime', detail.get('create_time') or detail.get('createTime'))
    _append_child(version_info, 'Updater', detail.get('update_by') or detail.get('updateBy'))
    _append_child(version_info, 'UpdateTime', detail.get('update_time') or detail.get('updateTime'))
    _append_child(version_info, 'IsLocked', detail.get('is_locked') or detail.get('isLocked'))
    _append_child(version_info, 'LockedBy', detail.get('locked_by') or detail.get('lockedBy'))
    _append_child(version_info, 'LockedTime', detail.get('locked_time') or detail.get('lockedTime'))

    summary_rows = collect_summary_rows(topology_data)
    summary_node = ET.SubElement(root, 'CommunicationSummary')
    if not summary_rows:
        summary_node.set('empty', 'true')
    else:
        for idx, row in enumerate(summary_rows, 1):
            link_el = ET.SubElement(summary_node, 'Link', index=str(idx))
            _append_child(link_el, 'Sender', row.get('sender'))
            _append_child(link_el, 'Receiver', row.get('receiver'))
            _append_child(link_el, 'CommunicationType', row.get('comm_type'))
            _append_child(link_el, 'BaudRate', row.get('baud'))
            _append_child(link_el, 'Method', row.get('method'))
            _append_child(link_el, 'Remark', row.get('remark'))

    devices_node = ET.SubElement(root, 'Devices')
    devices = extract_protocols_from_topology(topology_data or {}) if topology_data else []
    if not devices:
        devices_node.set('empty', 'true')
    else:
        for dev_index, device in enumerate(devices):
            appendix_letter = get_appendix_letter(dev_index)
            device_el = ET.SubElement(
                devices_node,
                'Device',
                appendix=appendix_letter,
                name=device.get('deviceName', '') or ''
            )
            protocols = device.get('protocols', []) or []
            if not protocols:
                device_el.set('empty', 'true')
                continue

            for proto_index, protocol in enumerate(protocols, 1):
                proto_el = ET.SubElement(
                    device_el,
                    'Protocol',
                    index=str(proto_index)
                )
                _append_child(proto_el, 'ProtocolName', protocol.get('name') or protocol.get('protocolName'))
                _append_child(proto_el, 'Sender', protocol.get('sender'))
                _append_child(proto_el, 'Receiver', protocol.get('receiver'))

                header_node = ET.SubElement(proto_el, 'Header')
                header = protocol.get('header', {}) or {}
                if not header:
                    header_node.set('empty', 'true')
                else:
                    for key, value in header.items():
                        _append_child(header_node, _format_xml_tag(key), value)

                fields_node = ET.SubElement(proto_el, 'Fields')
                fields = protocol.get('fields', []) or []
                if not fields:
                    fields_node.set('empty', 'true')
                else:
                    for field_index, field in enumerate(fields, 1):
                        field_el = ET.SubElement(fields_node, 'Field', index=str(field_index))
                        if isinstance(field, dict):
                            for f_key, f_val in field.items():
                                _append_child(field_el, _format_xml_tag(f_key), f_val)
                        else:
                            _append_child(field_el, 'Value', field)

    return _prettify_xml(root)
