from typing import Dict, Optional


class IOToolkitException(Exception):
    """IO工具库基础异常"""

    def __init__(self, message: str, details: Optional[Dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class ExportException(IOToolkitException):
    """导出异常"""


class ImportException(IOToolkitException):
    """导入异常"""


class ImportValidationException(ImportException):
    """导入数据验证异常"""

    def __init__(self, message: str, errors: list):
        super().__init__(message, {'errors': errors})
        self.errors = errors


class VersionIncompatibleException(ImportException):
    """版本不兼容异常"""

    def __init__(self, current_version: str, supported_versions: list[str]):
        message = f'不支持的版本: {current_version}，支持的版本: {supported_versions}'
        super().__init__(message, {
            'current_version': current_version,
            'supported_versions': supported_versions,
        })
        self.current_version = current_version
        self.supported_versions = supported_versions


class FileFormatException(ImportException):
    """文件格式异常"""

    def __init__(self, expected_formats: list[str], actual_format: str):
        message = f'文件格式不正确: {actual_format}，期望格式: {expected_formats}'
        super().__init__(message, {
            'expected_formats': expected_formats,
            'actual_format': actual_format,
        })
        self.expected_formats = expected_formats
        self.actual_format = actual_format
