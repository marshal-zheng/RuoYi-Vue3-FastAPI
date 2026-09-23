# 业务浏览器路线覆盖清单

> 2026-09-23最终范围调整：用户明确不再要求设备、仿真、工程、监控和生成器的后续工作与验收。下表保留原始范围的静态盘点，相关路线不再作为本次待完成验收；既有检查结果保留，未验证分支不标通过。独立fixture已停止新增交互，N02–N06的准确截止状态见 [browser-fixture-coverage.md](browser-fixture-coverage.md)。

日期：2026-09-22 库存，2026-09-23 收尾更新。下表保留原始路线与节点数；状态依据实际浏览器证据回写，不从源码可达推导通过。

用户最新明确停止设备、仿真、工程、监控、生成器后续工作。当前验收范围为 **B01–B13 系统管理/登录资料页，以及 ZXUI 通用能力**。B14–B27及相关C/F条目仅保留已执行事实，不再作为待办，也不标整项通过。完整结论与历史证据限制见 [最终交付说明](completion-report.md)。

基准为 `migration-inventory.md` 的 **184 个 input / 68 文件、18 个原生 dialog / 16 文件**；input迁移分组来自 `input-migration.json`（root 145/64，generator UI 39/4）。合并后 **72 个唯一文件**。数字是迁移前源码节点数，不是当前可见控件数。生成SFC另验，不能加入184/18。

## 路由来源和边界

- `ruoyi-fastapi-frontend/src/router/index.js:37` 公共路由；`:109` 起权限动态路由；`src/router/history.ts` 确认real模式使用web history。本文route在开发服务对应 `http://localhost<route>`，不是离线hash路由。
- `ruoyi-fastapi-backend/capabilities/modules/platform.module.yaml` 是当前受管菜单单源；父子menu_id/path合成下表URL。`scripts/seed_data/menus.registry.yaml` 已明确废弃且为空；旧release managed-data、mock菜单不作为当前真实route证明。
- 隐藏详情route保留权限要求和ID参数。`meta.activeMenu`、barrel导出、全局注册、注释中的实例不构成页面可达证明。
- 本表不覆盖仿真目录，也不把共享Dag/协议模板因仿真消费而排除。

## 最少不重复页面集

B01–B27 是按当前源码可证明入口组织的27个route模板；同一组件只安排一条主覆盖路径，/project/operlog等别名不重复。多个子状态仍须逐个打开；这不是一次页面访问即可覆盖全部节点的承诺。C类需要先证明当前服务器菜单，否则fixture验证；F类直接安排独立fixture。

| ID | 路由/入口 | 操作覆盖 | 数据/权限前提 | input / dialog | 状态 |
| --- | --- | --- | --- | ---: | --- |
| B01 | /login | 用户名、动态密码显隐、验证码输入；只观察或使用既有合法会话流程 | 验证码开关决定第3个字段是否显示 | 3 / 0 | 已实测既有账号登录；验证码关闭分支未显示 |
| B02 | /register | 用户名、密码、确认密码、验证码；无须提交注册 | 公共路由；验证码与注册是否开放取决服务配置 | 4 / 0 | 已观察3个原生输入，未注册；[记录](browser/resumed/B02-register-observe.json) |
| B03 | /system/user | 检索用户名/手机号；新增/修改用户，校验、取消重开 | system:user权限；部门/岗位/角色/状态字典；编辑需既有用户 | 9 / 0 | 新增/编辑/导入、校验/焦点、九主题明暗通过；[矩阵](browser/business-nine-theme-matrix.json)，[窄屏真实组件](browser-fixture-coverage.md) |
| B04 | /user/profile | 基本资料、修改密码页签；点击头像打开裁剪弹框 | 已有登录账号及资料；裁剪预览可选本地图片，不提交修改 | 6 / 1 | 资料加载及3输入、密码页签观察、头像弹框通过；[记录](browser/resumed/B04-profile-inputs.json) |
| B05 | /system/role | 角色搜索；新增/修改；操作“数据权限” | system:role权限；数据权限需角色行及部门树 | 6 / 0 | 新增/必填、数据权限弹框已实测；[记录](browser/role-add-validation.json) |
| B06 | /system/role-auth/user/:roleId | 从角色操作“分配用户”进入；搜索；“添加用户”打开选择弹框 | 非管理员角色ID；已分配与未分配用户数据 | 4 / 1 | 分配/待分配用户接口与列表恢复，检索及弹框实测；[记录](browser/resumed/role-unassigned-fixed.json) |
| B07 | /system/menu | 搜索；新增/修改；分别切目录/菜单/按钮类型；打开图标选择 | system:menu权限；类型切换决定图标、组件路径、权限等条件字段 | 8 / 0 | 目录/菜单/按钮条件字段及图标浮层实测；[记录](browser/resumed/B07-menu-icon-popover-fixed.json) |
| B08 | /system/dept | 搜索；新增/修改部门 | system:dept权限；父部门树，编辑需部门行 | 5 / 0 | 新增/必填及字典状态实测；[记录](browser/dept-validation.json) |
| B09 | /system/post | 搜索；新增/修改岗位 | system:post权限；编辑需岗位行 | 4 / 0 | 新增/必填及字典状态实测；[记录](browser/post-validation.json) |
| B10 | /system/dict | 字典搜索；新增/修改字典类型 | system:dict权限；新增无需先有字典行 | 4 / 0 | 新增/必填及字典状态实测；[记录](browser/dict-type-validation.json) |
| B11 | /system/dict-data/index/:dictId | 点字典类型进入数据页；新增/修改字典数据 | 有效字典ID；编辑需字典数据行 | 5 / 1 | 数据表单/校验实测；[记录](browser/dict-data-validation.json) |
| B12 | /system/config | 搜索；新增/修改参数（包含两个textarea） | system:config权限；编辑需参数行 | 5 / 0 | 参数表单/textarea/校验、并发字典修复后Y/N恢复；[记录](browser/resumed/config-dict-fixed.json) |
| B13 | /system/notice | 搜索；新增/修改公告标题 | system:notice权限；富文本编辑不计入input184 | 2 / 0 | 公告标题/校验实测；[记录](browser/notice-validation.json) |
| B14 | /system/log/operlog | 操作日志检索 | monitor:operlog权限；空列表仍可检索；/project/operlog消费相同页面无需重复 | 1 / 0 | 用户停止后续验收；仅保留既有记录，不判整项通过 |
| B15 | /system/log/logininfor | 登录IP/账号搜索 | monitor:logininfor权限；无需制造登录记录 | 2 / 0 | 用户停止后续验收；仅保留既有记录，不判整项通过 |
| B16 | /system/log/audit | 审计检索条件 | monitor:audit权限；无需修改审计记录 | 2 / 0 | 用户停止后续验收；仅保留既有记录，不判整项通过 |
| B17 | /monitor/online | IP/用户搜索 | monitor:online权限；不要执行强退 | 2 / 0 | 用户停止后续验收；仅保留既有记录，不判整项通过 |
| B18 | /monitor/cacheList | 选择缓存名称，再点缓存键查看内容 | monitor:cache权限；至少一个既有缓存键，输入项为只读详情 | 3 / 0 | 用户停止后续验收；仅保留既有记录，不判整项通过 |
| B19 | /monitor/job | 新增/修改任务、调用目标；打开Cron生成器；行操作详情 | monitor:job权限；新增可查看表单，详情需任务行；不运行/新增任务 | 5 / 3 | 用户停止后续验收；仅保留既有记录，不判整项通过 |
| B20 | /monitor/job-log/index/:jobId | 任务操作“日志”进入；检索；日志行“详情” | 有效任务ID及至少一条日志；RightToolbar本页无columns，不能覆盖其弹框 | 1 / 1 | 用户停止后续验收；仅保留既有记录，不判整项通过 |
| B21 | /tool/build | 属性面板切文本/textarea/密码/数值/日期/上传/选择/级联等字段；图标选择；级联“添加选项”；复制/导出打开生成类型选择 | tool:build菜单；39个input是多个互斥配置状态，单次打开页面不等于39全部显示。RightPanel需覆盖prepend/append与原生number；导出选择dialog以检查生成产物 | 39 / 3 | 用户停止后续验收；仅保留既有记录，不判整项通过 |
| B22 | /tool/gen | 检索；“导入”列表检索；“创建”打开SQL输入 | tool:gen权限；导入需要可导入数据库表；只打开不执行建表 | 4 / 0 | 用户停止后续验收；仅保留既有记录，不判整项通过 |
| B23 | /tool/gen-edit/index/:tableId | 从生成列表“修改”进入；基本信息/字段信息/生成信息；输出路径append | 已有生成表记录及字段；字段行可编辑状态需打开对应页签 | 12 / 0 | 用户停止后续验收；仅保留既有记录，不判整项通过 |
| B24 | /project/project | “新增”工程弹框及备注 | project:project:add；只打开/校验/取消，无需创建工程 | 2 / 0 | 用户停止后续验收；仅保留既有记录，不判整项通过 |
| B25 | /project/project-detail/index/:projectId | 工程详情的版本页签；“新增版本”；既有版本“克隆” | 有效工程ID；克隆需版本行；项目列表详情按钮为入口。新版VersionExportDialog不等于孤立ExportDialog | 6 / 1 | 用户停止后续验收；仅保留既有记录，不判整项通过 |
| B26 | /project/topo/index/:projectId | 工程版本操作“拓扑设计”；左侧设备搜索 | 有效工程/版本上下文；设备候选可为空，但拖拽/节点操作需既有设备。矩阵弹框消费已注释，不计覆盖 | 1 / 0 | 用户停止后续验收；仅保留既有记录，不判整项通过 |
| B27 | /device/detail/index/:deviceId? | 设备详情“添加端口”；端口备注；端口配置的LAN参数、报文配置；设备节点右键“编辑设备信息”打开命名；保存会直接提交；按CAN/RS422/LAN/1553B切四模板并编辑字段单元格 | 静态动态路由，受device:list:query权限；可无ID创建本地画布状态。ParamsConfigTab输入仅LAN显示；四种端口类型都要实际进入；VXE DictAutocomplete要激活字典单元格，不只看表格 | 9 / 0 | 用户停止后续验收；仅保留既有记录，不判整项通过 |
| C01 | 未在当前路由/菜单声明定位到；页面src/views/device/category/index.vue | 分类“新增/修改”→CategoryFormDialog | 查证服务器自定义菜单后才可记生产route；否则用此页面/组件fixture | 2 / 0 | 用户停止后续验收；仅保留既有记录，不判整项通过 |
| C02 | 未在当前路由/菜单声明定位到；页面src/views/device/index.vue | 设备行“克隆”→DeviceCloneDialog | 需要设备行；不能把meta.activeMenu=/device/list当路由注册 | 1 / 0 | 用户停止后续验收；仅保留既有记录，不判整项通过 |
| C03 | 未在当前路由/菜单声明定位到；页面src/views/protocol/index.vue | 协议“新增/修改”→ProtocolFormDrawer | 协议列表/协议类型；模板可由B27覆盖，但此Drawer自身不能借此计通过 | 2 / 0 | 用户停止后续验收；仅保留既有记录，不判整项通过 |
| C04 | 未在当前路由/菜单声明定位到；页面src/views/system/project/index.vue | 旧工程页面“新增/修改”→ProjectDlg；行“详情”→ProjectList内dialog | 这是旧system/project页面，不是B24的project/index；需独立fixture或已验证的自定义菜单 | 1 / 1 | 用户停止后续验收；仅保留既有记录，不判整项通过 |
| F01 | 独立fixture | 只经DagMatrixDialog消费；Dag/index.vue的实例和import均注释。fixture需矩阵数据并打开关系配置弹框 | 不得登记为真实页面通过；静态门禁仍覆盖 | 3 / 1 | 用户停止后续验收；仅保留既有记录，不判整项通过 |
| F02 | 独立fixture | 未发现实例消费；fixture需矩阵数据并打开关系配置弹框 | 不得登记为真实页面通过；静态门禁仍覆盖 | 3 / 1 | 用户停止后续验收；仅保留既有记录，不判整项通过 |
| F03 | 独立fixture | 未发现import或模板消费；fixture验证prefix与输入搜索 | 不得登记为真实页面通过；静态门禁仍覆盖 | 1 / 0 | 用户停止后续验收；仅保留既有记录，不判整项通过 |
| F04 | 独立fixture | 仅Device/index.ts导出；fixture打开分类表单 | 不得登记为真实页面通过；静态门禁仍覆盖 | 2 / 0 | 用户停止后续验收；仅保留既有记录，不判整项通过 |
| F05 | 独立fixture | 仅Device/index.ts导出；fixture提供导出列表与model/open；不能等同设备页下载 | 不得登记为真实页面通过；静态门禁仍覆盖 | 1 / 1 | 用户停止后续验收；仅保留既有记录，不判整项通过 |
| F06 | 独立fixture | 仅Device/index.ts导出；topo用的是views/project/components/NodeEditDrawer，不是本文件 | 不得登记为真实页面通过；静态门禁仍覆盖 | 6 / 0 | 用户停止后续验收；仅保留既有记录，不判整项通过 |
| F07 | 独立fixture | 仅project/components/index.ts导出；VersionList实际用VersionExportDialog，不是本文件 | 不得登记为真实页面通过；静态门禁仍覆盖 | 1 / 1 | 用户停止后续验收；仅保留既有记录，不判整项通过 |
| F08 | 独立fixture | 仅barrel导出；工程页编辑通过路由/其他入口，未消费此组件 | 不得登记为真实页面通过；静态门禁仍覆盖 | 2 / 0 | 用户停止后续验收；仅保留既有记录，不判整项通过 |
| F09 | 独立fixture | 仅barrel导出；fixture提供协议配置数据并打开 | 不得登记为真实页面通过；静态门禁仍覆盖 | 3 / 0 | 用户停止后续验收；仅保留既有记录，不判整项通过 |
| F10 | 独立fixture | 仅ui/index.ts导出；示例未有生产route，fixture覆盖text/password | 不得登记为真实页面通过；静态门禁仍覆盖 | 2 / 0 | 真实组件fixture已实测；[记录](browser-fixture-coverage.md) |
| F11 | 独立fixture | main.ts全局注册但未找到模板消费；fixture以现有图片URL触发预览dialog，无需上传文件 | 不得登记为真实页面通过；静态门禁仍覆盖 | 0 / 1 | 真实组件fixture已实测；[记录](browser-fixture-coverage.md) |
| F12 | 独立fixture | job/log虽挂载组件，但未传columns且默认checkbox；transfer弹框需fixture传columns与showColumnsType=transfer后点击显隐列 | 不得登记为真实页面通过；静态门禁仍覆盖 | 0 / 1 | 用户停止后续验收；仅保留既有记录，不判整项通过 |

## 72个文件逐项对照

以下路径相对 `ruoyi-fastapi-frontend/`。I/D为原迁移节点数。每行都指向上面的路线/fixture；未从任一文件的源码存在推导运行时通过。

| 文件 | I | D | 路线 |
| --- | ---: | ---: | --- |
| `src/views/login.vue` | 3 | 0 | B01 |
| `src/views/register.vue` | 4 | 0 | B02 |
| `src/views/system/user/index.vue` | 3 | 0 | B03 |
| `src/views/system/user/components/UserFormDialog.vue` | 6 | 0 | B03 |
| `src/views/system/user/profile/userInfo.vue` | 3 | 0 | B04 |
| `src/views/system/user/profile/resetPwd.vue` | 3 | 0 | B04 |
| `src/views/system/user/profile/userAvatar.vue` | 0 | 1 | B04 |
| `src/views/system/role/index.vue` | 1 | 0 | B05 |
| `src/views/system/role/components/RoleFormDrawer.vue` | 3 | 0 | B05 |
| `src/views/system/role/components/RoleDataScopeDrawer.vue` | 2 | 0 | B05 |
| `src/views/system/role/authUser.vue` | 2 | 0 | B06 |
| `src/views/system/role/selectUser.vue` | 2 | 1 | B06 |
| `src/views/system/menu/components/MenuList.vue` | 1 | 0 | B07 |
| `src/views/system/menu/components/MenuDrawer.vue` | 6 | 0 | B07 |
| `src/components/ui/IconSelect/index.vue` | 1 | 0 | B07 |
| `src/views/system/dept/components/DeptList.vue` | 1 | 0 | B08 |
| `src/views/system/dept/components/DeptDlg.vue` | 4 | 0 | B08 |
| `src/views/system/post/components/PostList.vue` | 1 | 0 | B09 |
| `src/views/system/post/components/PostDlg.vue` | 3 | 0 | B09 |
| `src/views/system/dict/components/DictList.vue` | 1 | 0 | B10 |
| `src/views/system/dict/components/DictDlg.vue` | 3 | 0 | B10 |
| `src/views/system/dict/data.vue` | 5 | 1 | B11 |
| `src/views/system/config/components/ConfigList.vue` | 1 | 0 | B12 |
| `src/views/system/config/components/ConfigDlg.vue` | 4 | 0 | B12 |
| `src/views/system/notice/components/NoticeList.vue` | 1 | 0 | B13 |
| `src/views/system/notice/components/NoticeDlg.vue` | 1 | 0 | B13 |
| `src/components/business/Monitor/OperlogGrid.vue` | 1 | 0 | B14 |
| `src/views/monitor/logininfor/index.vue` | 2 | 0 | B15 |
| `src/views/monitor/audit/index.vue` | 2 | 0 | B16 |
| `src/views/monitor/online/index.vue` | 2 | 0 | B17 |
| `src/views/monitor/cache/list.vue` | 3 | 0 | B18 |
| `src/views/monitor/job/index.vue` | 5 | 3 | B19 |
| `src/views/monitor/job/log.vue` | 1 | 1 | B20 |
| `src/views/tool/build/RightPanel.vue` | 35 | 0 | B21 |
| `src/views/tool/build/CodeTypeDialog.vue` | 1 | 1 | B21 |
| `src/views/tool/build/IconsDialog.vue` | 1 | 1 | B21 |
| `src/views/tool/build/TreeNodeDialog.vue` | 2 | 1 | B21 |
| `src/views/tool/gen/index.vue` | 1 | 0 | B22 |
| `src/views/tool/gen/importTable.vue` | 2 | 0 | B22 |
| `src/views/tool/gen/createTable.vue` | 1 | 0 | B22 |
| `src/views/tool/gen/editTable.vue` | 2 | 0 | B23 |
| `src/views/tool/gen/basicInfoForm.vue` | 5 | 0 | B23 |
| `src/views/tool/gen/genInfoForm.vue` | 5 | 0 | B23 |
| `src/views/project/components/ProjectFormDialog.vue` | 2 | 0 | B24 |
| `src/views/project/components/VersionList.vue` | 3 | 1 | B25 |
| `src/views/project/components/VersionCloneDialog.vue` | 3 | 0 | B25 |
| `src/components/business/Dag/components/DagDnd.vue` | 1 | 0 | B26 |
| `src/components/business/Device/DeviceNameDialog.vue` | 2 | 0 | B27 |
| `src/components/business/Device/PortEditDialog.vue` | 1 | 0 | B27 |
| `src/components/business/Device/ParamsConfigTab.vue` | 1 | 0 | B27 |
| `src/components/business/Protocol/templates/CANProtocolTemplate.vue` | 1 | 0 | B27 |
| `src/components/business/Protocol/templates/EthernetProtocolTemplate.vue` | 1 | 0 | B27 |
| `src/components/business/Protocol/templates/Protocol1553BTemplate.vue` | 1 | 0 | B27 |
| `src/components/business/Protocol/templates/RS422ProtocolTemplate.vue` | 1 | 0 | B27 |
| `src/components/business/VxeDictAutocomplete/index.vue` | 1 | 0 | B27 |
| `src/components/business/Device/CategoryFormDialog.vue` | 2 | 0 | C01 |
| `src/components/business/Device/DeviceCloneDialog.vue` | 1 | 0 | C02 |
| `src/components/business/Protocol/ProtocolFormDrawer.vue` | 2 | 0 | C03 |
| `src/views/system/project/components/ProjectDlg.vue` | 1 | 0 | C04 |
| `src/views/system/project/components/ProjectList.vue` | 0 | 1 | C04 |
| `src/components/business/Dag/components/DagMatrixView.vue` | 3 | 1 | F01 |
| `src/components/business/Dag/components/DagMatrixViewSimple.vue` | 3 | 1 | F02 |
| `src/components/business/Dag/components/DagSearchInput.vue` | 1 | 0 | F03 |
| `src/components/business/Device/DeviceClazzDialog.vue` | 2 | 0 | F04 |
| `src/components/business/Device/ExportDialog.vue` | 1 | 1 | F05 |
| `src/components/business/Device/NodeEditDrawer.vue` | 6 | 0 | F06 |
| `src/views/project/components/ExportDialog.vue` | 1 | 1 | F07 |
| `src/views/project/components/ProjectEditDialog.vue` | 2 | 0 | F08 |
| `src/views/project/components/ProtocolConfigDrawer.vue` | 3 | 0 | F09 |
| `src/components/ui/ThemeValidation/index.vue` | 2 | 0 | F10 |
| `src/components/ui/ImageUpload/index.vue` | 0 | 1 | F11 |
| `src/components/ui/RightToolbar/index.vue` | 0 | 1 | F12 |

## 引用链复核证据

- B04：`src/views/system/user/profile/index.vue` 消费userInfo/resetPwd/userAvatar；头像裁剪与通用ImageUpload是不同组件。
- B06/B11/B20/B23：`src/router/index.js` 明确声明role-auth、dict-data、job-log和gen-edit带ID路由。
- B07：`src/views/system/menu/components/MenuDrawer.vue` 消费IconSelect；需切换菜单类型才能显示所有条件字段。
- B14：`src/views/monitor/operlog/index.vue` 消费Monitor/OperlogGrid；两个菜单共用相同页面。
- B21：`src/views/tool/build/index.vue:90` RightPanel、`:93` CodeTypeDialog；`RightPanel.vue:474` IconsDialog，TreeNodeDialog通过级联选项操作打开。`utils/generator/html.ts/js.ts` 是输出源头，和页面组件分开记录。
- B24/B25：`src/views/project/index.vue:263` ProjectFormDialog；`src/views/project/detail.vue:21` VersionList；`VersionList.vue:197` VersionCloneDialog。
- B26：`src/views/project/topo.vue:44` Dag/index；Dag/index的DagDnd有实例，`:131` 的DagMatrixDialog在HTML注释中且import也注释。
- B27：`src/router/index.js:184` device/detail；`src/views/device/detail.vue:31` PortEditDialog、`:37` PortConfigDrawer、`:43` DeviceNameDialog；PortConfigDrawer的ParamsConfigTab/MessageConfigTab分别提供参数和协议模板。`MessageConfigTab.vue` 的类型映射覆盖CAN/RS422/RS485/LAN/1553B，RS485复用RS422。
- VXE：四协议模板使用`DictAutocomplete` renderer；`src/plugins/vxe-table.ts:41` 注册，`:79`实例化VxeDictAutocomplete。必须点击单元格进入编辑态才能覆盖动态inputType。
- C01–C04：相应页面有组件实例，但当前`platform.module.yaml`与`router/index.js`未登记这四个页面组件；不能使用URL猜测证明生产可达。
- F12：`src/components/ui/RightToolbar/index.vue:16`要求columns；`:17`还要求transfer；唯一非注释消费`src/views/monitor/job/log.vue:100`未提供这些props。

## 生成产物与验证记录

`tests/generator-form-runtime.test.ts`将真实`makeUpHtml + makeUpJs`产物交给同一检查核心，再用Vue SFC编译器转换并挂载真实公开ZxDialog/ZxInput、原生ElForm与业务FormGrid/useFormDialog。验证普通输入、原生number、prepend/append、整行textarea、打开、required校验、resetFields以及确认回传/关闭。该JSDOM证据不替代B21实际页面和浏览器尺寸/主题验收。

2026-09-23：生成器/门禁/真实生成SFC运行回归3文件15测试通过。C/F的独立浏览器fixture和G01生成产物实际交互已执行，详见 [browser-fixture-coverage.md](browser-fixture-coverage.md)；其证据不将本表B路线或C类未知生产route标为通过。

## 当前范围的证据解释

B01–B13的“已实测”只覆盖上表和原始DOM/截图中的操作，不表示创建账号、修改密码、批量删除或全部权限组合。密码/注册仅观察，不设置新凭据。真实用户窄屏使用同一业务SFC的fixture补充：640×700与390×630，单列、内部滚动、焦点恢复通过，不冒称整个业务shell移动端全覆盖。

原始主题基线与最终工厂蓝深色表单的背景/label计算色一致，radio从0恢复2；但原图1124×1000与新图1280×720且旧DOM未保留viewport，因此R9.AC3严格“同视口前后对照”证据仍不完整，未伪造补拍。
