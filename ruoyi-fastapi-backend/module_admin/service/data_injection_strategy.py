"""
数据注入策略模块
提供多种仿真通信数据注入/自动填充策略

策略类型:
1. random - 随机值生成
2. increment - 序列递增（计数器）
3. fixed - 固定模板
4. cycle - 循环模式（循环使用预设数据集）
5. sine_wave - 正弦波模式（模拟周期性数据变化）
"""
import struct
import math
import random
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod


class DataInjectionStrategy(ABC):
    """数据注入策略基类"""
    
    @abstractmethod
    def generate(self, field_config: Dict[str, Any], context: Dict[str, Any]) -> bytes:
        """
        生成字段数据
        
        参数:
            field_config: 字段配置（包含字段名、数据类型、字节数、值域等）
            context: 上下文信息（包含当前tick计数、时间戳等）
            
        返回:
            生成的字节数据
        """
        pass
    
    @staticmethod
    def get_strategy(strategy_type: str) -> 'DataInjectionStrategy':
        """获取策略实例"""
        strategies = {
            'random': RandomStrategy(),
            'increment': IncrementStrategy(),
            'fixed': FixedStrategy(),
            'cycle': CycleStrategy(),
            'sine_wave': SineWaveStrategy(),
        }
        return strategies.get(strategy_type, RandomStrategy())


class RandomStrategy(DataInjectionStrategy):
    """随机值生成策略"""
    
    def generate(self, field_config: Dict[str, Any], context: Dict[str, Any]) -> bytes:
        data_type = field_config.get('dataType', 'UINT8')
        byte_count = field_config.get('byteCount', 1)
        value_range = field_config.get('valueRange', '')
        
        # 解析值域范围
        min_val, max_val = self._parse_range(value_range, data_type)
        
        # 根据数据类型生成随机值
        value = self._generate_random_value(data_type, min_val, max_val)
        
        # 转换为字节
        return self._value_to_bytes(value, data_type, byte_count)
    
    def _parse_range(self, value_range: str, data_type: str) -> tuple:
        """解析值域范围"""
        type_defaults = {
            'UINT8': (0, 255),
            'UINT16': (0, 65535),
            'UINT32': (0, 4294967295),
            'INT8': (-128, 127),
            'INT16': (-32768, 32767),
            'INT32': (-2147483648, 2147483647),
            'FLOAT32': (-1000.0, 1000.0),
            'FLOAT64': (-1000.0, 1000.0),
        }
        
        if not value_range:
            return type_defaults.get(data_type, (0, 255))
        
        # 尝试解析 "min~max" 或 "min-max" 格式
        for sep in ['~', '-', '..']:
            if sep in value_range:
                parts = value_range.split(sep)
                if len(parts) == 2:
                    try:
                        return float(parts[0].strip()), float(parts[1].strip())
                    except ValueError:
                        pass
        
        # 尝试解析十六进制 "0xFFFF"
        if value_range.startswith('0x'):
            try:
                max_val = int(value_range, 16)
                return 0, max_val
            except ValueError:
                pass
        
        return type_defaults.get(data_type, (0, 255))
    
    def _generate_random_value(self, data_type: str, min_val: float, max_val: float):
        """生成随机值"""
        if data_type.startswith('FLOAT'):
            return random.uniform(min_val, max_val)
        return random.randint(int(min_val), int(max_val))
    
    def _value_to_bytes(self, value, data_type: str, byte_count: int) -> bytes:
        """将值转换为字节"""
        format_map = {
            'UINT8': 'B',
            'UINT16': 'H',
            'UINT32': 'I',
            'INT8': 'b',
            'INT16': 'h',
            'INT32': 'i',
            'FLOAT32': 'f',
            'FLOAT64': 'd',
        }
        
        fmt = format_map.get(data_type, 'B')
        try:
            return struct.pack('>' + fmt, value)  # 大端序
        except struct.error:
            # 如果打包失败，返回指定长度的零字节
            return bytes(byte_count)


class IncrementStrategy(DataInjectionStrategy):
    """序列递增策略（计数器模式）"""
    
    # 类级别的计数器存储
    _counters: Dict[str, int] = {}
    
    def generate(self, field_config: Dict[str, Any], context: Dict[str, Any]) -> bytes:
        field_name = field_config.get('fieldName', 'default')
        data_type = field_config.get('dataType', 'UINT16')
        byte_count = field_config.get('byteCount', 2)
        
        # 从配置中获取起始值和步长
        start_value = field_config.get('startValue', 0)
        step = field_config.get('step', 1)
        
        # 获取值域范围用于循环
        value_range = field_config.get('valueRange', '')
        _, max_val = self._parse_range(value_range, data_type)
        
        # 生成唯一键
        session_id = context.get('session_id', 'default')
        counter_key = f"{session_id}:{field_name}"
        
        # 获取或初始化计数器
        if counter_key not in self._counters:
            self._counters[counter_key] = start_value
        
        current_value = self._counters[counter_key]
        
        # 更新计数器（循环）
        next_value = current_value + step
        if next_value > max_val:
            next_value = start_value
        self._counters[counter_key] = next_value
        
        # 转换为字节
        return self._value_to_bytes(current_value, data_type, byte_count)
    
    def _parse_range(self, value_range: str, data_type: str) -> tuple:
        """解析值域范围"""
        type_defaults = {
            'UINT8': (0, 255),
            'UINT16': (0, 65535),
            'UINT32': (0, 4294967295),
            'INT8': (-128, 127),
            'INT16': (-32768, 32767),
            'INT32': (-2147483648, 2147483647),
        }
        
        if not value_range:
            return type_defaults.get(data_type, (0, 65535))
        
        for sep in ['~', '-', '..']:
            if sep in value_range:
                parts = value_range.split(sep)
                if len(parts) == 2:
                    try:
                        return int(parts[0].strip()), int(parts[1].strip())
                    except ValueError:
                        pass
        
        return type_defaults.get(data_type, (0, 65535))
    
    def _value_to_bytes(self, value: int, data_type: str, byte_count: int) -> bytes:
        """将值转换为字节"""
        format_map = {
            'UINT8': 'B',
            'UINT16': 'H',
            'UINT32': 'I',
            'INT8': 'b',
            'INT16': 'h',
            'INT32': 'i',
        }
        
        fmt = format_map.get(data_type, 'H')
        try:
            return struct.pack('>' + fmt, int(value))
        except struct.error:
            return bytes(byte_count)
    
    @classmethod
    def reset_counters(cls, session_id: str = None):
        """重置计数器"""
        if session_id:
            keys_to_remove = [k for k in cls._counters if k.startswith(f"{session_id}:")]
            for key in keys_to_remove:
                del cls._counters[key]
        else:
            cls._counters.clear()


class FixedStrategy(DataInjectionStrategy):
    """固定模板策略"""
    
    def generate(self, field_config: Dict[str, Any], context: Dict[str, Any]) -> bytes:
        data_type = field_config.get('dataType', 'UINT8')
        byte_count = field_config.get('byteCount', 1)
        
        # 从配置中获取固定值
        fixed_value = field_config.get('fixedValue')
        
        if fixed_value is None:
            # 使用默认值
            default_values = {
                'UINT8': 0,
                'UINT16': 0,
                'UINT32': 0,
                'INT8': 0,
                'INT16': 0,
                'INT32': 0,
                'FLOAT32': 0.0,
                'FLOAT64': 0.0,
            }
            fixed_value = default_values.get(data_type, 0)
        
        # 处理十六进制字符串
        if isinstance(fixed_value, str):
            if fixed_value.startswith('0x'):
                try:
                    fixed_value = int(fixed_value, 16)
                except ValueError:
                    fixed_value = 0
            else:
                try:
                    fixed_value = float(fixed_value) if '.' in fixed_value else int(fixed_value)
                except ValueError:
                    fixed_value = 0
        
        return self._value_to_bytes(fixed_value, data_type, byte_count)
    
    def _value_to_bytes(self, value, data_type: str, byte_count: int) -> bytes:
        """将值转换为字节"""
        format_map = {
            'UINT8': 'B',
            'UINT16': 'H',
            'UINT32': 'I',
            'INT8': 'b',
            'INT16': 'h',
            'INT32': 'i',
            'FLOAT32': 'f',
            'FLOAT64': 'd',
        }
        
        fmt = format_map.get(data_type, 'B')
        try:
            return struct.pack('>' + fmt, value)
        except struct.error:
            return bytes(byte_count)


class CycleStrategy(DataInjectionStrategy):
    """循环模式策略（循环使用预设数据集）"""
    
    # 类级别的索引存储
    _indices: Dict[str, int] = {}
    
    def generate(self, field_config: Dict[str, Any], context: Dict[str, Any]) -> bytes:
        field_name = field_config.get('fieldName', 'default')
        data_type = field_config.get('dataType', 'UINT8')
        byte_count = field_config.get('byteCount', 1)
        
        # 从配置中获取预设数据集
        preset_values = field_config.get('presetValues', [0, 1, 2, 3, 4, 5])
        
        if not preset_values:
            preset_values = [0]
        
        # 生成唯一键
        session_id = context.get('session_id', 'default')
        index_key = f"{session_id}:{field_name}"
        
        # 获取当前索引
        if index_key not in self._indices:
            self._indices[index_key] = 0
        
        current_index = self._indices[index_key]
        value = preset_values[current_index % len(preset_values)]
        
        # 更新索引
        self._indices[index_key] = (current_index + 1) % len(preset_values)
        
        return self._value_to_bytes(value, data_type, byte_count)
    
    def _value_to_bytes(self, value, data_type: str, byte_count: int) -> bytes:
        """将值转换为字节"""
        format_map = {
            'UINT8': 'B',
            'UINT16': 'H',
            'UINT32': 'I',
            'INT8': 'b',
            'INT16': 'h',
            'INT32': 'i',
            'FLOAT32': 'f',
            'FLOAT64': 'd',
        }
        
        fmt = format_map.get(data_type, 'B')
        try:
            return struct.pack('>' + fmt, value)
        except struct.error:
            return bytes(byte_count)
    
    @classmethod
    def reset_indices(cls, session_id: str = None):
        """重置索引"""
        if session_id:
            keys_to_remove = [k for k in cls._indices if k.startswith(f"{session_id}:")]
            for key in keys_to_remove:
                del cls._indices[key]
        else:
            cls._indices.clear()


class SineWaveStrategy(DataInjectionStrategy):
    """正弦波模式策略（模拟周期性数据变化）"""
    
    def generate(self, field_config: Dict[str, Any], context: Dict[str, Any]) -> bytes:
        data_type = field_config.get('dataType', 'FLOAT32')
        byte_count = field_config.get('byteCount', 4)
        
        # 从配置中获取正弦波参数
        amplitude = field_config.get('amplitude', 100.0)  # 振幅
        offset = field_config.get('offset', 0.0)  # 偏移
        frequency = field_config.get('frequency', 1.0)  # 频率 (Hz)
        phase = field_config.get('phase', 0.0)  # 初相位
        
        # 从上下文获取时间
        elapsed_time = context.get('elapsed_time', 0.0)
        
        # 计算正弦波值
        value = offset + amplitude * math.sin(2 * math.pi * frequency * elapsed_time + phase)
        
        # 如果是整数类型，需要四舍五入
        if data_type.startswith(('UINT', 'INT')):
            value = int(round(value))
        
        return self._value_to_bytes(value, data_type, byte_count)
    
    def _value_to_bytes(self, value, data_type: str, byte_count: int) -> bytes:
        """将值转换为字节"""
        format_map = {
            'UINT8': 'B',
            'UINT16': 'H',
            'UINT32': 'I',
            'INT8': 'b',
            'INT16': 'h',
            'INT32': 'i',
            'FLOAT32': 'f',
            'FLOAT64': 'd',
        }
        
        fmt = format_map.get(data_type, 'f')
        try:
            # 确保整数类型的值在有效范围内
            if data_type == 'UINT8':
                value = max(0, min(255, int(value)))
            elif data_type == 'UINT16':
                value = max(0, min(65535, int(value)))
            elif data_type == 'UINT32':
                value = max(0, min(4294967295, int(value)))
            elif data_type == 'INT8':
                value = max(-128, min(127, int(value)))
            elif data_type == 'INT16':
                value = max(-32768, min(32767, int(value)))
            elif data_type == 'INT32':
                value = max(-2147483648, min(2147483647, int(value)))
            
            return struct.pack('>' + fmt, value)
        except struct.error:
            return bytes(byte_count)


class PayloadGenerator:
    """报文内容生成器"""
    
    def __init__(self, default_strategy: str = 'random'):
        self.default_strategy = default_strategy
    
    def generate_payload(self, message_config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据消息配置生成完整的报文内容
        
        参数:
            message_config: 消息配置，包含header和fields
            context: 上下文信息
            
        返回:
            包含payload和payload_hex的字典
        """
        fields = message_config.get('fields', [])
        
        if not fields:
            # 没有字段定义，返回默认随机数据
            size = message_config.get('header', {}).get('frameLength', 64)
            payload = bytes([random.randint(0, 255) for _ in range(size)])
            return {
                'payload': payload,
                'payload_hex': payload.hex(),
                'field_values': {}
            }
        
        payload = bytearray()
        field_values = {}
        
        for field in fields:
            # 获取字段的填充策略
            strategy_type = field.get('fillStrategy', self.default_strategy)
            strategy = DataInjectionStrategy.get_strategy(strategy_type)
            
            # 生成字段数据
            field_data = strategy.generate(field, context)
            payload.extend(field_data)
            
            # 记录字段值（用于调试和显示）
            field_name = field.get('fieldName', 'unknown')
            field_values[field_name] = field_data.hex()
        
        return {
            'payload': bytes(payload),
            'payload_hex': bytes(payload).hex(),
            'field_values': field_values
        }


# 预定义的填充策略描述（供前端显示使用）
STRATEGY_DEFINITIONS = {
    'random': {
        'name': '随机值',
        'description': '在指定值域范围内随机生成数据',
        'icon': 'Dice',
        'params': ['valueRange']
    },
    'increment': {
        'name': '序列递增',
        'description': '计数器模式，数值按步长递增，到达上限后循环',
        'icon': 'TrendCharts',
        'params': ['startValue', 'step', 'valueRange']
    },
    'fixed': {
        'name': '固定值',
        'description': '使用预设的固定值填充',
        'icon': 'Lock',
        'params': ['fixedValue']
    },
    'cycle': {
        'name': '循环模式',
        'description': '按顺序循环使用预设数据集中的值',
        'icon': 'Refresh',
        'params': ['presetValues']
    },
    'sine_wave': {
        'name': '正弦波',
        'description': '模拟周期性数据变化，适合传感器数据仿真',
        'icon': 'DataLine',
        'params': ['amplitude', 'offset', 'frequency', 'phase']
    }
}
