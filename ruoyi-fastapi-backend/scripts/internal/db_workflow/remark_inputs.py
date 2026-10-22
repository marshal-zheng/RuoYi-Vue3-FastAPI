"""Explicit legacy release input adaptation after artifact checksum verification."""

from copy import deepcopy
from dataclasses import replace

from common.remark_document_v1 import plain_to_remark, validate_remark

KEYS = {'sys_dict_type': 'dict_id', 'sys_dict_data': 'dict_code', 'sys_config': 'config_id'}


def release_row(table, row):
    result = deepcopy(row)
    if table in KEYS and 'remark' in result:
        value = result['remark']
        result['remark'] = (
            plain_to_remark(value, identity_key=f'{table}:{result[KEYS[table]]}:remark')
            if isinstance(value, str)
            else validate_remark(value)
        )
    return result


def release_operation(operation):
    if operation.entity_type not in KEYS or 'remark' not in operation.values:
        return operation
    return replace(operation, values=release_row(operation.entity_type, operation.values))
