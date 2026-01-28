"""
字段验证工具
提供常用的字段验证装饰器和验证函数
"""
import re
from typing import Any, Optional


class FieldValidators:
    """字段验证器集合"""
    
    @staticmethod
    def validate_not_empty(value: Any, field_name: str = "字段") -> Any:
        """验证非空"""
        if value is None:
            raise ValueError(f"{field_name}不能为空")
        if isinstance(value, str) and len(value.strip()) == 0:
            raise ValueError(f"{field_name}不能为空字符串")
        return value.strip() if isinstance(value, str) else value
    
    @staticmethod
    def validate_max_length(value: str, max_len: int, field_name: str = "字段") -> str:
        """验证最大长度"""
        if value and len(value) > max_len:
            raise ValueError(f"{field_name}长度不能超过{max_len}个字符")
        return value
    
    @staticmethod
    def validate_email(value: Optional[str], field_name: str = "邮箱") -> Optional[str]:
        """验证邮箱格式"""
        if not value:
            return value
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise ValueError(f"{field_name}格式不正确")
        return value
    
    @staticmethod
    def validate_phone(value: Optional[str], field_name: str = "手机号") -> Optional[str]:
        """验证手机号格式（中国大陆）"""
        if not value:
            return value
        phone_pattern = r'^1[3-9]\d{9}$'
        if not re.match(phone_pattern, value):
            raise ValueError(f"{field_name}格式不正确")
        return value
    
    @staticmethod
    def validate_positive_int(value: int, field_name: str = "字段") -> int:
        """验证正整数"""
        if value is not None and value <= 0:
            raise ValueError(f"{field_name}必须为正整数")
        return value
    
    @staticmethod
    def validate_non_negative_int(value: int, field_name: str = "字段") -> int:
        """验证非负整数"""
        if value is not None and value < 0:
            raise ValueError(f"{field_name}不能为负数")
        return value
    
    @staticmethod
    def validate_in_range(value: Any, min_val: Any, max_val: Any, field_name: str = "字段") -> Any:
        """验证值在指定范围内"""
        if value is not None and (value < min_val or value > max_val):
            raise ValueError(f"{field_name}必须在{min_val}到{max_val}之间")
        return value
    
    @staticmethod
    def validate_pattern(value: Optional[str], pattern: str, field_name: str = "字段") -> Optional[str]:
        """验证正则表达式匹配"""
        if value and not re.match(pattern, value):
            raise ValueError(f"{field_name}格式不正确")
        return value


class ValidatorMixin:
    """
    验证器 Mixin
    
    为模型提供常用的字段验证方法
    
    注意: SQLAlchemy 的 @validates 装饰器不支持通配符 '*'
    如需对所有字符串字段去除空格，请在具体模型中使用 __init__ 或 
    重写 __setattr__ 方法，或在具体字段上使用 @validates('field_name')
    
    使用示例:
        class MyModel(BaseModel, ValidatorMixin):
            name = Column(String(100))
            
            @validates('name')
            def validate_name(self, key, value):
                return FieldValidators.validate_not_empty(value, "名称")
    """
    pass


def create_name_validator(max_length: int = 100, field_name: str = "名称"):
    """
    创建名称验证器
    
    Args:
        max_length: 最大长度
        field_name: 字段显示名称
    
    Returns:
        验证函数
    """
    def validator(value: str) -> str:
        value = FieldValidators.validate_not_empty(value, field_name)
        value = FieldValidators.validate_max_length(value, max_length, field_name)
        return value
    return validator


def create_code_validator(max_length: int = 50, field_name: str = "编码"):
    """
    创建编码验证器（字母、数字、下划线、中划线）
    
    Args:
        max_length: 最大长度
        field_name: 字段显示名称
    
    Returns:
        验证函数
    """
    def validator(value: str) -> str:
        value = FieldValidators.validate_not_empty(value, field_name)
        value = FieldValidators.validate_max_length(value, max_length, field_name)
        pattern = r'^[a-zA-Z0-9_-]+$'
        value = FieldValidators.validate_pattern(value, pattern, field_name)
        return value
    return validator


# 示例：如何在模型中使用验证器
"""
from sqlalchemy.orm import validates
from module_admin.entity.do.validators import FieldValidators, ValidatorMixin

class Device(BaseModel, ValidatorMixin):
    device_name = Column(String(100), nullable=False)
    
    @validates('device_name')
    def validate_device_name(self, key, value):
        value = FieldValidators.validate_not_empty(value, "设备名称")
        value = FieldValidators.validate_max_length(value, 100, "设备名称")
        return value
"""
