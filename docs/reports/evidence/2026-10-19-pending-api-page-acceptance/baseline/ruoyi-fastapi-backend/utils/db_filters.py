from typing import Optional

from sqlalchemy import or_

from module_admin.entity.do.enums import DelFlagEnum


def not_deleted(column, del_flag_value: Optional[str] = None):
    """
    Build a "not deleted" condition that treats NULL as not deleted.

    This keeps legacy data (NULL del_flag) visible while preserving the
    standard del_flag semantics.
    """
    value = DelFlagEnum.EXIST.value if del_flag_value is None else del_flag_value
    return or_(column == value, column.is_(None))
