"""Repository protocol contracts."""

from __future__ import annotations

from typing import (
    Any,
    Protocol,
    runtime_checkable,
)

TEntity = Any


@runtime_checkable
class IBaseRepository(Protocol):
    """Common repository contract for CRUD-style data access."""

    async def get_by_id(
        self,
        id: Any,
        relations: list[str] | None = None,
        include_deleted: bool = False,
    ) -> Any | None:
        """Return entity by primary key."""

    async def find_all(
        self,
        filters: dict[str, Any] | None = None,
        order_by: list[Any] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        relations: list[str] | None = None,
        include_deleted: bool = False,
    ) -> list[Any]:
        """Return entities that match filters."""

    async def find_one(
        self,
        filters: dict[str, Any] | None = None,
        include_deleted: bool = False,
    ) -> Any | None:
        """Return one entity that matches filters."""

    async def add(self, entity: Any) -> Any:
        """Persist one entity."""

    async def add_all(self, entities: list[Any]) -> list[Any]:
        """Persist many entities."""

    async def update(self, entity: Any) -> Any:
        """Persist entity updates."""

    async def delete_by_id(self, id: Any) -> bool:
        """Delete one entity by primary key."""

    async def delete_by_ids(self, ids: list[Any]) -> int:
        """Delete many entities by primary keys."""

    async def count(
        self,
        filters: dict[str, Any] | None = None,
        include_deleted: bool = False,
    ) -> int:
        """Count entities that match filters."""

    async def exists(self, filters: dict[str, Any] | None = None) -> bool:
        """Return whether at least one entity matches filters."""


@runtime_checkable
class IAuditLogRepository(Protocol):
    """Protocol contract for `AuditLogRepository`."""

    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        table_name: str | None = None,
        action: str | None = None,
        operator_name: str | None = None,
        request_id: str | None = None,
        begin_time: str | None = None,
        end_time: str | None = None,
        order_by_column: str | None = None,
        is_asc: str | None = None,
    ) -> Any:
        """Contract for `AuditLogRepository.paginate_with_filters`."""

    async def delete_by_id(self, audit_id: int) -> int:
        """Contract for `AuditLogRepository.delete_by_id`."""

    async def delete_by_ids(self, audit_ids: list[int]) -> int:
        """Contract for `AuditLogRepository.delete_by_ids`."""

    async def clear_all(self) -> int:
        """Contract for `AuditLogRepository.clear_all`."""


@runtime_checkable
class IDataSourceRepository(Protocol):
    """Protocol contract for DataSourceRepository."""

    async def find_by_name(self, name: str) -> Any | None: ...
    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        name: str | None = None,
        type: str | None = None,
        status: str | None = None,
    ) -> tuple[list[Any], int]: ...
    async def add(self, entity: Any) -> Any: ...
    async def update(self, entity: Any) -> Any: ...
    async def soft_delete_by_ids(self, ids: list[Any]) -> int: ...
    async def get_by_id(self, id: Any, **kwargs: Any) -> Any | None: ...


@runtime_checkable
class ICommonRepository(Protocol):
    """Protocol contract for `CommonRepository`."""

    async def list_sys_tables(self) -> list[dict[str, str]]:
        """Contract for `CommonRepository.list_sys_tables`."""


@runtime_checkable
class IConfigRepository(Protocol):
    """Protocol contract for `ConfigRepository`."""

    async def find_by_id(self, config_id: int) -> Any | None:
        """Contract for `ConfigRepository.find_by_id`."""

    async def find_by_key(self, config_key: str) -> Any | None:
        """Contract for `ConfigRepository.find_by_key`."""

    async def find_by_key_and_value(self, config_key: str | None = None, config_value: str | None = None) -> Any | None:
        """Contract for `ConfigRepository.find_by_key_and_value`."""

    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        config_name: str | None = None,
        config_key: str | None = None,
        config_type: str | None = None,
        begin_time: str | None = None,
        end_time: str | None = None,
    ) -> Any:
        """Contract for `ConfigRepository.paginate_with_filters`."""

    async def delete_by_id(self, config_id: int) -> int:
        """Contract for `ConfigRepository.delete_by_id`."""

    async def delete_by_ids(self, config_ids: list[int]) -> int:
        """Contract for `ConfigRepository.delete_by_ids`."""


@runtime_checkable
class IDeptRepository(Protocol):
    """Protocol contract for `DeptRepository`."""

    async def find_by_id(self, dept_id: int) -> Any | None:
        """Contract for `DeptRepository.find_by_id`."""

    async def find_active_by_id(self, dept_id: int) -> Any | None:
        """Contract for `DeptRepository.find_active_by_id`."""

    async def find_by_parent_and_name(self, parent_id: int | None, dept_name: str | None) -> Any | None:
        """Contract for `DeptRepository.find_by_parent_and_name`."""

    async def find_children(self, dept_id: int) -> list[Any]:
        """Contract for `DeptRepository.find_children`."""

    async def find_direct_children(self, dept_id: int) -> list[Any]:
        """Contract for `DeptRepository.find_direct_children`."""

    async def find_all_for_tree(self, dept_name: str | None = None, data_scope_sql: str = 'True') -> list[Any]:
        """Contract for `DeptRepository.find_all_for_tree`."""

    async def find_for_edit_option(self, exclude_dept_id: int, data_scope_sql: str = 'True') -> list[Any]:
        """Contract for `DeptRepository.find_for_edit_option`."""

    async def find_with_filters(
        self,
        dept_id: int | None = None,
        status: str | None = None,
        dept_name: str | None = None,
        data_scope_sql: str = 'True',
    ) -> list[Any]:
        """Contract for `DeptRepository.find_with_filters`."""

    async def update_children_ancestors(self, updates: list[Any]) -> Any:
        """Contract for `DeptRepository.update_children_ancestors`."""

    async def update_status_normal(self, dept_ids: list[int]) -> Any:
        """Contract for `DeptRepository.update_status_normal`."""

    async def soft_delete(self, dept_id: int, update_by: str) -> bool:
        """Contract for `DeptRepository.soft_delete`."""

    async def count_normal_children(self, dept_id: int) -> int:
        """Contract for `DeptRepository.count_normal_children`."""

    async def count_direct_children(self, dept_id: int) -> int:
        """Contract for `DeptRepository.count_direct_children`."""

    async def count_users(self, dept_id: int) -> int:
        """Contract for `DeptRepository.count_users`."""

    async def build_dept_tree_optimized(
        self, dept_name: str | None = None, status: str | None = None, data_scope_sql: str = 'True'
    ) -> list[Any]:
        """Contract for `DeptRepository.build_dept_tree_optimized`."""

    async def find_children_by_ancestors_prefix(self, dept_id: int) -> list[Any]:
        """Contract for `DeptRepository.find_children_by_ancestors_prefix`."""

    async def get_dept_id_and_children(self, dept_id: int) -> list[int]:
        """Contract for `DeptRepository.get_dept_id_and_children`."""


@runtime_checkable
class IDeviceCategoryRepository(Protocol):
    """Protocol contract for `DeviceCategoryRepository`."""

    async def find_by_id(self, category_id: int) -> Any | None:
        """Contract for `DeviceCategoryRepository.find_by_id`."""

    async def find_by_name(self, name: str) -> Any | None:
        """Contract for `DeviceCategoryRepository.find_by_name`."""

    async def find_all_active(self) -> list[Any]:
        """Contract for `DeviceCategoryRepository.find_all_active`."""

    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        name: str | None = None,
        status: str | None = None,
        begin_time: Any | None = None,
        end_time: Any | None = None,
    ) -> tuple[list[Any], int]:
        """Contract for `DeviceCategoryRepository.paginate_with_filters`."""

    async def delete_by_ids(self, category_ids: list[int]) -> int:
        """Contract for `DeviceCategoryRepository.delete_by_ids`."""


@runtime_checkable
class IDeviceInterfaceRepository(Protocol):
    """Protocol contract for `DeviceInterfaceRepository`."""

    async def find_by_device_id(self, device_id: int) -> list[Any]:
        """Contract for `DeviceInterfaceRepository.find_by_device_id`."""

    async def delete_by_device_id(self, device_id: int) -> int:
        """Contract for `DeviceInterfaceRepository.delete_by_device_id`."""

    async def delete_by_device_ids(self, device_ids: list[int]) -> int:
        """Contract for `DeviceInterfaceRepository.delete_by_device_ids`."""


@runtime_checkable
class IDeviceRepository(Protocol):
    """Protocol contract for `DeviceRepository`."""

    async def get_by_id_with_interfaces(self, device_id: int) -> Any | None:
        """Contract for `DeviceRepository.get_by_id_with_interfaces`."""

    async def find_by_name(self, device_name: str) -> Any | None:
        """Contract for `DeviceRepository.find_by_name`."""

    async def find_by_name_and_type(self, device_name: str, device_type: str | None = None) -> Any | None:
        """Contract for `DeviceRepository.find_by_name_and_type`."""

    async def find_by_ids(self, device_ids: list[int]) -> list[Any]:
        """Contract for `DeviceRepository.find_by_ids`."""

    async def search_devices(
        self,
        device_name: str | None = None,
        bus_type: str | None = None,
        device_type: str | None = None,
        category_id: int | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Any:
        """Contract for `DeviceRepository.search_devices`."""

    async def delete_by_device_ids(self, device_ids: list[int]) -> int:
        """Contract for `DeviceRepository.delete_by_device_ids`."""

    async def count_by_category_ids(self, category_ids: list[int]) -> int:
        """Contract for `DeviceRepository.count_by_category_ids`."""

    async def commit(self) -> Any:
        """Contract for `DeviceRepository.commit`."""


@runtime_checkable
class IGenTableColumnRepository(Protocol):
    """Protocol contract for `GenTableColumnRepository`."""

    async def find_by_table_id(self, table_id: int) -> list[Any]:
        """Contract for `GenTableColumnRepository.find_by_table_id`."""

    async def get_db_columns_by_table_name(self, table_name: str) -> list[Any]:
        """Contract for `GenTableColumnRepository.get_db_columns_by_table_name`."""

    async def add(self, column_data: dict[str, Any]) -> Any:
        """Contract for `GenTableColumnRepository.add`."""

    async def update(self, column_data: dict[str, Any]) -> None:
        """Contract for `GenTableColumnRepository.update`."""

    async def delete_by_table_id(self, table_id: int) -> None:
        """Contract for `GenTableColumnRepository.delete_by_table_id`."""

    async def delete_by_column_id(self, column_id: int) -> None:
        """Contract for `GenTableColumnRepository.delete_by_column_id`."""

    async def delete_by_column_ids(self, column_ids: list[int]) -> None:
        """Contract for `GenTableColumnRepository.delete_by_column_ids`."""


@runtime_checkable
class IGenTableRepository(Protocol):
    """Protocol contract for `GenTableRepository`."""

    async def find_by_id(self, table_id: int) -> Any | None:
        """Contract for `GenTableRepository.find_by_id`."""

    async def find_by_name(self, table_name: str) -> Any | None:
        """Contract for `GenTableRepository.find_by_name`."""

    async def find_all(self) -> list[Any]:
        """Contract for `GenTableRepository.find_all`."""

    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        table_name: str | None = None,
        table_comment: str | None = None,
        begin_time: str | None = None,
        end_time: str | None = None,
        is_page: bool = True,
    ) -> Any:
        """Contract for `GenTableRepository.paginate_with_filters`."""

    async def get_db_table_list(
        self,
        page: int,
        page_size: int,
        table_name: str | None = None,
        table_comment: str | None = None,
        begin_time: str | None = None,
        end_time: str | None = None,
        is_page: bool = True,
    ) -> Any:
        """Contract for `GenTableRepository.get_db_table_list`."""

    async def get_db_tables_by_names(self, table_names: list[str]) -> list[Any]:
        """Contract for `GenTableRepository.get_db_tables_by_names`."""

    async def execute_sql_statements(self, sql_statements: list[Any]) -> None:
        """Contract for `GenTableRepository.execute_sql_statements`."""

    async def add(self, gen_table_data: dict[str, Any]) -> Any:
        """Contract for `GenTableRepository.add`."""

    async def update(self, gen_table_data: dict[str, Any]) -> None:
        """Contract for `GenTableRepository.update`."""

    async def delete_by_id(self, table_id: int) -> None:
        """Contract for `GenTableRepository.delete_by_id`."""

    async def delete_by_ids(self, table_ids: list[int]) -> None:
        """Contract for `GenTableRepository.delete_by_ids`."""


@runtime_checkable
class IDictDataRepository(Protocol):
    """Protocol contract for `DictDataRepository`."""

    async def find_by_code(self, dict_code: int) -> Any | None:
        """Contract for `DictDataRepository.find_by_code`."""

    async def find_by_type_and_label(
        self, dict_type: str, dict_label: str, dict_value: str | None = None
    ) -> Any | None:
        """Contract for `DictDataRepository.find_by_type_and_label`."""

    async def find_by_type(self, dict_type: str) -> list[Any]:
        """Contract for `DictDataRepository.find_by_type`."""

    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        dict_type: str | None = None,
        dict_label: str | None = None,
        status: str | None = None,
    ) -> Any:
        """Contract for `DictDataRepository.paginate_with_filters`."""

    async def delete_by_code(self, dict_code: int) -> int:
        """Contract for `DictDataRepository.delete_by_code`."""

    async def count_by_type(self, dict_type: str) -> int:
        """Contract for `DictDataRepository.count_by_type`."""


@runtime_checkable
class IDictTypeRepository(Protocol):
    """Protocol contract for `DictTypeRepository`."""

    async def find_by_id(self, dict_id: int) -> Any | None:
        """Contract for `DictTypeRepository.find_by_id`."""

    async def find_by_type(self, dict_type: str) -> Any | None:
        """Contract for `DictTypeRepository.find_by_type`."""

    async def find_by_type_or_name(self, dict_type: str | None = None, dict_name: str | None = None) -> Any | None:
        """Contract for `DictTypeRepository.find_by_type_or_name`."""

    async def find_all(self) -> list[Any]:
        """Contract for `DictTypeRepository.find_all`."""

    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        dict_name: str | None = None,
        dict_type: str | None = None,
        status: str | None = None,
        begin_time: str | None = None,
        end_time: str | None = None,
    ) -> Any:
        """Contract for `DictTypeRepository.paginate_with_filters`."""

    async def delete_by_id(self, dict_id: int) -> int:
        """Contract for `DictTypeRepository.delete_by_id`."""


@runtime_checkable
class IJobLogRepository(Protocol):
    """Protocol contract for `JobLogRepository`."""

    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        job_name: str | None = None,
        job_group: str | None = None,
        status: str | None = None,
        begin_time: str | None = None,
        end_time: str | None = None,
    ) -> Any:
        """Contract for `JobLogRepository.paginate_with_filters`."""

    def add_sync(self, db: Any, job_log: Any) -> Any:
        """Contract for `JobLogRepository.add_sync`."""

    def commit_sync(self, db: Any) -> Any:
        """Contract for `JobLogRepository.commit_sync`."""

    async def delete_by_id(self, job_log_id: int) -> int:
        """Contract for `JobLogRepository.delete_by_id`."""

    async def delete_by_ids(self, job_log_ids: list[int]) -> int:
        """Contract for `JobLogRepository.delete_by_ids`."""

    async def clear_all(self) -> int:
        """Contract for `JobLogRepository.clear_all`."""


@runtime_checkable
class IJobRepository(Protocol):
    """Protocol contract for `JobRepository`."""

    async def find_by_id(self, job_id: int) -> Any | None:
        """Contract for `JobRepository.find_by_id`."""

    async def find_by_info(
        self,
        job_name: str | None = None,
        job_group: str | None = None,
        job_executor: str | None = None,
        invoke_target: str | None = None,
        job_args: str | None = None,
        job_kwargs: str | None = None,
        cron_expression: str | None = None,
    ) -> Any | None:
        """Contract for `JobRepository.find_by_info`."""

    async def find_all_active(self) -> list[Any]:
        """Contract for `JobRepository.find_all_active`."""

    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        job_name: str | None = None,
        job_group: str | None = None,
        status: str | None = None,
    ) -> Any:
        """Contract for `JobRepository.paginate_with_filters`."""

    async def delete_by_id(self, job_id: int) -> int:
        """Contract for `JobRepository.delete_by_id`."""


@runtime_checkable
class ILoginLogRepository(Protocol):
    """Protocol contract for `LoginLogRepository`."""

    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        ipaddr: str | None = None,
        user_name: str | None = None,
        status: str | None = None,
        begin_time: str | None = None,
        end_time: str | None = None,
        order_by_column: str | None = None,
        is_asc: str | None = None,
    ) -> Any:
        """Contract for `LoginLogRepository.paginate_with_filters`."""

    async def delete_by_id(self, info_id: int) -> int:
        """Contract for `LoginLogRepository.delete_by_id`."""

    async def delete_by_ids(self, info_ids: list[int]) -> int:
        """Contract for `LoginLogRepository.delete_by_ids`."""

    async def clear_all(self) -> int:
        """Contract for `LoginLogRepository.clear_all`."""

    async def paginate_cursor(
        self,
        page_size: int,
        cursor: int | None = None,
        ipaddr: str | None = None,
        user_name: str | None = None,
        status: str | None = None,
        begin_time: str | None = None,
        end_time: str | None = None,
    ) -> dict[str, Any]:
        """Contract for `LoginLogRepository.paginate_cursor`."""


@runtime_checkable
class ILoginRepository(Protocol):
    """Protocol contract for `LoginRepository`."""

    async def find_user_with_dept(self, user_name: str) -> tuple[Any, Any | None] | None:
        """Contract for `LoginRepository.find_user_with_dept`."""


@runtime_checkable
class IMenuRepository(Protocol):
    """Protocol contract for `MenuRepository`."""

    async def find_by_id(self, menu_id: int) -> Any | None:
        """Contract for `MenuRepository.find_by_id`."""

    async def find_by_parent_and_name(
        self, parent_id: int | None, menu_name: str | None, menu_type: str | None = None
    ) -> Any | None:
        """Contract for `MenuRepository.find_by_parent_and_name`."""

    async def find_all_active(self) -> list[Any]:
        """Contract for `MenuRepository.find_all_active`."""

    async def find_menus_by_user(self, user_id: int, is_admin: bool = False) -> list[Any]:
        """Contract for `MenuRepository.find_menus_by_user`."""

    async def find_with_filters(
        self,
        user_id: int | None = None,
        is_admin: bool = False,
        status: str | None = None,
        menu_name: str | None = None,
        visible: str | None = None,
    ) -> list[Any]:
        """Contract for `MenuRepository.find_with_filters`."""

    async def delete_by_id(self, menu_id: int) -> int:
        """Contract for `MenuRepository.delete_by_id`."""

    async def count_children(self, menu_id: int) -> int:
        """Contract for `MenuRepository.count_children`."""

    async def count_roles(self, menu_id: int) -> int:
        """Contract for `MenuRepository.count_roles`."""


@runtime_checkable
class INoticeRepository(Protocol):
    """Protocol contract for `NoticeRepository`."""

    async def find_by_id(self, notice_id: int) -> Any | None:
        """Contract for `NoticeRepository.find_by_id`."""

    async def find_by_content(self, notice_title: str, notice_type: str, notice_content: str) -> Any | None:
        """Contract for `NoticeRepository.find_by_content`."""

    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        notice_title: str | None = None,
        create_by: str | None = None,
        notice_type: str | None = None,
        begin_time: str | None = None,
        end_time: str | None = None,
    ) -> Any:
        """Contract for `NoticeRepository.paginate_with_filters`."""

    async def delete_by_id(self, notice_id: int) -> int:
        """Contract for `NoticeRepository.delete_by_id`."""


@runtime_checkable
class IOperLogRepository(Protocol):
    """Protocol contract for `OperLogRepository`."""

    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        title: str | None = None,
        oper_name: str | None = None,
        business_type: int | None = None,
        status: int | None = None,
        begin_time: str | None = None,
        end_time: str | None = None,
        order_by_column: str | None = None,
        is_asc: str | None = None,
    ) -> Any:
        """Contract for `OperLogRepository.paginate_with_filters`."""

    async def delete_by_id(self, oper_id: int) -> int:
        """Contract for `OperLogRepository.delete_by_id`."""

    async def delete_by_ids(self, oper_ids: list[int]) -> int:
        """Contract for `OperLogRepository.delete_by_ids`."""

    async def clear_all(self) -> int:
        """Contract for `OperLogRepository.clear_all`."""

    async def paginate_cursor(
        self,
        page_size: int,
        cursor: int | None = None,
        title: str | None = None,
        oper_name: str | None = None,
        business_type: int | None = None,
        status: int | None = None,
        begin_time: str | None = None,
        end_time: str | None = None,
    ) -> dict[str, Any]:
        """Contract for `OperLogRepository.paginate_cursor`."""


@runtime_checkable
class IPostRepository(Protocol):
    """Protocol contract for `PostRepository`."""

    async def find_by_id(self, post_id: int) -> Any | None:
        """Contract for `PostRepository.find_by_id`."""

    async def find_active_by_id(self, post_id: int) -> Any | None:
        """Contract for `PostRepository.find_active_by_id`."""

    async def find_by_name_or_code(
        self, post_name: str | None = None, post_code: str | None = None, post_sort: int | None = None
    ) -> Any | None:
        """Contract for `PostRepository.find_by_name_or_code`."""

    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        post_code: str | None = None,
        post_name: str | None = None,
        status: str | None = None,
    ) -> Any:
        """Contract for `PostRepository.paginate_with_filters`."""

    async def find_all_with_filters(
        self, post_code: str | None = None, post_name: str | None = None, status: str | None = None
    ) -> list[Any]:
        """Contract for `PostRepository.find_all_with_filters`."""

    async def delete_by_id(self, post_id: int) -> int:
        """Contract for `PostRepository.delete_by_id`."""

    async def count_users(self, post_id: int) -> int:
        """Contract for `PostRepository.count_users`."""


@runtime_checkable
class IProjectRepository(Protocol):
    """Protocol contract for `ProjectRepository`."""

    async def find_by_id(self, project_id: int) -> Any | None:
        """Contract for `ProjectRepository.find_by_id`."""

    async def find_all_active(self) -> list[Any]:
        """Contract for `ProjectRepository.find_all_active`."""

    async def get_max_project_code_by_prefix(self, prefix: str) -> str | None:
        """Contract for `ProjectRepository.get_max_project_code_by_prefix`."""

    async def paginate_with_filters(
        self, page: int, page_size: int, begin_time: str | None = None, end_time: str | None = None
    ) -> Any:
        """Contract for `ProjectRepository.paginate_with_filters`."""

    async def soft_delete(self, project_id: int, update_by: str) -> bool:
        """Contract for `ProjectRepository.soft_delete`."""

    async def soft_delete_batch(self, project_ids: list[int], update_by: str) -> int:
        """Contract for `ProjectRepository.soft_delete_batch`."""


@runtime_checkable
class IProjectTopologyRepository(Protocol):
    """Protocol contract for `ProjectTopologyRepository`."""

    async def find_by_project_and_version(self, project_id: int, version_id: int | None = None) -> Any | None:
        """Contract for `ProjectTopologyRepository.find_by_project_and_version`."""

    async def save_topology(
        self,
        project_id: int,
        topology_data: Any,
        version_id: int | None = None,
        create_by: str | None = None,
        update_by: str | None = None,
    ) -> Any:
        """Contract for `ProjectTopologyRepository.save_topology`."""

    async def find_by_version_ids(self, project_id: int, version_ids: list[int]) -> list[Any]:
        """Contract for `ProjectTopologyRepository.find_by_version_ids`."""


@runtime_checkable
class IProjectVersionRepository(Protocol):
    """Protocol contract for `ProjectVersionRepository`."""

    async def find_by_id(self, version_id: int) -> Any | None:
        """Contract for `ProjectVersionRepository.find_by_id`."""

    async def find_by_project(self, project_id: int) -> list[Any]:
        """Contract for `ProjectVersionRepository.find_by_project`."""

    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        project_id: int | None = None,
        version_name: str | None = None,
        version_number: str | None = None,
        begin_time: str | None = None,
        end_time: str | None = None,
    ) -> Any:
        """Contract for `ProjectVersionRepository.paginate_with_filters`."""

    async def check_version_number_unique(
        self, project_id: int, version_number: str, exclude_version_id: int | None = None
    ) -> bool:
        """Contract for `ProjectVersionRepository.check_version_number_unique`."""

    async def count_by_projects(self, project_ids: list[int]) -> dict[int, int]:
        """Contract for `ProjectVersionRepository.count_by_projects`."""

    async def find_locked_by_projects(self, project_ids: list[int]) -> dict[int, list[Any]]:
        """Contract for `ProjectVersionRepository.find_locked_by_projects`."""

    async def lock_version(
        self,
        version_id: int,
        is_locked: str,
        update_by: str,
        locked_by: str | None = None,
        locked_time: Any | None = None,
    ) -> bool:
        """Contract for `ProjectVersionRepository.lock_version`."""

    async def unlock_by_project(self, project_id: int, operator: str | None = None) -> int:
        """Contract for `ProjectVersionRepository.unlock_by_project`."""

    async def soft_delete_batch(self, version_ids: list[int], update_by: str) -> int:
        """Contract for `ProjectVersionRepository.soft_delete_batch`."""


@runtime_checkable
class IProtocolRepository(Protocol):
    """Protocol contract for `ProtocolRepository`."""

    async def find_by_id(self, protocol_id: int) -> Any | None:
        """Contract for `ProtocolRepository.find_by_id`."""

    async def find_by_name(self, protocol_name: str) -> Any | None:
        """Contract for `ProtocolRepository.find_by_name`."""

    async def find_all_active(self) -> list[Any]:
        """Contract for `ProtocolRepository.find_all_active`."""

    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        protocol_name: str | None = None,
        protocol_type: str | None = None,
        begin_time: str | None = None,
        end_time: str | None = None,
    ) -> Any:
        """Contract for `ProtocolRepository.paginate_with_filters`."""

    async def soft_delete_batch(self, protocol_ids: list[int], update_by: str) -> int:
        """Contract for `ProtocolRepository.soft_delete_batch`."""

    async def commit(self) -> Any:
        """Contract for `ProtocolRepository.commit`."""


@runtime_checkable
class IRoleDeptRepository(Protocol):
    """Protocol contract for `RoleDeptRepository`."""

    async def find_by_role_id(self, role_id: int) -> list[Any]:
        """Contract for `RoleDeptRepository.find_by_role_id`."""

    async def find_depts_by_role(self, role_id: int, check_strictly: bool = False) -> list[Any]:
        """Contract for `RoleDeptRepository.find_depts_by_role`."""

    async def delete_by_role_id(self, role_id: int) -> int:
        """Contract for `RoleDeptRepository.delete_by_role_id`."""

    async def batch_add(self, role_id: int, dept_ids: list[int]) -> Any:
        """Contract for `RoleDeptRepository.batch_add`."""


@runtime_checkable
class IRoleMenuRepository(Protocol):
    """Protocol contract for `RoleMenuRepository`."""

    async def find_by_role_id(self, role_id: int) -> list[Any]:
        """Contract for `RoleMenuRepository.find_by_role_id`."""

    async def find_menus_by_role(self, role_id: int, check_strictly: bool = False) -> list[Any]:
        """Contract for `RoleMenuRepository.find_menus_by_role`."""

    async def delete_by_role_id(self, role_id: int) -> int:
        """Contract for `RoleMenuRepository.delete_by_role_id`."""

    async def batch_add(self, role_id: int, menu_ids: list[int]) -> Any:
        """Contract for `RoleMenuRepository.batch_add`."""


@runtime_checkable
class IRoleRepository(Protocol):
    """Protocol contract for `RoleRepository`."""

    async def find_by_name(self, role_name: str) -> Any | None:
        """Contract for `RoleRepository.find_by_name`."""

    async def find_by_key(self, role_key: str) -> Any | None:
        """Contract for `RoleRepository.find_by_key`."""

    async def find_by_id(self, role_id: int) -> Any | None:
        """Contract for `RoleRepository.find_by_id`."""

    async def find_active_by_id(self, role_id: int) -> Any | None:
        """Contract for `RoleRepository.find_active_by_id`."""

    async def find_all_active(self, exclude_admin: bool = True) -> list[Any]:
        """Contract for `RoleRepository.find_all_active`."""

    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        role_id: int | None = None,
        role_name: str | None = None,
        role_key: str | None = None,
        status: str | None = None,
        begin_time: str | None = None,
        end_time: str | None = None,
        data_scope_sql: str = 'True',
    ) -> Any:
        """Contract for `RoleRepository.paginate_with_filters`."""

    async def soft_delete(self, role_id: int, update_by: str) -> bool:
        """Contract for `RoleRepository.soft_delete`."""

    async def count_users(self, role_id: int) -> int:
        """Contract for `RoleRepository.count_users`."""

    async def get_role_with_menus(self, role_id: int) -> dict[str, Any]:
        """Contract for `RoleRepository.get_role_with_menus`."""

    async def get_roles_menus_batch(self, role_ids: list[int]) -> dict[int, list[Any]]:
        """Contract for `RoleRepository.get_roles_menus_batch`."""

    async def get_user_permissions_optimized(self, user_id: int) -> list[str]:
        """Contract for `RoleRepository.get_user_permissions_optimized`."""


@runtime_checkable
class ISimulationAlarmRepository(Protocol):
    """Protocol contract for `SimulationAlarmRepository`."""

    async def find_by_session(self, session_id: str, alarm_type: str | None = None) -> list[Any]:
        """Contract for `SimulationAlarmRepository.find_by_session`."""

    async def batch_create(self, alarms: list[Any]) -> Any:
        """Contract for `SimulationAlarmRepository.batch_create`."""


@runtime_checkable
class ISimulationBandwidthRepository(Protocol):
    """Protocol contract for `SimulationBandwidthRepository`."""

    async def find_by_session(
        self,
        session_id: str,
        port_id: str | None = None,
        start_time: float | None = None,
        end_time: float | None = None,
    ) -> list[Any]:
        """Contract for `SimulationBandwidthRepository.find_by_session`."""

    async def batch_create(self, bandwidths: list[Any]) -> Any:
        """Contract for `SimulationBandwidthRepository.batch_create`."""


@runtime_checkable
class ISimulationMessageRepository(Protocol):
    """Protocol contract for `SimulationMessageRepository`."""

    async def find_by_session(
        self, session_id: str, start_time: float | None = None, end_time: float | None = None
    ) -> list[Any]:
        """Contract for `SimulationMessageRepository.find_by_session`."""

    async def batch_create(self, messages: list[Any]) -> Any:
        """Contract for `SimulationMessageRepository.batch_create`."""


@runtime_checkable
class ISimulationSessionRepository(Protocol):
    """Protocol contract for `SimulationSessionRepository`."""

    async def find_by_id(self, session_id: str) -> Any | None:
        """Contract for `SimulationSessionRepository.find_by_id`."""

    async def find_by_project(self, project_id: int, version_id: int | None = None) -> list[Any]:
        """Contract for `SimulationSessionRepository.find_by_project`."""

    async def update_status(self, session_id: str, status: str, end_time: Any | None = None) -> Any | None:
        """Contract for `SimulationSessionRepository.update_status`."""

    async def delete_with_data(self, session_id: str) -> Any:
        """Contract for `SimulationSessionRepository.delete_with_data`."""


@runtime_checkable
class IUserPostRepository(Protocol):
    """Protocol contract for `UserPostRepository`."""

    async def find_by_user_id(self, user_id: int) -> list[Any]:
        """Contract for `UserPostRepository.find_by_user_id`."""

    async def delete_by_user_id(self, user_id: int) -> int:
        """Contract for `UserPostRepository.delete_by_user_id`."""


@runtime_checkable
class IUserRepository(Protocol):
    """Protocol contract for `UserRepository`."""

    async def find_by_username(self, username: str) -> Any | None:
        """Contract for `UserRepository.find_by_username`."""

    async def find_by_phone(self, phone: str) -> Any | None:
        """Contract for `UserRepository.find_by_phone`."""

    async def find_by_email(self, email: str) -> Any | None:
        """Contract for `UserRepository.find_by_email`."""

    async def find_by_id_card(self, id_card: str) -> Any | None:
        """Contract for `UserRepository.find_by_id_card`."""

    async def get_user_with_relations(self, user_id: int) -> dict[str, Any]:
        """Contract for `UserRepository.get_user_with_relations`."""

    async def paginate_with_dept(
        self,
        page: int,
        page_size: int,
        user_id: int | None = None,
        dept_id: int | None = None,
        user_name: str | None = None,
        nick_name: str | None = None,
        email: str | None = None,
        phonenumber: str | None = None,
        status: str | None = None,
        sex: str | None = None,
        begin_time: str | None = None,
        end_time: str | None = None,
        data_scope_sql: str = 'True',
    ) -> Any:
        """Contract for `UserRepository.paginate_with_dept`."""

    async def soft_delete(self, user_id: int, update_by: str) -> bool:
        """Contract for `UserRepository.soft_delete`."""

    async def paginate_allocated_by_role(
        self,
        role_id: int,
        page: int,
        page_size: int,
        user_name: str | None = None,
        phonenumber: str | None = None,
        data_scope_sql: str = 'True',
    ) -> Any:
        """Contract for `UserRepository.paginate_allocated_by_role`."""

    async def paginate_unallocated_by_role(
        self,
        role_id: int,
        page: int,
        page_size: int,
        user_name: str | None = None,
        phonenumber: str | None = None,
        data_scope_sql: str = 'True',
    ) -> Any:
        """Contract for `UserRepository.paginate_unallocated_by_role`."""

    async def get_users_roles_batch(self, user_ids: list[int]) -> dict[int, list[Any]]:
        """Contract for `UserRepository.get_users_roles_batch`."""

    async def get_users_posts_batch(self, user_ids: list[int]) -> dict[int, list[Any]]:
        """Contract for `UserRepository.get_users_posts_batch`."""


@runtime_checkable
class IUserRoleRepository(Protocol):
    """Protocol contract for `UserRoleRepository`."""

    async def find_by_user_id(self, user_id: int) -> list[Any]:
        """Contract for `UserRoleRepository.find_by_user_id`."""

    async def delete_by_user_id(self, user_id: int) -> int:
        """Contract for `UserRoleRepository.delete_by_user_id`."""

    async def delete_by_user_and_role(self, user_id: int, role_id: int) -> int:
        """Contract for `UserRoleRepository.delete_by_user_and_role`."""

    async def find_by_user_and_role(self, user_id: int, role_id: int) -> Any | None:
        """Contract for `UserRoleRepository.find_by_user_and_role`."""


__all__ = [
    'IAuditLogRepository',
    'IBaseRepository',
    'IDataSourceRepository',
    'ICommonRepository',
    'IConfigRepository',
    'IDeptRepository',
    'IDeviceCategoryRepository',
    'IDeviceInterfaceRepository',
    'IDeviceRepository',
    'IDictDataRepository',
    'IDictTypeRepository',
    'IGenTableColumnRepository',
    'IGenTableRepository',
    'IJobLogRepository',
    'IJobRepository',
    'ILoginLogRepository',
    'ILoginRepository',
    'IMenuRepository',
    'INoticeRepository',
    'IOperLogRepository',
    'IPostRepository',
    'IProjectRepository',
    'IProjectTopologyRepository',
    'IProjectVersionRepository',
    'IProtocolRepository',
    'IRoleDeptRepository',
    'IRoleMenuRepository',
    'IRoleRepository',
    'ISimulationAlarmRepository',
    'ISimulationBandwidthRepository',
    'ISimulationMessageRepository',
    'ISimulationSessionRepository',
    'IUserPostRepository',
    'IUserRepository',
    'IUserRoleRepository',
    'TEntity',
]
