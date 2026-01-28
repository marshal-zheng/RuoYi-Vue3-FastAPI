from typing import Dict, Optional, Set


def _parse_config_set(value: str) -> Set[str]:
    return {item.strip().lower() for item in value.split(',') if item.strip()} if value else set()


_SENSITIVE_FIELDS: Set[str] = set()
_SENSITIVE_HASH_FIELDS: Dict[str, str] = {}


def register_sensitive_field(name: str, hash_field: Optional[str] = None) -> None:
    if not name:
        return
    key = name.strip().lower()
    _SENSITIVE_FIELDS.add(key)
    if hash_field:
        _SENSITIVE_HASH_FIELDS[key] = hash_field.strip().lower()


def get_registered_sensitive_fields() -> Set[str]:
    return set(_SENSITIVE_FIELDS)


def get_sensitive_hash_field(name: str) -> Optional[str]:
    if not name:
        return None
    return _SENSITIVE_HASH_FIELDS.get(name.strip().lower())


def get_registered_sensitive_hash_fields() -> Dict[str, str]:
    return dict(_SENSITIVE_HASH_FIELDS)


def get_mask_fields(config_value: str = '') -> Set[str]:
    hash_fields = set(_SENSITIVE_HASH_FIELDS.values())
    return _parse_config_set(config_value) | get_registered_sensitive_fields() | hash_fields
