"""
带宽计算器服务
实现不同协议类型的带宽计算公式
"""


class BandwidthCalculator:
    """
    带宽计算器
    根据不同协议类型计算带宽利用率
    """

    @staticmethod
    def calculate_lan_bandwidth(frequency_ms: float, byte_count: int) -> float:
        """
        计算LAN带宽
        
        公式: (频率 × 字节数 / 1024 × 8) Mbps
        
        参数:
            frequency_ms: 发送频率（毫秒）
            byte_count: 字节数
            
        返回:
            带宽（Mbps）
            
        示例:
            频率是100ms，字节数是100字节
            带宽 = 100 / 1024 × 8 = 0.78 Mbps
            1分钟发10包，1分钟的带宽 = 7.8 Mbps
        """
        if frequency_ms <= 0 or byte_count <= 0:
            return 0.0
        
        # 计算每包数据的带宽（MB）
        bandwidth_mb = byte_count / 1024
        # 转换为Mbps（兆比特每秒）
        bandwidth_mbps = bandwidth_mb * 8
        
        return bandwidth_mbps

    @staticmethod
    def calculate_rs422_bandwidth(baud_rate: int) -> float:
        """
        计算RS422/RS485带宽
        
        公式: (波特率 / 10 / 1024) Mbps
        
        参数:
            baud_rate: 波特率（bps）
            
        返回:
            带宽（Mbps）
            
        示例:
            波特率 = 115200 bps
            带宽 = 115200 / 10 / 1024 ≈ 11.25 Mbps
        """
        if baud_rate <= 0:
            return 0.0
        
        bandwidth_mbps = baud_rate / 10 / 1024
        return bandwidth_mbps

    @staticmethod
    def calculate_can_bandwidth(baud_rate: int, frame_size: int = 8) -> float:
        """
        计算CAN带宽
        
        公式: (波特率 × 64 / 113 / 1024) Mbps（8字节标准帧）
        
        参数:
            baud_rate: 波特率（bps）
            frame_size: 帧大小（字节），默认8字节
            
        返回:
            带宽（Mbps）
            
        说明:
            在500 Kbps波特率下，传输8字节标准帧：
            理论最大有效数据速率 ≈ 500,000 * (64 / 113) ≈ 500,000 * 0.566 / 1024
            
            CAN帧结构开销：
            - 标准帧：1位起始位 + 11位标识符 + 6位控制 + 0-64位数据 + 
                     15位CRC + 2位ACK + 7位EOF = 总共约113位（对于8字节数据）
            - 有效数据位：64位（8字节）
            - 效率：64/113 ≈ 56.6%
        """
        if baud_rate <= 0:
            return 0.0
        
        # CAN帧效率约为56.6%（64位数据 / 113位总帧长）
        efficiency = 64 / 113
        bandwidth_mbps = baud_rate * efficiency / 1024
        
        return bandwidth_mbps

    @staticmethod
    def calculate_bandwidth_by_protocol(
        protocol_type: str,
        frequency_ms: float = None,
        byte_count: int = None,
        baud_rate: int = None
    ) -> float:
        """
        根据协议类型自动选择计算方法
        
        参数:
            protocol_type: 协议类型（LAN/RS422/RS485/CAN/1553B）
            frequency_ms: 发送频率（毫秒），用于LAN
            byte_count: 字节数，用于LAN
            baud_rate: 波特率，用于RS422/RS485/CAN
            
        返回:
            带宽（Mbps）
        """
        protocol_type = protocol_type.upper() if protocol_type else ''
        
        if protocol_type == 'LAN' or protocol_type == 'ETHERNET':
            if frequency_ms and byte_count:
                return BandwidthCalculator.calculate_lan_bandwidth(frequency_ms, byte_count)
        
        elif protocol_type in ['RS422', 'RS485']:
            if baud_rate:
                return BandwidthCalculator.calculate_rs422_bandwidth(baud_rate)
        
        elif protocol_type == 'CAN':
            if baud_rate:
                return BandwidthCalculator.calculate_can_bandwidth(baud_rate)
        
        elif protocol_type == '1553B':
            # 1553B协议的带宽计算可以后续扩展
            # 目前返回固定值或基于波特率计算
            if baud_rate:
                return baud_rate / 1024 / 1024  # 简化计算
        
        return 0.0

    @staticmethod
    def calculate_load_rate(actual_bandwidth: float, max_bandwidth: float) -> float:
        """
        计算负载率
        
        参数:
            actual_bandwidth: 实际带宽（Mbps）
            max_bandwidth: 最大可用带宽（Mbps）
            
        返回:
            负载率（0-1之间的浮点数）
        """
        if max_bandwidth <= 0:
            return 0.0
        
        load_rate = actual_bandwidth / max_bandwidth
        # 限制在0-1之间
        return min(max(load_rate, 0.0), 1.0)
