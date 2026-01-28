"""
协议解析服务
支持 1553B、CAN、RS485、LAN 协议的编解码
"""
from typing import Any, Dict, List, Optional, Tuple


class Protocol1553BParser:
    """MIL-STD-1553B 协议解析器"""

    @staticmethod
    def encode_command_word(
        rt_address: int, sub_address: int, tr_bit: bool, word_count: int
    ) -> int:
        """
        编码命令字（16位）

        格式: RT地址(5) + T/R(1) + 子地址(5) + 字计数(5)
        """
        rt_address = rt_address & 0x1F
        sub_address = sub_address & 0x1F
        word_count = word_count & 0x1F
        tr = 1 if tr_bit else 0

        return (rt_address << 11) | (tr << 10) | (sub_address << 5) | word_count

    @staticmethod
    def parse_command_word(word: int) -> Dict[str, Any]:
        """
        解析命令字

        返回:
            rt_address: RT地址 (0-31)
            sub_address: 子地址 (0-31)
            tr_bit: T/R位 (True=RT->BC, False=BC->RT)
            word_count: 字计数 (1-32, 0表示32)
        """
        rt_address = (word >> 11) & 0x1F
        tr_bit = bool((word >> 10) & 0x01)
        sub_address = (word >> 5) & 0x1F
        word_count = word & 0x1F
        if word_count == 0:
            word_count = 32

        return {
            "rt_address": rt_address,
            "sub_address": sub_address,
            "tr_bit": tr_bit,
            "word_count": word_count,
            "raw_word": word,
            "word_hex": f"{word:04X}",
        }

    @staticmethod
    def encode_status_word(
        rt_address: int,
        message_error: bool = False,
        instrumentation: bool = False,
        service_request: bool = False,
        broadcast_received: bool = False,
        busy: bool = False,
        subsystem_flag: bool = False,
        dynamic_bus_control: bool = False,
        terminal_flag: bool = False,
    ) -> int:
        """
        编码状态字（16位）

        格式: RT地址(5) + 消息错误(1) + 仪表(1) + 服务请求(1) +
              保留(3) + 广播接收(1) + 忙(1) + 子系统标志(1) +
              动态总线控制(1) + 终端标志(1)
        """
        word = (rt_address & 0x1F) << 11
        if message_error:
            word |= 1 << 10
        if instrumentation:
            word |= 1 << 9
        if service_request:
            word |= 1 << 8
        if broadcast_received:
            word |= 1 << 4
        if busy:
            word |= 1 << 3
        if subsystem_flag:
            word |= 1 << 2
        if dynamic_bus_control:
            word |= 1 << 1
        if terminal_flag:
            word |= 1

        return word

    @staticmethod
    def parse_status_word(word: int) -> Dict[str, Any]:
        """解析状态字"""
        return {
            "rt_address": (word >> 11) & 0x1F,
            "message_error": bool((word >> 10) & 0x01),
            "instrumentation": bool((word >> 9) & 0x01),
            "service_request": bool((word >> 8) & 0x01),
            "broadcast_received": bool((word >> 4) & 0x01),
            "busy": bool((word >> 3) & 0x01),
            "subsystem_flag": bool((word >> 2) & 0x01),
            "dynamic_bus_control": bool((word >> 1) & 0x01),
            "terminal_flag": bool(word & 0x01),
            "raw_word": word,
            "word_hex": f"{word:04X}",
        }

    @staticmethod
    def parse_frame(payload_hex: str, frame_type: str = "command_word") -> Dict[str, Any]:
        """解析1553B帧"""
        if not payload_hex:
            return {"error": "空数据"}

        word = int(payload_hex[:4], 16) if len(payload_hex) >= 4 else 0

        if frame_type == "command_word":
            return Protocol1553BParser.parse_command_word(word)
        elif frame_type == "status_word":
            return Protocol1553BParser.parse_status_word(word)
        else:
            return {"data_word": word, "word_hex": f"{word:04X}"}


class ProtocolCANParser:
    """CAN 协议解析器"""

    @staticmethod
    def encode_frame(
        can_id: int, data: bytes, is_extended: bool = False
    ) -> Tuple[bytes, int]:
        """
        编码 CAN 帧

        返回:
            帧字节序列, DLC
        """
        dlc = min(len(data), 8)
        data_padded = (data[:8] + b"\x00" * 8)[:8]

        # 简化编码：ID(4字节) + DLC(1字节) + DATA(8字节)
        if is_extended:
            id_bytes = can_id.to_bytes(4, "big")
        else:
            id_bytes = (can_id & 0x7FF).to_bytes(2, "big")

        frame = id_bytes + bytes([dlc]) + data_padded[:dlc]
        return frame, dlc

    @staticmethod
    def parse_frame(
        can_id: int, data_hex: str, dlc: int, is_extended: bool = False
    ) -> Dict[str, Any]:
        """
        解析 CAN 帧

        返回:
            帧ID、DLC、数据内容、CRC
        """
        data_bytes = bytes.fromhex(data_hex) if data_hex else b""

        # 计算 CRC（简化版 CRC-15）
        crc = 0
        for byte in data_bytes:
            crc ^= byte
            for _ in range(8):
                if crc & 0x4000:
                    crc = (crc << 1) ^ 0x4599
                else:
                    crc <<= 1
                crc &= 0x7FFF

        return {
            "can_id": can_id,
            "can_id_hex": f"{can_id:08X}" if is_extended else f"{can_id:03X}",
            "dlc": dlc,
            "data_hex": data_hex.upper() if data_hex else "",
            "data_bytes": list(data_bytes),
            "is_extended": is_extended,
            "crc": crc,
            "crc_hex": f"{crc:04X}",
        }

    @staticmethod
    def decode_standard_id(can_id: int) -> Dict[str, Any]:
        """解码标准帧ID（11位）"""
        return {
            "priority": (can_id >> 8) & 0x07,
            "data_page": (can_id >> 7) & 0x01,
            "pdu_format": (can_id >> 0) & 0x7F,
            "raw_id": can_id,
        }


class ProtocolRS485Parser:
    """RS422/RS485 协议解析器"""

    DEFAULT_HEADER = 0xAA55

    @staticmethod
    def encode_frame(data: bytes, header: int = 0xAA55) -> bytes:
        """
        编码 RS485 帧

        格式: 帧头(2字节) + 长度(1字节) + 数据(N字节) + 校验和(1字节)
        """
        data_len = len(data)
        checksum = sum(data) & 0xFF

        frame = (
            header.to_bytes(2, "big")
            + bytes([data_len])
            + data
            + bytes([checksum])
        )
        return frame

    @staticmethod
    def parse_frame(payload_hex: str) -> Dict[str, Any]:
        """
        解析 RS485 帧

        返回:
            帧头、数据长度、数据内容、校验和、校验结果
        """
        if not payload_hex or len(payload_hex) < 8:
            return {"error": "帧长度不足"}

        frame_bytes = bytes.fromhex(payload_hex)

        header = int.from_bytes(frame_bytes[:2], "big")
        data_len = frame_bytes[2]
        data = frame_bytes[3 : 3 + data_len]
        checksum = frame_bytes[3 + data_len] if len(frame_bytes) > 3 + data_len else 0

        # 验证校验和
        calculated_checksum = sum(data) & 0xFF
        checksum_valid = checksum == calculated_checksum

        return {
            "header": header,
            "header_hex": f"{header:04X}",
            "data_length": data_len,
            "data_hex": data.hex().upper(),
            "data_bytes": list(data),
            "checksum": checksum,
            "checksum_hex": f"{checksum:02X}",
            "checksum_valid": checksum_valid,
            "calculated_checksum": calculated_checksum,
        }

    @staticmethod
    def calculate_checksum(data: bytes) -> int:
        """计算校验和"""
        return sum(data) & 0xFF


class ProtocolLANParser:
    """LAN/以太网协议解析器"""

    @staticmethod
    def parse_mac_address(mac_hex: str) -> str:
        """格式化 MAC 地址"""
        mac_bytes = bytes.fromhex(mac_hex.replace(":", "").replace("-", ""))
        return ":".join(f"{b:02X}" for b in mac_bytes)

    @staticmethod
    def parse_ip_address(ip_int: int) -> str:
        """将整数IP转换为点分十进制"""
        return ".".join(str((ip_int >> (8 * i)) & 0xFF) for i in range(3, -1, -1))

    @staticmethod
    def encode_ethernet_frame(
        src_mac: str,
        dst_mac: str,
        ether_type: int,
        payload: bytes,
    ) -> bytes:
        """
        编码以太网帧

        格式: 目的MAC(6) + 源MAC(6) + 类型(2) + 负载(46-1500) + FCS(4)
        """
        dst_bytes = bytes.fromhex(dst_mac.replace(":", "").replace("-", ""))
        src_bytes = bytes.fromhex(src_mac.replace(":", "").replace("-", ""))
        type_bytes = ether_type.to_bytes(2, "big")

        # 填充到最小帧大小
        min_payload = 46
        if len(payload) < min_payload:
            payload = payload + b"\x00" * (min_payload - len(payload))

        frame = dst_bytes + src_bytes + type_bytes + payload

        # 计算 FCS（简化版 CRC32）
        fcs = ProtocolLANParser._calculate_crc32(frame)
        frame += fcs.to_bytes(4, "little")

        return frame

    @staticmethod
    def parse_ethernet_frame(payload_hex: str) -> Dict[str, Any]:
        """
        解析以太网帧

        返回:
            MAC地址、IP地址、端口号、负载数据
        """
        if not payload_hex or len(payload_hex) < 28:
            return {"error": "帧长度不足"}

        frame_bytes = bytes.fromhex(payload_hex)

        # 解析以太网头
        dst_mac = ":".join(f"{b:02X}" for b in frame_bytes[:6])
        src_mac = ":".join(f"{b:02X}" for b in frame_bytes[6:12])
        ether_type = int.from_bytes(frame_bytes[12:14], "big")

        result = {
            "dst_mac": dst_mac,
            "src_mac": src_mac,
            "ether_type": ether_type,
            "ether_type_hex": f"{ether_type:04X}",
        }

        # 如果是 IPv4 (0x0800)
        if ether_type == 0x0800 and len(frame_bytes) >= 34:
            ip_header = frame_bytes[14:]
            version = (ip_header[0] >> 4) & 0x0F
            header_len = (ip_header[0] & 0x0F) * 4
            total_len = int.from_bytes(ip_header[2:4], "big")
            protocol = ip_header[9]
            src_ip = ".".join(str(b) for b in ip_header[12:16])
            dst_ip = ".".join(str(b) for b in ip_header[16:20])

            result.update(
                {
                    "ip_version": version,
                    "ip_header_len": header_len,
                    "ip_total_len": total_len,
                    "ip_protocol": protocol,
                    "src_ip": src_ip,
                    "dst_ip": dst_ip,
                }
            )

            # 如果是 TCP (6) 或 UDP (17)
            if protocol in (6, 17) and len(ip_header) >= header_len + 4:
                transport_header = ip_header[header_len:]
                src_port = int.from_bytes(transport_header[:2], "big")
                dst_port = int.from_bytes(transport_header[2:4], "big")
                result.update(
                    {
                        "src_port": src_port,
                        "dst_port": dst_port,
                        "transport_protocol": "TCP" if protocol == 6 else "UDP",
                    }
                )

        # 负载数据
        payload_start = 14  # 以太网头之后
        if ether_type == 0x0800:
            payload_start += 20  # IP头
            if result.get("transport_protocol"):
                payload_start += 8 if result["transport_protocol"] == "UDP" else 20

        payload_data = frame_bytes[payload_start:-4] if len(frame_bytes) > payload_start + 4 else b""
        result["payload_hex"] = payload_data.hex().upper()
        result["payload_len"] = len(payload_data)

        return result

    @staticmethod
    def _calculate_crc32(data: bytes) -> int:
        """计算 CRC32"""
        crc = 0xFFFFFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xEDB88320
                else:
                    crc >>= 1
        return crc ^ 0xFFFFFFFF


class ProtocolParserFactory:
    """协议解析器工厂"""

    _parsers = {
        "1553B": Protocol1553BParser,
        "CAN": ProtocolCANParser,
        "RS485": ProtocolRS485Parser,
        "RS422": ProtocolRS485Parser,
        "LAN": ProtocolLANParser,
        "ETHERNET": ProtocolLANParser,
    }

    @classmethod
    def get_parser(cls, protocol_type: str):
        """获取协议解析器"""
        return cls._parsers.get(protocol_type.upper())

    @classmethod
    def parse(
        cls, protocol_type: str, payload_hex: str, **kwargs
    ) -> Dict[str, Any]:
        """通用解析接口"""
        parser = cls.get_parser(protocol_type)
        if not parser:
            return {"error": f"不支持的协议类型: {protocol_type}"}

        if protocol_type.upper() == "1553B":
            frame_type = kwargs.get("frame_type", "command_word")
            return parser.parse_frame(payload_hex, frame_type)
        elif protocol_type.upper() == "CAN":
            can_id = kwargs.get("can_id", 0)
            dlc = kwargs.get("dlc", 8)
            is_extended = kwargs.get("is_extended", False)
            return parser.parse_frame(can_id, payload_hex, dlc, is_extended)
        elif protocol_type.upper() in ("RS485", "RS422"):
            return parser.parse_frame(payload_hex)
        elif protocol_type.upper() in ("LAN", "ETHERNET"):
            return parser.parse_ethernet_frame(payload_hex)

        return {"error": "解析失败"}


class ProtocolParser(ProtocolParserFactory):
    """
    协议解析器统一入口（兼容旧导入）
    """







