from typing import Optional, Tuple

from sqlalchemy import Column, event
from sqlalchemy.orm import Mapper
from sqlalchemy.types import String, TypeDecorator

from utils.log_util import logger
from utils.sensitive.cipher import SensitiveDataCipher
from utils.sensitive.registry import register_sensitive_field


class EncryptedString(TypeDecorator):
    """SQLAlchemy type that transparently encrypts/decrypts strings."""

    impl = String
    cache_ok = True

    def __init__(self, length=None, *args, **kwargs):
        super().__init__(length=length, *args, **kwargs)

    def process_bind_param(self, value, dialect):
        return SensitiveDataCipher.encrypt(value)

    def process_result_value(self, value, dialect):
        return SensitiveDataCipher.decrypt(value)

    def coerce_compared_value(self, op, value):
        return self


def sensitive_string(length: int = 255, hash_field: Optional[str] = None, **kwargs):
    """
    Factory for encrypted string columns.

    Example:
        phone = sensitive_string(default=None, comment='联系电话')
    """
    column = Column(EncryptedString(length), **kwargs)
    if hash_field:
        column.info['sensitive_hash'] = hash_field
    return column


def sensitive_string_with_hash(
    name: str,
    length: int = 255,
    hash_length: int = 64,
    hash_index: bool = True,
    **kwargs,
) -> Tuple[Column, Column]:
    """
    Factory for encrypted string column + hash column.

    Example:
        phone, phone_hash = sensitive_string_with_hash('phone', comment='联系电话')
    """
    hash_field = f'{name}_hash'
    comment = kwargs.get('comment')
    default = kwargs.get('default', None)
    nullable = kwargs.get('nullable', True)

    enc_col = sensitive_string(length=length, hash_field=hash_field, **kwargs)
    hash_comment = f'{comment} Hash' if comment else 'Sensitive hash'
    hash_col = Column(
        String(hash_length),
        index=hash_index,
        default=default,
        nullable=nullable,
        comment=hash_comment,
    )
    return enc_col, hash_col


@event.listens_for(Mapper, 'mapper_configured')
def _register_sensitive_columns(mapper, cls):
    for column in mapper.columns:
        if isinstance(column.type, EncryptedString):
            register_sensitive_field(column.key, column.info.get('sensitive_hash'))


@event.listens_for(Mapper, 'before_insert')
@event.listens_for(Mapper, 'before_update')
def _populate_sensitive_hash(mapper, connection, target):
    for column in mapper.columns:
        if not isinstance(column.type, EncryptedString):
            continue
        hash_field = column.info.get('sensitive_hash')
        if not hash_field:
            continue
        if not hasattr(target, hash_field):
            logger.warning(
                f'Sensitive hash field {hash_field} not found on {type(target).__name__}'
            )
            continue
        value = getattr(target, column.key, None)
        if value is None or value == '':
            setattr(target, hash_field, value or '')
        else:
            setattr(target, hash_field, SensitiveDataCipher.hash(value))
