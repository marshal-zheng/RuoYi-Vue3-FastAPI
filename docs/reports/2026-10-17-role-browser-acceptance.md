# 角色管理与双向授权浏览器验收

本轮补齐真实浏览器视觉和交互验收，发现并修复四类问题，相关回归及独立复审通过。源起点为 `std@fe5081897704dc4bff1cfff5fbdc06ea357f7af5`，候选工作树为项目内 `.worktrees/role-browser-acceptance`；仅纳入本轮 8 个产品/测试文件与报告证据。

## 浏览器与真实业务链路

使用可见 Chromium，覆盖 `1440×1000` 和 `1024×768` 桌面视口。前端为实际源 Vite / 80，`VITE_ZXUI_LOCAL=true`、`VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus`；后端为实际源 `app.py --env=dev` / 8088，连接已有 Docker MySQL 和 Redis。没有以 jsdom 或直接修改页面业务状态代替浏览器交互。

分页数据准备使用本轮命名空间 `bqa171407`：10 个角色与 11 个用户通过真实 API 准备，另 2 个角色由界面创建。所有授权、撤销、编辑、筛选、导出、删除和保存重开均通过真实点击或键盘完成；API/只读 SQL 用于独立核对结果。未向现有用户授予本轮角色。

| 验收项 | 交互结果 | 已审阅视觉证据 |
| --- | --- | --- |
| 角色列表 | 筛选、权限字符 Enter、日期、状态、无结果恢复、分页、返回页码、选中修改、导出均通过 | [宽屏列表](evidence/2026-10-17-role-browser-acceptance/28-role-list-1440-final.jpg)、[小桌面列表](evidence/2026-10-17-role-browser-acceptance/29-role-list-1024-final.jpg) |
| 角色编辑 | 必填校验、菜单展开/折叠与全选/全不选、菜单勾选保存重开、停用详情、备注保存、全屏往返、关闭/取消通过 | [小桌面编辑](evidence/2026-10-17-role-browser-acceptance/30-role-form-1024-final.jpg)、[菜单持久化](evidence/2026-10-17-role-browser-acceptance/34-menu-permission-persisted.jpg) |
| 状态与数据范围 | 取消停用不变、停用/恢复正常；全部/自定义/本部门/本部门及以下/仅本人五种模式保存重开通过，自定义部门勾选保留 | [其他模式](evidence/2026-10-17-role-browser-acceptance/35-data-scope-other-modes.jpg)；[自定义部门](evidence/2026-10-17-role-browser-acceptance/17-data-scope-1024.jpg) |
| 角色侧用户授权 | 11 条跨页勾选、取消、搜索保留、保存、重开清零、全选、单条撤销取消/确认、批量撤销均通过 | [全选和时间列](evidence/2026-10-17-role-browser-acceptance/24-select-all-1024.jpg)、[批量确认](evidence/2026-10-17-role-browser-acceptance/25-batch-revoke-confirm-1024.jpg) |
| 用户侧角色授权 | 已关联停用角色可见，取消后跨页不被旧 flag 勾回；完整替换、空集合保存、关闭放弃草稿、列表返回、双向更新可见均通过 | [窄屏完整文本提示](evidence/2026-10-17-role-browser-acceptance/21-role-tooltip-1024.jpg)、[最终双向结果](evidence/2026-10-17-role-browser-acceptance/32-bidirectional-auth-final-1440.jpg) |
| 异常和键盘 | 对真实请求控制注入 503，错误可见、确认禁用、重新加载恢复；搜索延迟 900ms 后关闭重开不污染新会话；离线等待/恢复；Tab、Enter、Escape 均通过 | [失败与重试入口](evidence/2026-10-17-role-browser-acceptance/26-selector-error-1024.jpg) |

额外完成 68 秒正常输入探索，覆盖工具栏修改、键盘筛选、状态和日期切换、真实下载。检查未发现主按钮裁切、弹框错层或文字不可读等剩余问题。窄屏角色表格中间列采用 ElTable 自身横滚，选择/身份列初始可见、操作列固定右侧；这不等于整表所有列同时适配到 1024。未扩展为手机端、其他主题或全系统视觉验收。

## 发现与修复

1. 角色/用户两向授权的创建时间列为空。真实服务/仓储已带时间，`RoleUserItemReadModel` 和 `UserAllocatedRoleReadModel` 转换时丢字段；补齐读取字段。SQLite 仓储→服务→handler→响应序列化回归先复现 4 项失败，再通过；真实浏览器路由的两向时间列也已复验。现有 OpenAPI 使用的 DTO 已有字段，本轮无需重写生成产物。
2. 状态写入后列表按既有 `update_time` 排序刷新，原行位置换成另一角色；缺少稳定行键导致旧操作 DOM 被复用。添加 `row-key="roleId"`。真实 ElTable 回归先 RED，再 GREEN；浏览器再次通过状态确认触发刷新，确认旧操作节点已脱离 DOM，点击当前行打开正确角色。
3. 角色表单“权限字符”的必填星号单独占行。标签改为 `inline-flex`，在普通及较小桌面抽屉中复验同行显示。
4. 窄视口长名称/权限字符逐字折行，角色创建时间列被压缩。复用表格溢出提示；时间列设 `min-width="180"`，保留宽屏弹性填充；操作列固定右侧。悬浮完整文本、宽屏填满和小桌面视口已检查。

## 验证与环境记录

- 实际源后端相关集合：210 passed；实际源前端 7 个相关 suite：67 passed。
- 实际源类型检查通过；UI standards 通过，附带 23 项规范回归通过。
- 隔离工作树前后端约定检查通过，覆盖本轮 lint/format/guardrails；这些脚本跳过的测试/类型检查由上述独立命令执行。
- 独立复审无 P0/P1/P2，独立执行后端 25 项、前端 37 项回归通过，且复核最终 `min-width` 差量。
- 浏览器 `pageerror` 为 0。原始浏览器请求、截图和执行日志在 `.git/codex-delivery-preservation/role-browser-acceptance/`；仓库内[验证摘要](evidence/2026-10-17-role-browser-acceptance/verification-summary.json)、[检查命令](evidence/2026-10-17-role-browser-acceptance/final-quality.json)、[独立复审](evidence/2026-10-17-role-browser-acceptance/independent-review.md)保留结果与日志 SHA。

开发环境干扰单独保留：最初源后端测试文件变化触发 WatchFiles 重载，之后仅用进程级 `APP_RELOAD=false` 稳定本轮后端，没有修改配置文件；另有会话 401，恢复后复验通过，不把未证明根因的会话失效称作已修产品缺陷。Vite 一次由 `src/types/auto-imports.d.ts` 触发整页重载，重设明确条件后通过；该声明文件初始与最终均无 git 差异。早期自动化的隐藏原生 input、路由过渡重复元素和排序假设超时属于操作脚本问题，后续使用可见控件与实际排序重新验收。既有 `/health` 的 `ResponseUtil.success` 500 未纳入本轮修复，角色真实业务路由正常。

## 数据与交付边界

11 个验收用户和 12 个验收角色均通过正常界面删除。独立只读 SELECT 确认有效用户/角色、用户角色/岗位、角色部门/菜单关系全部为 0，保留正常软删除记录，见[清理核对](evidence/2026-10-17-role-browser-acceptance/fixture-cleanup.json)。本轮登录正常注销，浏览器及自有开发服务器关闭，已有 MySQL/Redis 保留。

源其他未提交工作保持原归属。最终 `std` 提交、交付窗口哈希保留核对及工作树清理由交付补记确认；不宣称全库所有历史测试或所有页面均已通过。
