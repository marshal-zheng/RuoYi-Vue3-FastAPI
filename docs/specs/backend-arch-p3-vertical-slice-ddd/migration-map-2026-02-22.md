# P3 迁移映射表（2026-02-22）

## 说明

- 目标：记录旧路径到新路径映射，支撑 Task6 一次性迁移与回归验收。
- 范围：本轮 `system/identity/project` 上下文。
- 策略：按上下文切换并删除旧实现，不保留兼容类代码。

## 文件级映射

| 状态 | 旧路径 | 新路径 | 说明 |
|---|---|---|---|
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/service/config_service.py` | `ruoyi-fastapi-backend/modules/system/application/services/config_service.py` | 参数服务迁移到 system 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/service/dept_service.py` | `ruoyi-fastapi-backend/modules/system/application/services/dept_service.py` | 部门服务迁移到 system 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/service/dict_service.py` | `ruoyi-fastapi-backend/modules/system/application/services/{dict_type_service.py,dict_data_service.py}` | 字典服务拆分迁移 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/service/menu_service.py` | `ruoyi-fastapi-backend/modules/system/application/services/menu_service.py` | 菜单服务迁移到 system 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/service/notice_service.py` | `ruoyi-fastapi-backend/modules/system/application/services/notice_service.py` | 通知服务迁移到 system 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/service/post_service.py` | `ruoyi-fastapi-backend/modules/system/application/services/post_service.py` | 岗位服务迁移到 system 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/service/role_service.py` | `ruoyi-fastapi-backend/modules/system/application/services/role_service.py` | 角色服务迁移到 system 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/service/user_service.py` | `ruoyi-fastapi-backend/modules/system/application/services/user_service.py` | 用户服务迁移到 system 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/service/audit_log_service.py` | `ruoyi-fastapi-backend/modules/system/application/services/audit_log_service.py` | 审计日志服务迁移到 system 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/service/cache_service.py` | `ruoyi-fastapi-backend/modules/system/application/services/cache_service.py` | 缓存监控服务迁移到 system 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/service/common_service.py` | `ruoyi-fastapi-backend/modules/system/application/services/common_service.py` | 通用服务迁移到 system 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/service/log_service.py` | `ruoyi-fastapi-backend/modules/system/application/services/log_service.py` | 登录/操作日志服务迁移到 system 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/service/online_service.py` | `ruoyi-fastapi-backend/modules/system/application/services/online_service.py` | 在线用户服务迁移到 system 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/service/server_service.py` | `ruoyi-fastapi-backend/modules/system/application/services/server_service.py` | 服务器监控服务迁移到 system 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/repository/config_repository.py` | `ruoyi-fastapi-backend/modules/system/infrastructure/config_repository.py` | 参数仓储迁移到 system 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/repository/dept_repository.py` | `ruoyi-fastapi-backend/modules/system/infrastructure/dept_repository.py` | 部门仓储迁移到 system 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/repository/dict_repository.py` | `ruoyi-fastapi-backend/modules/system/infrastructure/dict_repository.py` | 字典仓储迁移到 system 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/repository/menu_repository.py` | `ruoyi-fastapi-backend/modules/system/infrastructure/menu_repository.py` | 菜单仓储迁移到 system 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/repository/notice_repository.py` | `ruoyi-fastapi-backend/modules/system/infrastructure/notice_repository.py` | 通知仓储迁移到 system 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/repository/post_repository.py` | `ruoyi-fastapi-backend/modules/system/infrastructure/post_repository.py` | 岗位仓储迁移到 system 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/repository/role_repository.py::RoleRepository` | `ruoyi-fastapi-backend/modules/system/infrastructure/role_repository.py` | 角色仓储主实现迁移 |
| 已迁移 | `ruoyi-fastapi-backend/module_admin/repository/role_repository.py::RoleMenuRepository` | `ruoyi-fastapi-backend/modules/system/infrastructure/role_menu_repository.py` | 角色-菜单关联仓储拆分 |
| 已迁移 | `ruoyi-fastapi-backend/module_admin/repository/role_repository.py::RoleDeptRepository` | `ruoyi-fastapi-backend/modules/system/infrastructure/role_dept_repository.py` | 角色-部门关联仓储拆分 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/repository/user_repository.py::UserRepository` | `ruoyi-fastapi-backend/modules/system/infrastructure/user_repository.py` | 用户仓储主实现迁移 |
| 已迁移 | `ruoyi-fastapi-backend/module_admin/repository/user_repository.py::UserRoleRepository` | `ruoyi-fastapi-backend/modules/system/infrastructure/user_role_repository.py` | 用户-角色关联仓储拆分 |
| 已迁移 | `ruoyi-fastapi-backend/module_admin/repository/user_repository.py::UserPostRepository` | `ruoyi-fastapi-backend/modules/system/infrastructure/user_post_repository.py` | 用户-岗位关联仓储拆分 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/repository/audit_log_repository.py` | `ruoyi-fastapi-backend/modules/system/infrastructure/audit_log_repository.py` | 审计日志仓储迁移到 system 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/repository/common_repository.py` | `ruoyi-fastapi-backend/modules/system/infrastructure/common_repository.py` | 通用仓储迁移到 system 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/repository/log_repository.py` | `ruoyi-fastapi-backend/modules/system/infrastructure/log_repository.py` | 登录/操作日志仓储迁移到 system 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/controller/{config,dept,dict,menu,notice,post,role,user}_controller.py` | `ruoyi-fastapi-backend/modules/system/api/{config,dept,dict,menu,notice,post,role,user}_controller.py` | 系统管理 API 迁移 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/controller/{audit,cache,common,log,online,resilience,server}_controller.py` | `ruoyi-fastapi-backend/modules/system/api/{audit,cache,common,log,online,resilience,server}_controller.py` | 系统监控/通用 API 迁移 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/service/login_service.py` | `ruoyi-fastapi-backend/modules/identity/application/services/login_service.py` | 登录鉴权服务迁移到 identity 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/service/captcha_service.py` | `ruoyi-fastapi-backend/modules/identity/application/services/captcha_service.py` | 验证码服务迁移到 identity 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/repository/login_repository.py` | `ruoyi-fastapi-backend/modules/identity/infrastructure/login_repository.py` | 登录仓储迁移到 identity 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/controller/login_controller.py` | `ruoyi-fastapi-backend/modules/identity/api/login_controller.py` | 登录 API 迁移到 identity 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/controller/captcha_controller.py` | `ruoyi-fastapi-backend/modules/identity/api/captcha_controller.py` | 验证码 API 迁移到 identity 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/service/project_service.py` | `ruoyi-fastapi-backend/modules/project/application/services/project_service.py` | 工程服务迁移到 project 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/service/project_topology_service.py` | `ruoyi-fastapi-backend/modules/project/application/services/project_topology_service.py` | 工程拓扑服务迁移到 project 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/service/project_version_service.py` | `ruoyi-fastapi-backend/modules/project/application/services/project_version_service.py` | 工程版本服务迁移到 project 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/repository/project_repository.py` | `ruoyi-fastapi-backend/modules/project/infrastructure/project_repository.py` | 工程仓储迁移到 project 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/repository/project_topology_repository.py` | `ruoyi-fastapi-backend/modules/project/infrastructure/project_topology_repository.py` | 工程拓扑仓储迁移到 project 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/repository/project_version_repository.py` | `ruoyi-fastapi-backend/modules/project/infrastructure/project_version_repository.py` | 工程版本仓储迁移到 project 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/controller/project_controller.py` | `ruoyi-fastapi-backend/modules/project/api/project_controller.py` | 工程 API 迁移到 project 上下文 |
| 已迁移并删除旧文件 | `ruoyi-fastapi-backend/module_admin/controller/project_version_controller.py` | `ruoyi-fastapi-backend/modules/project/api/project_version_controller.py` | 工程版本 API 迁移到 project 上下文 |

## 导出与装配调整

- `ruoyi-fastapi-backend/modules/registry.py` 已切换 `system/identity/project` 路由来源到 `modules/*/api/*_controller.py`。
- `ruoyi-fastapi-backend/container/providers.py` 已切换到 `modules/*/application/services` 与 `modules/*/infrastructure` 直连装配，并补充 `modules` 服务目录自动发现。
- `ruoyi-fastapi-backend/module_admin/repository/__init__.py` 已改为导出 `system/identity/project` 新仓储实现。
- `ruoyi-fastapi-backend/modules/identity/ports.py` 已提供 `get_current_user` 端口，`system/project` 对身份依赖已通过 `ports` 访问，满足边界门禁。
- `ruoyi-fastapi-backend/module_admin/controller/` 现仅保留非本轮范围控制器：`device_category/device/job/protocol/simulation`。
- `ruoyi-fastapi-backend/module_admin/service/` 现仅保留非本轮范围服务：`device/protocol/simulation/scheduler` 相关。
- `ruoyi-fastapi-backend/module_admin/repository/` 现仅保留非本轮范围仓储与基础抽象。

## 后续批次建议

1. 按同一策略推进 `simulation/protocol/device`，完成旧实现删除收口。
2. 评估 `scheduler/codegen` 是否并入独立上下文切换批次，避免与系统域耦合回流。
