from typing import Optional

from sqlalchemy import and_, or_

from config.env import SensitiveConfig
from utils.sensitive.cipher import SensitiveDataCipher
from utils.sensitive.registry import get_sensitive_hash_field


def sensitive_equals(model, field_name: str, value: Optional[str]):
    """
    Build a filter for sensitive fields. Prefer hash column if registered.

    Example:
        cond = sensitive_equals(SysUser, 'phonenumber', query.phonenumber)
    """
    if value is None or value == '':
        return None
    hash_field = get_sensitive_hash_field(field_name)
    if hash_field and hasattr(model, hash_field):
        hash_column = getattr(model, hash_field)
        hash_condition = hash_column == SensitiveDataCipher.hash(value)
        if getattr(SensitiveConfig, 'sensitive_data_deterministic', True):
            # Transitional fallback: use ciphertext match when hash is missing
            return or_(
                hash_condition,
                and_(
                    or_(hash_column.is_(None), hash_column == ''),
                    getattr(model, field_name) == value,
                ),
            )
        return hash_condition
    if not getattr(SensitiveConfig, 'sensitive_data_deterministic', True):
        raise ValueError(
            f'Sensitive field "{field_name}" requires a hash column when deterministic encryption is disabled'
        )
    return getattr(model, field_name) == value
