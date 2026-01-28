"""
测试错误码体系
"""
import pytest
from config.error_codes import ErrorCode, ErrorType, ERROR_CODE_MAP, get_error_info


class TestErrorCode:
    """测试错误码枚举"""
    
    def test_error_code_values(self):
        """测试错误码值"""
        assert ErrorCode.VALIDATION_ERROR == 10001
        assert ErrorCode.UNAUTHORIZED == 20001
        assert ErrorCode.USER_NOT_FOUND == 30001
        assert ErrorCode.ROLE_NOT_FOUND == 40001
        assert ErrorCode.SYSTEM_ERROR == 50000
    
    def test_error_code_uniqueness(self):
        """测试错误码唯一性"""
        codes = [code.value for code in ErrorCode]
        assert len(codes) == len(set(codes)), "错误码存在重复"


class TestErrorCodeInfo:
    """测试错误码信息"""
    
    def test_validation_error_info(self):
        """测试校验错误信息"""
        info = ERROR_CODE_MAP[ErrorCode.VALIDATION_ERROR]
        assert info.code == 10001
        assert info.title == "参数校验失败"
        assert info.http_status == 422
        assert info.error_type == ErrorType.VALIDATION
    
    def test_user_already_exists_info(self):
        """测试用户已存在错误信息"""
        info = ERROR_CODE_MAP[ErrorCode.USER_ALREADY_EXISTS]
        assert info.code == 30002
        assert "用户名已被使用" in info.detail
        assert info.http_status == 409
        assert info.error_type == ErrorType.BUSINESS
    
    def test_system_error_info(self):
        """测试系统错误信息（用户消息通用化）"""
        info = ERROR_CODE_MAP[ErrorCode.SYSTEM_ERROR]
        assert info.code == 50000
        assert info.title == "系统繁忙，请稍后重试"
        assert info.http_status == 500
        assert info.error_type == ErrorType.SYSTEM
    
    def test_database_error_info(self):
        """测试数据库错误信息（用户消息通用化）"""
        info = ERROR_CODE_MAP[ErrorCode.DATABASE_ERROR]
        assert info.code == 50001
        assert info.title == "系统繁忙，请稍后重试"
        assert info.http_status == 500
        assert info.error_type == ErrorType.SYSTEM


class TestGetErrorInfo:
    """测试获取错误信息函数"""
    
    def test_get_existing_error_info(self):
        """测试获取已存在的错误信息"""
        info = get_error_info(ErrorCode.USER_NOT_FOUND)
        assert info.code == 30001
        assert "用户不存在" in info.title
    
    def test_get_nonexistent_error_info(self):
        """测试获取不存在的错误信息（返回默认系统错误）"""
        info = get_error_info(99999)
        assert info.code == 50000
        assert "系统繁忙" in info.title


class TestErrorCodeMapping:
    """测试错误码映射完整性"""
    
    def test_all_error_codes_have_mapping(self):
        """测试所有错误码都有映射"""
        for code in ErrorCode:
            assert code in ERROR_CODE_MAP, f"错误码 {code} 缺少映射"
    
    def test_http_status_codes_valid(self):
        """测试 HTTP 状态码有效性"""
        valid_statuses = {400, 401, 403, 404, 409, 422, 500}
        for info in ERROR_CODE_MAP.values():
            assert info.http_status in valid_statuses, \
                f"错误码 {info.code} 的 HTTP 状态码 {info.http_status} 无效"
    
    def test_system_errors_use_generic_messages(self):
        """测试系统错误使用通用消息"""
        system_error_codes = [
            ErrorCode.SYSTEM_ERROR,
            ErrorCode.DATABASE_ERROR,
            ErrorCode.EXTERNAL_SERVICE_ERROR,
            ErrorCode.CACHE_ERROR
        ]
        
        for code in system_error_codes:
            info = ERROR_CODE_MAP[code]
            # 系统错误的用户消息应该通用化
            assert "系统繁忙" in info.title or "请稍后重试" in info.title, \
                f"系统错误 {code} 的用户消息未通用化"
