import bcrypt
from utils.log_util import logger

_BCRYPT_MAX_BYTES = 72


class PwdUtil:
    """
    密码工具类，基于bcrypt原生实现，避免passlib在Python3.13 + bcrypt 4.x上的72字节限制崩溃
    """

    @classmethod
    def verify_password(cls, plain_password, hashed_password):
        """
        工具方法：校验当前输入的密码与数据库存储的密码是否一致

        :param plain_password: 当前输入的密码
        :param hashed_password: 数据库存储的密码($2a$/$2b$格式)
        :return: 校验结果
        """
        if plain_password is None or hashed_password is None:
            return False
        normalized = cls.__normalize_password(plain_password)
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(normalized, hashed_bytes)

    @classmethod
    def get_password_hash(cls, input_password):
        """
        工具方法：对当前输入的密码进行加密

        :param input_password: 输入的密码
        :return: 加密成功的密码
        """
        if input_password is None:
            raise ValueError('密码不能为空')
        normalized = cls.__normalize_password(input_password)
        hashed = bcrypt.hashpw(normalized, bcrypt.gensalt())
        return hashed.decode('utf-8')

    @classmethod
    def sanitize_password(cls, password: str) -> str:
        """
        对外暴露的安全处理方法，确保任何进入bcrypt的明文密码都被安全截断
        """
        if password is None:
            return password
        truncated_bytes = cls.__truncate_bytes(password.encode('utf-8'))
        if len(truncated_bytes) < len(password.encode('utf-8')):
            logger.warning('密码长度超过bcrypt 72字节限制，系统将自动截断以兼容登录/加密流程')
        return truncated_bytes.decode('utf-8', errors='ignore')

    @classmethod
    def __normalize_password(cls, password: str) -> bytes:
        """
        返回裁剪后的字节序列，供bcrypt直接消费
        """
        if password is None:
            return b''
        encoded = password.encode('utf-8')
        return cls.__truncate_bytes(encoded)

    @staticmethod
    def __truncate_bytes(encoded: bytes) -> bytes:
        if encoded is None:
            return b''
        if len(encoded) <= _BCRYPT_MAX_BYTES:
            return encoded
        return encoded[:_BCRYPT_MAX_BYTES]
