"""
Global soft-delete filtering for ORM SELECTs.

Applies default filters for models that have:
- del_flag (legacy soft delete)
- is_deleted (new soft delete)
"""
from sqlalchemy import and_, or_, true
from sqlalchemy import event
from sqlalchemy.orm import Session, with_loader_criteria

INCLUDE_DELETED_OPTION = "include_deleted"
_SOFT_DELETE_FILTER_INITIALIZED = False


def init_soft_delete_filter(base_cls, del_flag_value: str = "0") -> None:
    """
    Register a Session event to auto-filter soft-deleted rows.

    Args:
        base_cls: Declarative base class for all ORM models.
        del_flag_value: Value representing "not deleted" for del_flag.
    """
    global _SOFT_DELETE_FILTER_INITIALIZED
    if _SOFT_DELETE_FILTER_INITIALIZED:
        return
    _SOFT_DELETE_FILTER_INITIALIZED = True

    def _criteria(cls):
        conditions = []
        if hasattr(cls, "del_flag"):
            conditions.append(or_(cls.del_flag == del_flag_value, cls.del_flag.is_(None)))
        if hasattr(cls, "is_deleted"):
            conditions.append(or_(cls.is_deleted == False, cls.is_deleted.is_(None)))
        if not conditions:
            return true()
        return and_(*conditions)

    @event.listens_for(Session, "do_orm_execute")
    def _add_soft_delete_filter(orm_execute_state):
        if not orm_execute_state.is_select:
            return
        if orm_execute_state.execution_options.get(INCLUDE_DELETED_OPTION):
            return
        orm_execute_state.statement = orm_execute_state.statement.options(
            with_loader_criteria(
                base_cls,
                _criteria,
                include_aliases=True,
                track_closure_variables=False,
            )
        )
