"""Service protocol contracts."""

# ruff: noqa: N803

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class IBaseService(Protocol):
    """Marker protocol for application services."""


@runtime_checkable
class IAuditLogService(IBaseService, Protocol):
    """Protocol contract for `AuditLogService`."""

    async def get_audit_log_list_services(self, query_db: Any, query_object: Any, is_page: bool = False) -> Any:
        """Contract for `AuditLogService.get_audit_log_list_services`."""

    async def delete_audit_log_services(self, query_db: Any, page_object: Any) -> Any:
        """Contract for `AuditLogService.delete_audit_log_services`."""

    async def clear_audit_log_services(self, query_db: Any) -> Any:
        """Contract for `AuditLogService.clear_audit_log_services`."""


@runtime_checkable
class ICacheService(IBaseService, Protocol):
    """Protocol contract for `CacheService`."""

    async def get_cache_monitor_statistical_info_services(self, request: Any) -> Any:
        """Contract for `CacheService.get_cache_monitor_statistical_info_services`."""

    async def get_cache_monitor_cache_name_services(self) -> Any:
        """Contract for `CacheService.get_cache_monitor_cache_name_services`."""

    async def get_cache_monitor_cache_key_services(self, request: Any, cache_name: str) -> Any:
        """Contract for `CacheService.get_cache_monitor_cache_key_services`."""

    async def get_cache_monitor_cache_value_services(self, request: Any, cache_name: str, cache_key: str) -> Any:
        """Contract for `CacheService.get_cache_monitor_cache_value_services`."""

    async def clear_cache_monitor_cache_name_services(self, request: Any, cache_name: str) -> Any:
        """Contract for `CacheService.clear_cache_monitor_cache_name_services`."""

    async def clear_cache_monitor_cache_key_services(self, request: Any, cache_key: str) -> Any:
        """Contract for `CacheService.clear_cache_monitor_cache_key_services`."""

    async def clear_cache_monitor_all_services(self, request: Any) -> Any:
        """Contract for `CacheService.clear_cache_monitor_all_services`."""


@runtime_checkable
class ICaptchaService(IBaseService, Protocol):
    """Protocol contract for `CaptchaService`."""

    async def create_captcha_image_service(self) -> Any:
        """Contract for `CaptchaService.create_captcha_image_service`."""


@runtime_checkable
class ICommonService(IBaseService, Protocol):
    """Protocol contract for `CommonService`."""

    async def upload_service(self, request: Any, file: Any) -> Any:
        """Contract for `CommonService.upload_service`."""

    async def download_services(self, background_tasks: Any, file_name: Any, delete: bool) -> Any:
        """Contract for `CommonService.download_services`."""

    async def download_resource_services(self, resource: str) -> Any:
        """Contract for `CommonService.download_resource_services`."""

    async def get_table_names_services(self) -> list[dict[str, str]]:
        """Contract for `CommonService.get_table_names_services`."""


@runtime_checkable
class IConfigService(IBaseService, Protocol):
    """Protocol contract for `ConfigService`."""

    async def get_config_list_services(self, query_object: Any, is_page: bool = False) -> Any:
        """Contract for `ConfigService.get_config_list_services`."""

    async def init_cache_sys_config_services(self, redis: Any) -> Any:
        """Contract for `ConfigService.init_cache_sys_config_services`."""

    async def query_config_list_from_cache_services(self, redis: Any, config_key: str) -> Any:
        """Contract for `ConfigService.query_config_list_from_cache_services`."""

    async def check_config_key_unique_services(self, page_object: Any) -> Any:
        """Contract for `ConfigService.check_config_key_unique_services`."""

    async def add_config_services(self, redis: Any, page_object: Any) -> Any:
        """Contract for `ConfigService.add_config_services`."""

    async def edit_config_services(self, redis: Any, page_object: Any) -> Any:
        """Contract for `ConfigService.edit_config_services`."""

    async def delete_config_services(self, redis: Any, page_object: Any) -> Any:
        """Contract for `ConfigService.delete_config_services`."""

    async def config_detail_services(self, config_id: int) -> Any:
        """Contract for `ConfigService.config_detail_services`."""

    async def export_config_list_services(self, config_list: list) -> Any:
        """Contract for `ConfigService.export_config_list_services`."""

    async def refresh_sys_config_services(self, redis: Any) -> Any:
        """Contract for `ConfigService.refresh_sys_config_services`."""


@runtime_checkable
class IDataSourceService(IBaseService, Protocol):
    """Protocol contract for DataSourceService."""

    async def get_datasource_list_services(self, query: Any) -> Any: ...
    async def datasource_detail_services(self, datasource_id: int) -> Any: ...
    async def add_datasource_services(self, data: Any, current_user: str) -> Any: ...
    async def edit_datasource_services(self, data: Any, current_user: str) -> Any: ...
    async def delete_datasource_services(self, datasource_ids: str) -> Any: ...
    async def test_connection_services(self, config: Any) -> Any: ...
    async def test_saved_connection_services(self, datasource_id: int) -> Any: ...


@runtime_checkable
class IDeptService(IBaseService, Protocol):
    """Protocol contract for `DeptService`."""

    async def get_dept_tree_services(self, page_object: Any, data_scope_sql: str) -> Any:
        """Contract for `DeptService.get_dept_tree_services`."""

    async def get_dept_for_edit_option_services(self, page_object: Any, data_scope_sql: str) -> Any:
        """Contract for `DeptService.get_dept_for_edit_option_services`."""

    async def get_dept_list_services(self, page_object: Any, data_scope_sql: str) -> Any:
        """Contract for `DeptService.get_dept_list_services`."""

    async def check_dept_data_scope_services(self, dept_id: int, data_scope_sql: str) -> Any:
        """Contract for `DeptService.check_dept_data_scope_services`."""

    async def check_dept_name_unique_services(self, page_object: Any) -> Any:
        """Contract for `DeptService.check_dept_name_unique_services`."""

    async def add_dept_services(self, page_object: Any) -> Any:
        """Contract for `DeptService.add_dept_services`."""

    async def edit_dept_services(self, page_object: Any) -> Any:
        """Contract for `DeptService.edit_dept_services`."""

    async def delete_dept_services(self, page_object: Any) -> Any:
        """Contract for `DeptService.delete_dept_services`."""

    async def dept_detail_services(self, dept_id: int) -> Any:
        """Contract for `DeptService.dept_detail_services`."""

    async def export_dept_list_services(self, dept_list: list) -> Any:
        """Contract for `DeptService.export_dept_list_services`."""

    def list_to_tree(self, permission_list: list) -> list:
        """Contract for `DeptService.list_to_tree`."""

    async def replace_first(self, original_str: str, old_str: str, new_str: str) -> Any:
        """Contract for `DeptService.replace_first`."""

    async def update_parent_dept_status_normal(self, dept: Any) -> Any:
        """Contract for `DeptService.update_parent_dept_status_normal`."""

    async def update_dept_children(self, dept_id: int, new_ancestors: str, old_ancestors: str) -> Any:
        """Contract for `DeptService.update_dept_children`."""


@runtime_checkable
class IDeviceCategoryService(IBaseService, Protocol):
    """Protocol contract for `DeviceCategoryService`."""

    async def get_device_category_list_services(self, query: Any, current_user: str) -> Any:
        """Contract for `DeviceCategoryService.get_device_category_list_services`."""

    async def device_category_detail_services(self, category_id: int) -> Any:
        """Contract for `DeviceCategoryService.device_category_detail_services`."""

    async def add_device_category_services(self, category_data: Any, current_user: str) -> Any:
        """Contract for `DeviceCategoryService.add_device_category_services`."""

    async def edit_device_category_services(self, category_data: Any, current_user: str) -> Any:
        """Contract for `DeviceCategoryService.edit_device_category_services`."""

    async def delete_device_category_services(self, category_ids: str) -> Any:
        """Contract for `DeviceCategoryService.delete_device_category_services`."""

    async def get_device_category_options_services(self) -> Any:
        """Contract for `DeviceCategoryService.get_device_category_options_services`."""

    async def check_device_category_name_unique_services(self, name: str, category_id: int | None = None) -> Any:
        """Contract for `DeviceCategoryService.check_device_category_name_unique_services`."""


@runtime_checkable
class IDeviceService(IBaseService, Protocol):
    """Protocol contract for `DeviceService`."""

    async def get_device_list_services(self, query: Any, current_user: str) -> Any:
        """Contract for `DeviceService.get_device_list_services`."""

    async def device_detail_services(self, device_id: int) -> Any:
        """Contract for `DeviceService.device_detail_services`."""

    async def add_device_services(self, device_data: Any, current_user: str) -> Any:
        """Contract for `DeviceService.add_device_services`."""

    async def edit_device_services(self, device_data: Any, current_user: str) -> Any:
        """Contract for `DeviceService.edit_device_services`."""

    async def delete_device_services(self, device_ids: str) -> Any:
        """Contract for `DeviceService.delete_device_services`."""

    async def check_device_name_unique_services(self, device_name: str, device_id: int | None = None) -> Any:
        """Contract for `DeviceService.check_device_name_unique_services`."""

    async def clone_device_services(self, clone_data: Any, current_user: str) -> Any:
        """Contract for `DeviceService.clone_device_services`."""

    async def export_devices_zip_services(self, device_ids: list[int]) -> Any:
        """Contract for `DeviceService.export_devices_zip_services`."""

    async def import_devices_from_zip_services(self, file_bytes: bytes, operator: str) -> Any:
        """Contract for `DeviceService.import_devices_from_zip_services`."""

    async def import_devices_multi_services(self, files: list[bytes], operator: str) -> Any:
        """Contract for `DeviceService.import_devices_multi_services`."""


@runtime_checkable
class IDictDataService(IBaseService, Protocol):
    """Protocol contract for `DictDataService`."""

    async def get_dict_data_list_services(self, query_object: Any, is_page: bool = False) -> Any:
        """Contract for `DictDataService.get_dict_data_list_services`."""

    async def query_dict_data_list_services(self, dict_type: str) -> Any:
        """Contract for `DictDataService.query_dict_data_list_services`."""

    async def init_cache_sys_dict_services(self, redis: Any) -> Any:
        """Contract for `DictDataService.init_cache_sys_dict_services`."""

    async def query_dict_data_list_from_cache_services(self, redis: Any, dict_type: str) -> Any:
        """Contract for `DictDataService.query_dict_data_list_from_cache_services`."""

    async def check_dict_data_unique_services(self, page_object: Any) -> Any:
        """Contract for `DictDataService.check_dict_data_unique_services`."""

    async def add_dict_data_services(self, redis: Any, page_object: Any, operator: str | None = None) -> Any:
        """Contract for `DictDataService.add_dict_data_services`."""

    async def edit_dict_data_services(self, redis: Any, page_object: Any, operator: str | None = None) -> Any:
        """Contract for `DictDataService.edit_dict_data_services`."""

    async def delete_dict_data_services(self, redis: Any, page_object: Any) -> Any:
        """Contract for `DictDataService.delete_dict_data_services`."""

    async def dict_data_detail_services(self, dict_code: int) -> Any:
        """Contract for `DictDataService.dict_data_detail_services`."""

    async def export_dict_data_list_services(self, dict_data_list: list) -> Any:
        """Contract for `DictDataService.export_dict_data_list_services`."""


@runtime_checkable
class IDictTypeService(IBaseService, Protocol):
    """Protocol contract for `DictTypeService`."""

    async def get_dict_type_list_services(self, query_object: Any, is_page: bool = False) -> Any:
        """Contract for `DictTypeService.get_dict_type_list_services`."""

    async def check_dict_type_unique_services(self, page_object: Any) -> Any:
        """Contract for `DictTypeService.check_dict_type_unique_services`."""

    async def add_dict_type_services(self, redis: Any, page_object: Any, operator: str | None = None) -> Any:
        """Contract for `DictTypeService.add_dict_type_services`."""

    async def edit_dict_type_services(self, redis: Any, page_object: Any, operator: str | None = None) -> Any:
        """Contract for `DictTypeService.edit_dict_type_services`."""

    async def delete_dict_type_services(self, redis: Any, page_object: Any) -> Any:
        """Contract for `DictTypeService.delete_dict_type_services`."""

    async def dict_type_detail_services(self, dict_id: int) -> Any:
        """Contract for `DictTypeService.dict_type_detail_services`."""

    async def export_dict_type_list_services(self, dict_type_list: list) -> Any:
        """Contract for `DictTypeService.export_dict_type_list_services`."""

    async def refresh_sys_dict_services(self, redis: Any) -> Any:
        """Contract for `DictTypeService.refresh_sys_dict_services`."""


@runtime_checkable
class IEventTriggerService(IBaseService, Protocol):
    """Protocol contract for `EventTriggerService`."""

    def set_action_executor(self, executor: Any) -> Any:
        """Contract for `EventTriggerService.set_action_executor`."""

    def add_event(self, session_id: str, event: dict) -> dict:
        """Contract for `EventTriggerService.add_event`."""

    def update_event(self, session_id: str, event_id: str, updates: dict) -> dict | None:
        """Contract for `EventTriggerService.update_event`."""

    def trigger_event(self, session_id: str, event_id: str) -> dict | None:
        """Contract for `EventTriggerService.trigger_event`."""

    def remove_event(self, session_id: str, event_id: str) -> bool:
        """Contract for `EventTriggerService.remove_event`."""

    def list_events(self, session_id: str) -> list[dict]:
        """Contract for `EventTriggerService.list_events`."""

    def get_event(self, session_id: str, event_id: str) -> dict | None:
        """Contract for `EventTriggerService.get_event`."""

    def evaluate(
        self,
        session_id: str,
        now: float,
        message_count: int,
        bandwidth_snapshot: list[dict],
        condition_matcher: Any | None = None,
        action_executor: Any | None = None,
    ) -> list[dict]:
        """Contract for `EventTriggerService.evaluate`."""

    def reset_event(self, session_id: str, event_id: str) -> bool:
        """Contract for `EventTriggerService.reset_event`."""

    def clear_session_events(self, session_id: str) -> Any:
        """Contract for `EventTriggerService.clear_session_events`."""


@runtime_checkable
class IGenTableColumnService(IBaseService, Protocol):
    """Protocol contract for `GenTableColumnService`."""

    async def get_gen_table_column_list_by_table_id_services(self, table_id: int) -> Any:
        """Contract for `GenTableColumnService.get_gen_table_column_list_by_table_id_services`."""


@runtime_checkable
class IGenTableService(IBaseService, Protocol):
    """Protocol contract for `GenTableService`."""

    async def get_gen_table_list_services(self, query_object: Any, is_page: bool = False) -> Any:
        """Contract for `GenTableService.get_gen_table_list_services`."""

    async def get_gen_db_table_list_services(self, query_object: Any, is_page: bool = False) -> Any:
        """Contract for `GenTableService.get_gen_db_table_list_services`."""

    async def get_gen_db_table_list_by_name_services(self, table_names: list[str]) -> Any:
        """Contract for `GenTableService.get_gen_db_table_list_by_name_services`."""

    async def import_gen_table_services(self, gen_table_list: list[Any], current_user: Any) -> Any:
        """Contract for `GenTableService.import_gen_table_services`."""

    async def edit_gen_table_services(self, page_object: Any) -> Any:
        """Contract for `GenTableService.edit_gen_table_services`."""

    async def delete_gen_table_services(self, page_object: Any) -> Any:
        """Contract for `GenTableService.delete_gen_table_services`."""

    async def get_gen_table_by_id_services(self, table_id: int) -> Any:
        """Contract for `GenTableService.get_gen_table_by_id_services`."""

    async def get_gen_table_all_services(self) -> Any:
        """Contract for `GenTableService.get_gen_table_all_services`."""

    async def create_table_services(self, sql: str, current_user: Any) -> Any:
        """Contract for `GenTableService.create_table_services`."""

    async def preview_code_services(self, table_id: int) -> Any:
        """Contract for `GenTableService.preview_code_services`."""

    async def generate_code_services(self, table_name: str) -> Any:
        """Contract for `GenTableService.generate_code_services`."""

    async def batch_gen_code_services(self, table_names: list[str]) -> Any:
        """Contract for `GenTableService.batch_gen_code_services`."""

    async def sync_db_services(self, table_name: str) -> Any:
        """Contract for `GenTableService.sync_db_services`."""

    async def set_sub_table(self, gen_table: Any) -> Any:
        """Contract for `GenTableService.set_sub_table`."""

    async def set_pk_column(self, gen_table: Any) -> Any:
        """Contract for `GenTableService.set_pk_column`."""

    async def set_table_from_options(self, gen_table: Any) -> Any:
        """Contract for `GenTableService.set_table_from_options`."""

    async def validate_edit(self, edit_gen_table: Any) -> Any:
        """Contract for `GenTableService.validate_edit`."""


@runtime_checkable
class IJobLogService(IBaseService, Protocol):
    """Protocol contract for `JobLogService`."""

    async def get_job_log_list_services(self, query_object: Any, is_page: bool = False) -> Any:
        """Contract for `JobLogService.get_job_log_list_services`."""

    async def add_job_log_services(self, page_object: Any) -> Any:
        """Contract for `JobLogService.add_job_log_services`."""

    async def delete_job_log_services(self, page_object: Any) -> Any:
        """Contract for `JobLogService.delete_job_log_services`."""

    async def clear_job_log_services(self) -> Any:
        """Contract for `JobLogService.clear_job_log_services`."""

    async def export_job_log_list_services(self, request: Any, job_log_list: list, dict_data_service: Any) -> Any:
        """Contract for `JobLogService.export_job_log_list_services`."""


@runtime_checkable
class IJobService(IBaseService, Protocol):
    """Protocol contract for `JobService`."""

    async def get_job_list_services(self, query_object: Any, is_page: bool = False) -> Any:
        """Contract for `JobService.get_job_list_services`."""

    async def check_job_unique_services(self, page_object: Any) -> Any:
        """Contract for `JobService.check_job_unique_services`."""

    async def add_job_services(self, page_object: Any) -> Any:
        """Contract for `JobService.add_job_services`."""

    async def edit_job_services(self, page_object: Any) -> Any:
        """Contract for `JobService.edit_job_services`."""

    async def execute_job_once_services(self, page_object: Any) -> Any:
        """Contract for `JobService.execute_job_once_services`."""

    async def delete_job_services(self, page_object: Any) -> Any:
        """Contract for `JobService.delete_job_services`."""

    async def job_detail_services(self, job_id: int) -> Any:
        """Contract for `JobService.job_detail_services`."""

    async def export_job_list_services(self, request: Any, job_list: list, dict_data_service: Any) -> Any:
        """Contract for `JobService.export_job_list_services`."""


@runtime_checkable
class ILoginLogService(IBaseService, Protocol):
    """Protocol contract for `LoginLogService`."""

    async def get_login_log_list_services(self, query_object: Any, is_page: bool = False) -> Any:
        """Contract for `LoginLogService.get_login_log_list_services`."""

    async def add_login_log_services(self, page_object: Any) -> Any:
        """Contract for `LoginLogService.add_login_log_services`."""

    async def delete_login_log_services(self, page_object: Any) -> Any:
        """Contract for `LoginLogService.delete_login_log_services`."""

    async def clear_login_log_services(self) -> Any:
        """Contract for `LoginLogService.clear_login_log_services`."""

    async def unlock_user_services(self, request: Any, unlock_user: Any) -> Any:
        """Contract for `LoginLogService.unlock_user_services`."""

    async def export_login_log_list_services(self, login_log_list: list) -> Any:
        """Contract for `LoginLogService.export_login_log_list_services`."""


@runtime_checkable
class ILoginService(IBaseService, Protocol):
    """Protocol contract for `LoginService`."""

    async def authenticate_user(self, request: Any, login_user: Any) -> Any:
        """Contract for `LoginService.authenticate_user`."""

    async def create_access_token(self, data: dict, expires_delta: Any | None = None) -> Any:
        """Contract for `LoginService.create_access_token`."""

    async def get_current_user(self, request: Any = None, token: str | None = None, query_db: Any = None) -> Any:
        """Contract for `LoginService.get_current_user`."""

    async def get_current_user_from_token(self, context: Any, token: str | None, query_db: Any) -> Any:
        """Contract for `LoginService.get_current_user_from_token`."""

    async def get_current_user_routers(self, user_id: int) -> Any:
        """Contract for `LoginService.get_current_user_routers`."""

    async def register_user_services(self, request: Any, user_register: Any, user_service: Any | None = None) -> Any:
        """Contract for `LoginService.register_user_services`."""

    async def get_sms_code_services(self, request: Any, user: Any) -> Any:
        """Contract for `LoginService.get_sms_code_services`."""

    async def forget_user_services(self, request: Any, forget_user: Any, user_service: Any | None = None) -> Any:
        """Contract for `LoginService.forget_user_services`."""

    async def logout_services(self, request: Any, session_id: str) -> Any:
        """Contract for `LoginService.logout_services`."""


@runtime_checkable
class IMenuService(IBaseService, Protocol):
    """Protocol contract for `MenuService`."""

    async def get_menu_tree_services(self, current_user: Any | None = None) -> Any:
        """Contract for `MenuService.get_menu_tree_services`."""

    async def get_role_menu_tree_services(self, role_id: int, current_user: Any | None = None) -> Any:
        """Contract for `MenuService.get_role_menu_tree_services`."""

    async def get_menu_list_services(self, page_object: Any, current_user: Any | None = None) -> Any:
        """Contract for `MenuService.get_menu_list_services`."""

    async def check_menu_name_unique_services(self, page_object: Any) -> Any:
        """Contract for `MenuService.check_menu_name_unique_services`."""

    async def add_menu_services(self, page_object: Any) -> Any:
        """Contract for `MenuService.add_menu_services`."""

    async def edit_menu_services(self, page_object: Any) -> Any:
        """Contract for `MenuService.edit_menu_services`."""

    async def delete_menu_services(self, page_object: Any) -> Any:
        """Contract for `MenuService.delete_menu_services`."""

    async def menu_detail_services(self, menu_id: int) -> Any:
        """Contract for `MenuService.menu_detail_services`."""

    def list_to_tree(self, permission_list: list) -> list:
        """Contract for `MenuService.list_to_tree`."""


@runtime_checkable
class INoticeService(IBaseService, Protocol):
    """Protocol contract for `NoticeService`."""

    async def get_notice_list_services(self, query_object: Any, is_page: bool = True) -> Any:
        """Contract for `NoticeService.get_notice_list_services`."""

    async def check_notice_unique_services(self, page_object: Any) -> Any:
        """Contract for `NoticeService.check_notice_unique_services`."""

    async def add_notice_services(self, page_object: Any) -> Any:
        """Contract for `NoticeService.add_notice_services`."""

    async def edit_notice_services(self, page_object: Any) -> Any:
        """Contract for `NoticeService.edit_notice_services`."""

    async def delete_notice_services(self, page_object: Any) -> Any:
        """Contract for `NoticeService.delete_notice_services`."""

    async def notice_detail_services(self, notice_id: int) -> Any:
        """Contract for `NoticeService.notice_detail_services`."""


@runtime_checkable
class IOnlineService(IBaseService, Protocol):
    """Protocol contract for `OnlineService`."""

    async def get_online_list_services(self, request: Any, query_object: Any) -> Any:
        """Contract for `OnlineService.get_online_list_services`."""

    async def delete_online_services(self, request: Any, page_object: Any) -> Any:
        """Contract for `OnlineService.delete_online_services`."""


@runtime_checkable
class IOperationLogService(IBaseService, Protocol):
    """Protocol contract for `OperationLogService`."""

    async def get_operation_log_list_services(self, query_object: Any, is_page: bool = False) -> Any:
        """Contract for `OperationLogService.get_operation_log_list_services`."""

    async def add_operation_log_services(self, page_object: Any) -> Any:
        """Contract for `OperationLogService.add_operation_log_services`."""

    async def delete_operation_log_services(self, page_object: Any) -> Any:
        """Contract for `OperationLogService.delete_operation_log_services`."""

    async def clear_operation_log_services(self) -> Any:
        """Contract for `OperationLogService.clear_operation_log_services`."""

    async def export_operation_log_list_services(
        self, request: Any, operation_log_list: list, dict_data_service: Any
    ) -> Any:
        """Contract for `OperationLogService.export_operation_log_list_services`."""


@runtime_checkable
class IPostService(IBaseService, Protocol):
    """Protocol contract for `PostService`."""

    async def get_post_list_services(self, query_object: Any, is_page: bool = False) -> Any:
        """Contract for `PostService.get_post_list_services`."""

    async def check_post_name_unique_services(self, page_object: Any) -> Any:
        """Contract for `PostService.check_post_name_unique_services`."""

    async def check_post_code_unique_services(self, page_object: Any) -> Any:
        """Contract for `PostService.check_post_code_unique_services`."""

    async def add_post_services(self, page_object: Any) -> Any:
        """Contract for `PostService.add_post_services`."""

    async def edit_post_services(self, page_object: Any) -> Any:
        """Contract for `PostService.edit_post_services`."""

    async def delete_post_services(self, page_object: Any) -> Any:
        """Contract for `PostService.delete_post_services`."""

    async def post_detail_services(self, post_id: int) -> Any:
        """Contract for `PostService.post_detail_services`."""

    async def export_post_list_services(self, post_list: list) -> Any:
        """Contract for `PostService.export_post_list_services`."""


@runtime_checkable
class IProjectService(IBaseService, Protocol):
    """Protocol contract for `ProjectService`."""

    async def get_project_list(self, query_object: Any, is_page: bool = False) -> Any:
        """Contract for `ProjectService.get_project_list`."""

    async def add_project(self, page_object: Any, operator: str | None = None) -> Any:
        """Contract for `ProjectService.add_project`."""

    async def edit_project(self, page_object: Any, operator: str | None = None) -> Any:
        """Contract for `ProjectService.edit_project`."""

    async def delete_project(self, page_object: Any, operator: str | None = None) -> Any:
        """Contract for `ProjectService.delete_project`."""

    async def get_project_detail(self, project_id: int) -> Any:
        """Contract for `ProjectService.get_project_detail`."""

    async def export_project_zip(self, project_id: int) -> Any:
        """Contract for `ProjectService.export_project_zip`."""

    async def export_projects_zip(self, project_ids: list[int]) -> Any:
        """Contract for `ProjectService.export_projects_zip`."""

    async def import_project(self, import_data: Any, operator: str) -> Any:
        """Contract for `ProjectService.import_project`."""

    async def import_projects_from_zip(self, file_bytes: bytes, operator: str) -> Any:
        """Contract for `ProjectService.import_projects_from_zip`."""

    async def get_project_list_services(self, query_object: Any, is_page: bool = False) -> Any:
        """Contract for `ProjectService.get_project_list_services`."""

    async def add_project_services(self, page_object: Any, operator: str | None = None) -> Any:
        """Contract for `ProjectService.add_project_services`."""

    async def edit_project_services(self, page_object: Any, operator: str | None = None) -> Any:
        """Contract for `ProjectService.edit_project_services`."""

    async def delete_project_services(self, page_object: Any, operator: str | None = None) -> Any:
        """Contract for `ProjectService.delete_project_services`."""

    async def project_detail_services(self, project_id: int) -> Any:
        """Contract for `ProjectService.project_detail_services`."""

    async def export_project_services(self, project_id: int) -> Any:
        """Contract for `ProjectService.export_project_services`."""

    async def export_project_zip_services(self, project_id: int) -> Any:
        """Contract for `ProjectService.export_project_zip_services`."""

    async def export_projects_zip_services(self, project_ids: list[int]) -> Any:
        """Contract for `ProjectService.export_projects_zip_services`."""

    async def import_project_services(self, import_data: Any, operator: str) -> Any:
        """Contract for `ProjectService.import_project_services`."""

    async def import_projects_from_zip_services(self, file_bytes: bytes, operator: str) -> Any:
        """Contract for `ProjectService.import_projects_from_zip_services`."""


@runtime_checkable
class IProjectTopologyService(IBaseService, Protocol):
    """Protocol contract for `ProjectTopologyService`."""

    async def save_project_topology(self, topology: Any, operator: str | None = None) -> Any:
        """Contract for `ProjectTopologyService.save_project_topology`."""

    async def get_project_topology(self, project_id: int, version_id: int | None = None) -> Any:
        """Contract for `ProjectTopologyService.get_project_topology`."""

    async def save_project_topology_services(self, topology: Any, operator: str | None = None) -> Any:
        """Contract for `ProjectTopologyService.save_project_topology_services`."""

    async def get_project_topology_services(self, project_id: int, version_id: int | None = None) -> Any:
        """Contract for `ProjectTopologyService.get_project_topology_services`."""


@runtime_checkable
class IProjectVersionService(IBaseService, Protocol):
    """Protocol contract for `ProjectVersionService`."""

    async def get_project_version_list_services(self, query_object: Any, is_page: bool = False) -> Any:
        """Contract for `ProjectVersionService.get_project_version_list_services`."""

    async def add_project_version_services(self, page_object: Any) -> Any:
        """Contract for `ProjectVersionService.add_project_version_services`."""

    async def edit_project_version_services(self, page_object: Any) -> Any:
        """Contract for `ProjectVersionService.edit_project_version_services`."""

    async def delete_project_version_services(self, page_object: Any) -> Any:
        """Contract for `ProjectVersionService.delete_project_version_services`."""

    async def project_version_detail_services(self, version_id: int) -> Any:
        """Contract for `ProjectVersionService.project_version_detail_services`."""

    async def clone_project_version_services(self, clone_object: Any) -> Any:
        """Contract for `ProjectVersionService.clone_project_version_services`."""

    async def lock_project_version_services(self, lock_object: Any) -> Any:
        """Contract for `ProjectVersionService.lock_project_version_services`."""

    async def unlock_project_versions_by_project_services(self, project_id: int, operator: str | None = None) -> Any:
        """Contract for `ProjectVersionService.unlock_project_versions_by_project_services`."""


@runtime_checkable
class IProtocolService(IBaseService, Protocol):
    """Protocol contract for `ProtocolService`."""

    async def get_protocol_list(self, query_object: Any, is_page: bool = False) -> Any:
        """Contract for `ProtocolService.get_protocol_list`."""

    async def add_protocol(self, page_object: Any, operator: str | None = None) -> Any:
        """Contract for `ProtocolService.add_protocol`."""

    async def edit_protocol(self, page_object: Any, operator: str | None = None) -> Any:
        """Contract for `ProtocolService.edit_protocol`."""

    async def delete_protocol(self, page_object: Any, operator: str | None = None) -> Any:
        """Contract for `ProtocolService.delete_protocol`."""

    async def delete_protocol_batch(self, protocol_ids: list[int], operator: str | None = None) -> Any:
        """Contract for `ProtocolService.delete_protocol_batch`."""

    async def get_protocol_detail(self, protocol_id: int) -> Any:
        """Contract for `ProtocolService.get_protocol_detail`."""

    async def get_protocol_list_services(self, query_object: Any, is_page: bool = False) -> Any:
        """Contract for `ProtocolService.get_protocol_list_services`."""

    async def add_protocol_services(self, page_object: Any, operator: str | None = None) -> Any:
        """Contract for `ProtocolService.add_protocol_services`."""

    async def edit_protocol_services(self, page_object: Any, operator: str | None = None) -> Any:
        """Contract for `ProtocolService.edit_protocol_services`."""

    async def delete_protocol_services(self, page_object: Any, operator: str | None = None) -> Any:
        """Contract for `ProtocolService.delete_protocol_services`."""

    async def delete_protocol_batch_services(self, protocol_ids: list[int], operator: str) -> dict[str, Any]:
        """Contract for `ProtocolService.delete_protocol_batch_services`."""

    async def protocol_detail_services(self, protocol_id: int) -> Any:
        """Contract for `ProtocolService.protocol_detail_services`."""

    async def export_protocol_config_services(self, protocol_id: int) -> Any:
        """Contract for `ProtocolService.export_protocol_config_services`."""

    async def get_protocol_import_template_services(
        self, protocol_type: str | None = None, protocolType: str | None = None, **kwargs: Any
    ) -> Any:
        """Contract for `ProtocolService.get_protocol_import_template_services`."""

    async def protocol_import_preview_services(self, file: Any) -> Any:
        """Contract for `ProtocolService.protocol_import_preview_services`."""

    async def import_protocol_services(self, file: Any, protocol_name: str | None, operator: str) -> Any:
        """Contract for `ProtocolService.import_protocol_services`."""

    async def import_protocol_batch_services(self, files: list[Any], operator: str) -> Any:
        """Contract for `ProtocolService.import_protocol_batch_services`."""

    def parse_1553b_message(self, message_data: dict[str, Any]) -> dict[str, Any]:
        """Contract for `ProtocolService.parse_1553b_message`."""

    def parse_can_frame(self, frame_data: dict[str, Any]) -> dict[str, Any]:
        """Contract for `ProtocolService.parse_can_frame`."""

    def parse_ethernet_packet(self, packet_data: dict[str, Any]) -> dict[str, Any]:
        """Contract for `ProtocolService.parse_ethernet_packet`."""


@runtime_checkable
class IRoleService(IBaseService, Protocol):
    """Protocol contract for `RoleService`."""

    async def get_role_select_option_services(self) -> Any:
        """Contract for `RoleService.get_role_select_option_services`."""

    async def get_role_dept_tree_services(self, role_id: int) -> Any:
        """Contract for `RoleService.get_role_dept_tree_services`."""

    async def get_role_list_services(self, query_object: Any, data_scope_sql: str, is_page: bool = False) -> Any:
        """Contract for `RoleService.get_role_list_services`."""

    async def check_role_allowed_services(self, check_role: Any) -> Any:
        """Contract for `RoleService.check_role_allowed_services`."""

    async def check_role_data_scope_services(self, role_ids: str, data_scope_sql: str) -> Any:
        """Contract for `RoleService.check_role_data_scope_services`."""

    async def check_role_name_unique_services(self, page_object: Any) -> Any:
        """Contract for `RoleService.check_role_name_unique_services`."""

    async def check_role_key_unique_services(self, page_object: Any) -> Any:
        """Contract for `RoleService.check_role_key_unique_services`."""

    async def add_role_services(self, page_object: Any) -> Any:
        """Contract for `RoleService.add_role_services`."""

    async def edit_role_services(self, page_object: Any) -> Any:
        """Contract for `RoleService.edit_role_services`."""

    async def role_datascope_services(self, page_object: Any) -> Any:
        """Contract for `RoleService.role_datascope_services`."""

    async def delete_role_services(self, page_object: Any) -> Any:
        """Contract for `RoleService.delete_role_services`."""

    async def role_detail_services(self, role_id: int) -> Any:
        """Contract for `RoleService.role_detail_services`."""

    async def export_role_list_services(self, role_list: list) -> Any:
        """Contract for `RoleService.export_role_list_services`."""

    async def get_role_user_allocated_list_services(self, page_object: Any, data_scope_sql: str, is_page: bool = False) -> Any:
        """Contract for `RoleService.get_role_user_allocated_list_services`."""

    async def get_role_user_unallocated_list_services(self, page_object: Any, data_scope_sql: str, is_page: bool = False) -> Any:
        """Contract for `RoleService.get_role_user_unallocated_list_services`."""


@runtime_checkable
class IServerService(IBaseService, Protocol):
    """Protocol contract for `ServerService`."""

    async def get_server_monitor_info(self) -> Any:
        """Contract for `ServerService.get_server_monitor_info`."""


@runtime_checkable
class ISimulationService(IBaseService, Protocol):
    """Protocol contract for `SimulationService`."""

    async def create_session(self, request: Any, operator: str | None = None) -> dict:
        """Contract for `SimulationService.create_session`."""

    async def start_session(self, session_id: str) -> Any:
        """Contract for `SimulationService.start_session`."""

    async def stop_session(self, session_id: str) -> Any:
        """Contract for `SimulationService.stop_session`."""

    async def export_simulation_data(self, request: Any) -> Any:
        """Contract for `SimulationService.export_simulation_data`."""

    async def pause_session(self, session_id: str) -> Any:
        """Contract for `SimulationService.pause_session`."""

    async def resume_session(self, session_id: str) -> Any:
        """Contract for `SimulationService.resume_session`."""

    async def get_shared_session_status(self, session_id: str) -> dict:
        """Contract for `SimulationService.get_shared_session_status`."""

    def get_realtime_messages(self, session_id: str, limit: int = 100) -> list[dict]:
        """Contract for `SimulationService.get_realtime_messages`."""

    def get_new_messages(self, session_id: str, limit: int = 20) -> list[dict]:
        """Contract for `SimulationService.get_new_messages`."""

    async def read_messages_with_fallback(self, session_id: str, limit: int = 100) -> list[dict]:
        """Contract for `SimulationService.read_messages_with_fallback`."""

    async def get_runtime_latest_events(self, session_id: str, stream: str, limit: int) -> list[dict]:
        """Contract for `SimulationService.get_runtime_latest_events`."""

    async def get_runtime_events_since(
        self, session_id: str, stream: str, offset: int, limit: int
    ) -> tuple[list[dict], int]:
        """Contract for `SimulationService.get_runtime_events_since`."""

    async def append_runtime_events(self, session_id: str, stream: str, events: list[dict]) -> Any:
        """Contract for `SimulationService.append_runtime_events`."""

    async def get_runtime_stream_size(self, session_id: str, stream: str) -> int:
        """Contract for `SimulationService.get_runtime_stream_size`."""

    def get_realtime_bandwidth(self, session_id: str, port_id: str | None = None) -> list[dict]:
        """Contract for `SimulationService.get_realtime_bandwidth`."""

    def get_new_bandwidth(self, session_id: str) -> list[dict]:
        """Contract for `SimulationService.get_new_bandwidth`."""

    async def read_bandwidth_with_fallback(
        self, session_id: str, port_id: str | None = None, limit: int = 400
    ) -> list[dict]:
        """Contract for `SimulationService.read_bandwidth_with_fallback`."""

    def get_realtime_alarms(self, session_id: str) -> list[dict]:
        """Contract for `SimulationService.get_realtime_alarms`."""

    def get_new_alarms(self, session_id: str) -> list[dict]:
        """Contract for `SimulationService.get_new_alarms`."""

    async def read_alarms_with_fallback(self, session_id: str, limit: int = 200) -> list[dict]:
        """Contract for `SimulationService.read_alarms_with_fallback`."""

    def get_new_fault_events(self, session_id: str, offset: int = 0) -> tuple[list[dict], int]:
        """Contract for `SimulationService.get_new_fault_events`."""

    async def set_speed(self, session_id: str, speed: float) -> Any:
        """Contract for `SimulationService.set_speed`."""

    async def claim_runtime_producer_owner(self, session_id: str, worker_id: str, ttl_seconds: int = 10) -> bool:
        """Contract for `SimulationService.claim_runtime_producer_owner`."""

    async def release_runtime_producer_owner(self, session_id: str, worker_id: str) -> Any:
        """Contract for `SimulationService.release_runtime_producer_owner`."""

    async def step_once(self, session_id: str) -> Any:
        """Contract for `SimulationService.step_once`."""

    async def set_duration(self, session_id: str, duration: float | None) -> Any:
        """Contract for `SimulationService.set_duration`."""

    def resolve_speed_input(self, payload: dict | None) -> float:
        """Contract for `SimulationService.resolve_speed_input`."""

    def resolve_duration_input(
        self,
        *,
        duration: float | None = None,
        payload: dict | None = None,
    ) -> float | None:
        """Contract for `SimulationService.resolve_duration_input`."""

    def build_fault_injection_request(
        self,
        *,
        session_id: str | None = None,
        fault_type: str | None = None,
        target_id: str | None = None,
        payload: dict | None = None,
        require_session_id: bool = False,
    ) -> dict:
        """Contract for `SimulationService.build_fault_injection_request`."""

    def require_session_id(self, session_id: str | None) -> str:
        """Contract for `SimulationService.require_session_id`."""

    def apply_fault_injection(
        self,
        *,
        session_id: str | None = None,
        fault_type: str | None = None,
        target_id: str | None = None,
        payload: dict | None = None,
        require_session_id: bool = False,
    ) -> dict:
        """Contract for `SimulationService.apply_fault_injection`."""

    def inject_fault(self, session_id: str, fault_type: str, target_id: str, params: dict | None = None) -> dict:
        """Contract for `SimulationService.inject_fault`."""

    def clear_fault(self, session_id: str, fault_id: str) -> Any:
        """Contract for `SimulationService.clear_fault`."""

    def clear_all_faults(self, session_id: str) -> Any:
        """Contract for `SimulationService.clear_all_faults`."""

    def list_faults(self, session_id: str) -> list[dict]:
        """Contract for `SimulationService.list_faults`."""

    def add_event(self, session_id: str, event: dict) -> dict:
        """Contract for `SimulationService.add_event`."""

    def update_event(self, session_id: str, event_id: str, updates: dict) -> dict:
        """Contract for `SimulationService.update_event`."""

    def trigger_event(self, session_id: str, event_id: str) -> dict:
        """Contract for `SimulationService.trigger_event`."""

    def reset_event(self, session_id: str, event_id: str) -> Any:
        """Contract for `SimulationService.reset_event`."""

    def remove_event(self, session_id: str, event_id: str) -> Any:
        """Contract for `SimulationService.remove_event`."""

    def list_events(self, session_id: str) -> list[dict]:
        """Contract for `SimulationService.list_events`."""

    def validate_topology(self, topology_data: dict) -> dict:
        """Contract for `SimulationService.validate_topology`."""

    async def stream_session_updates(
        self,
        session_id: str,
        *,
        has_connections: Any,
        broadcast: Any,
        worker_id: str,
        owner_ttl_seconds: int = 10,
    ) -> Any:
        """Contract for `SimulationService.stream_session_updates`."""

    async def get_shared_session_status_services(self, session_id: str) -> dict:
        """Contract for `SimulationService.get_shared_session_status_services`."""

    async def create_session_services(self, query_db: Any, request: Any, operator: str | None = None) -> dict:
        """Contract for `SimulationService.create_session_services`."""

    async def start_session_services(self, query_db: Any, session_id: str) -> Any:
        """Contract for `SimulationService.start_session_services`."""

    async def stop_session_services(self, query_db: Any, session_id: str) -> Any:
        """Contract for `SimulationService.stop_session_services`."""

    def get_session_status_services(self, session_id: str) -> dict:
        """Contract for `SimulationService.get_session_status_services`."""

    def get_realtime_messages_services(self, session_id: str, limit: int = 100) -> list[dict]:
        """Contract for `SimulationService.get_realtime_messages_services`."""

    def get_new_messages_services(self, session_id: str, limit: int = 20) -> list[dict]:
        """Contract for `SimulationService.get_new_messages_services`."""

    def get_realtime_bandwidth_services(self, session_id: str, port_id: str | None = None) -> list[dict]:
        """Contract for `SimulationService.get_realtime_bandwidth_services`."""

    def get_new_bandwidth_services(self, session_id: str) -> list[dict]:
        """Contract for `SimulationService.get_new_bandwidth_services`."""

    def get_realtime_alarms_services(self, session_id: str) -> list[dict]:
        """Contract for `SimulationService.get_realtime_alarms_services`."""

    def get_new_alarms_services(self, session_id: str) -> list[dict]:
        """Contract for `SimulationService.get_new_alarms_services`."""

    def get_new_fault_events_services(self, session_id: str, offset: int = 0) -> tuple[list[dict], int]:
        """Contract for `SimulationService.get_new_fault_events_services`."""

    async def append_runtime_events_services(self, session_id: str, stream: str, events: list[dict]) -> Any:
        """Contract for `SimulationService.append_runtime_events_services`."""

    async def get_runtime_events_since_services(
        self, session_id: str, stream: str, offset: int, limit: int
    ) -> tuple[list[dict], int]:
        """Contract for `SimulationService.get_runtime_events_since_services`."""

    async def get_runtime_latest_events_services(self, session_id: str, stream: str, limit: int) -> list[dict]:
        """Contract for `SimulationService.get_runtime_latest_events_services`."""

    async def get_runtime_stream_size_services(self, session_id: str, stream: str) -> int:
        """Contract for `SimulationService.get_runtime_stream_size_services`."""

    async def claim_runtime_producer_owner_services(
        self, session_id: str, worker_id: str, ttl_seconds: int = 10
    ) -> bool:
        """Contract for `SimulationService.claim_runtime_producer_owner_services`."""

    async def release_runtime_producer_owner_services(self, session_id: str, worker_id: str) -> Any:
        """Contract for `SimulationService.release_runtime_producer_owner_services`."""

    async def get_historical_messages_services(self, query_db: Any, query: Any) -> list[dict]:
        """Contract for `SimulationService.get_historical_messages_services`."""

    async def export_simulation_data_services(self, query_db: Any, export_request: Any) -> dict:
        """Contract for `SimulationService.export_simulation_data_services`."""

    async def pause_session_services(self, query_db: Any, session_id: str) -> Any:
        """Contract for `SimulationService.pause_session_services`."""

    async def resume_session_services(self, query_db: Any, session_id: str) -> Any:
        """Contract for `SimulationService.resume_session_services`."""

    async def set_speed_services(self, session_id: str, speed: float) -> Any:
        """Contract for `SimulationService.set_speed_services`."""

    async def step_once_services(self, session_id: str) -> Any:
        """Contract for `SimulationService.step_once_services`."""

    async def set_duration_services(self, session_id: str, duration: float | None) -> Any:
        """Contract for `SimulationService.set_duration_services`."""

    def build_fault_injection_request_services(
        self,
        *,
        session_id: str | None = None,
        fault_type: str | None = None,
        target_id: str | None = None,
        payload: dict | None = None,
        require_session_id: bool = False,
    ) -> dict:
        """Contract for `SimulationService.build_fault_injection_request_services`."""

    def inject_fault_services(
        self, session_id: str, fault_type: str, target_id: str, params: dict | None = None
    ) -> dict:
        """Contract for `SimulationService.inject_fault_services`."""

    def clear_fault_services(self, session_id: str, fault_id: str) -> Any:
        """Contract for `SimulationService.clear_fault_services`."""

    def clear_all_faults_services(self, session_id: str) -> Any:
        """Contract for `SimulationService.clear_all_faults_services`."""

    def list_faults_services(self, session_id: str) -> list[dict]:
        """Contract for `SimulationService.list_faults_services`."""

    def add_event_services(self, session_id: str, event: dict) -> dict:
        """Contract for `SimulationService.add_event_services`."""

    def update_event_services(self, session_id: str, event_id: str, updates: dict) -> dict:
        """Contract for `SimulationService.update_event_services`."""

    def trigger_event_services(self, session_id: str, event_id: str) -> dict:
        """Contract for `SimulationService.trigger_event_services`."""

    def reset_event_services(self, session_id: str, event_id: str) -> Any:
        """Contract for `SimulationService.reset_event_services`."""

    def remove_event_services(self, session_id: str, event_id: str) -> Any:
        """Contract for `SimulationService.remove_event_services`."""

    def list_events_services(self, session_id: str) -> list[dict]:
        """Contract for `SimulationService.list_events_services`."""

    def validate_topology_services(self, topology_data: dict) -> dict:
        """Contract for `SimulationService.validate_topology_services`."""


@runtime_checkable
class IUserService(IBaseService, Protocol):
    """Protocol contract for `UserService`."""

    async def get_user_list_services(
        self, query_db: Any, query_object: Any, data_scope_sql: str, is_page: bool = False
    ) -> Any:
        """Contract for `UserService.get_user_list_services`."""

    async def check_user_allowed_services(self, check_user: Any) -> Any:
        """Contract for `UserService.check_user_allowed_services`."""

    async def check_user_data_scope_services(self, query_db: Any, user_id: int, data_scope_sql: str) -> Any:
        """Contract for `UserService.check_user_data_scope_services`."""

    async def check_user_name_unique_services(self, query_db: Any, page_object: Any) -> Any:
        """Contract for `UserService.check_user_name_unique_services`."""

    async def check_phonenumber_unique_services(self, query_db: Any, page_object: Any) -> Any:
        """Contract for `UserService.check_phonenumber_unique_services`."""

    async def check_email_unique_services(self, query_db: Any, page_object: Any) -> Any:
        """Contract for `UserService.check_email_unique_services`."""

    async def check_id_card_unique_services(self, query_db: Any, page_object: Any) -> Any:
        """Contract for `UserService.check_id_card_unique_services`."""

    async def add_user_services(self, query_db: Any, page_object: Any) -> Any:
        """Contract for `UserService.add_user_services`."""

    async def edit_user_services(self, query_db: Any, page_object: Any) -> Any:
        """Contract for `UserService.edit_user_services`."""

    async def delete_user_services(self, query_db: Any, page_object: Any) -> Any:
        """Contract for `UserService.delete_user_services`."""

    async def user_detail_services(
        self,
        query_db: Any,
        user_id: int | str,
        posts: list | None = None,
        roles: list | None = None,
    ) -> Any:
        """Contract for `UserService.user_detail_services`."""

    async def user_profile_services(self, query_db: Any, user_id: int) -> Any:
        """Contract for `UserService.user_profile_services`."""

    async def reset_user_services(self, query_db: Any, page_object: Any) -> Any:
        """Contract for `UserService.reset_user_services`."""

    async def batch_import_user_services(
        self,
        request: Any,
        query_db: Any,
        file: Any,
        update_support: bool,
        current_user: Any,
        user_data_scope_sql: str,
        dept_data_scope_sql: str,
    ) -> Any:
        """Contract for `UserService.batch_import_user_services`."""

    async def get_user_import_template_services(self) -> Any:
        """Contract for `UserService.get_user_import_template_services`."""

    async def export_user_list_services(self, user_list: list) -> Any:
        """Contract for `UserService.export_user_list_services`."""

    async def get_user_role_allocated_list_services(self, query_db: Any, page_object: Any) -> Any:
        """Contract for `UserService.get_user_role_allocated_list_services`."""

    async def add_user_role_services(self, query_db: Any, page_object: Any) -> Any:
        """Contract for `UserService.add_user_role_services`."""

    async def delete_user_role_services(self, query_db: Any, page_object: Any) -> Any:
        """Contract for `UserService.delete_user_role_services`."""

    async def detail_user_role_services(self, query_db: Any, page_object: Any) -> Any:
        """Contract for `UserService.detail_user_role_services`."""


__all__ = [
    'IAuditLogService',
    'IBaseService',
    'ICacheService',
    'ICaptchaService',
    'ICommonService',
    'IConfigService',
    'IDataSourceService',
    'IDeptService',
    'IDeviceCategoryService',
    'IDeviceService',
    'IDictDataService',
    'IDictTypeService',
    'IEventTriggerService',
    'IGenTableColumnService',
    'IGenTableService',
    'IJobLogService',
    'IJobService',
    'ILoginLogService',
    'ILoginService',
    'IMenuService',
    'INoticeService',
    'IOnlineService',
    'IOperationLogService',
    'IPostService',
    'IProjectService',
    'IProjectTopologyService',
    'IProjectVersionService',
    'IProtocolService',
    'IRoleService',
    'IServerService',
    'ISimulationService',
    'IUserService',
]
