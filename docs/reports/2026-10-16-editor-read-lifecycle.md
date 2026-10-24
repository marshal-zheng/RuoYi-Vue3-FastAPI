# 五类编辑读取生命周期收敛

日期：2026-10-16。范围：参数、字典类型、部门、角色编辑、角色数据权限。

五类入口已采用用户编辑既有的读取原则：弹层立即打开并清空旧草稿，每次打开持有独立 AbortController，只有当前打开可以回填数据、显示错误和结束 loading。关闭、重开、编辑切新增、组件卸载都会同步结束旧读取；角色权限树在 nextTick 后再次校验归属，旧 finally 不会清除新读取的 loading。

## 实现与责任边界

- 新增 `src/utils/editor-read.ts`，复用用户编辑已经验证过的 signal、读取身份、同步关闭监听与卸载清理模式。业务接口只增加可选的 signal / silentError 透传，不改变写入协议。
- 参数、字典类型、部门详情读取从列表移入弹层的显式 open；角色与数据权限将详情、选项树归入同一次读取。保留部门新增子节点的 parentId 和新增默认值、角色菜单原有逐节点勾选语义。
- 读取期间和读取失败均阻止保存。当前失败留在弹层中并允许重试；并行读取任一失败会取消同次打开的其余请求。父级事件入口承接已经呈现过的读取拒绝。
- 为防止过期读取抢先弹出错误，传输阶段使用 silentError。当前有效失败调用从原 HTTP onError 提取的 `presentRequestError`，复用原有鉴权与业务反馈策略；当前 401 仍有“重新登录”入口，过期 401 静默。保留原 HttpError、config、cause，鉴权继续按传输 meta.status 判定。
- 已查阅 ZXUI useDialog / useDrawer / use-form-modal 的代次与关闭守卫；现有能力能支撑这轮读取归属。未发现需要在库层新增机制的问题，因此 ZXUI 源码、依赖包和 vendor 产物均未修改。请求编排与领域回填仍由业务负责。

机制取舍：直接采用 [Vue 同步 watcher 与副作用清理](https://vuejs.org/guide/essentials/watchers.html#side-effect-cleanup)和 [Axios AbortController](https://axios-http.com/docs/cancellation)，并用读取身份隔离不能及时停止的异步任务；没有引入请求缓存或查询框架。用户编辑既有代码未改动，其他 HTTP 优化不在本轮范围内。

## 验证

| 层次 | 结果与边界 |
| --- | --- |
| 回归先红 | 初版生命周期回归 29 项中 26 项失败、3 项通过；鉴权传输状态与 problem.status 不一致的两个回归先失败后通过。见 evidence 中 red / auth-status-red 日志。 |
| 业务定向回归 | 9 个文件、108 项通过。新增五类生命周期回归 32 项，覆盖乱序成功、旧失败与 finally、同 ID 关闭重开、编辑切新增、当前失败与重试、卸载、树 nextTick、当前/过期 401；同时保留用户编辑与真实 ElTree 的既有回归。 |
| 表单标准 | `yarn ui:standards`：504 个文件、0 违规；标准与生成器回归 14 项通过。 |
| ZXUI 原有能力 | useDialog / useDrawer 定向测试 20 项通过；库工作区非忽略文件哈希与本轮开始一致。 |
| 质量检查 | `yarn lint:check`、`yarn type-check`、`VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus yarn build:prod` 均退出 0。构建保留体积提示。 |
| 约定脚本 | `validate.sh --changed` 仅因既有 `src/views/project/components/VersionList.vue` 的 console 用法失败；该文件哈希未变。 |
| 独立复核 | 复核提出的鉴权入口及传输状态问题已修正；最终只读复核未发现本轮新增的实质问题。 |

真实业务验证：加载五个生产 SFC 的 setup / open / confirm，以及生产 API、HTTP 和错误反馈逻辑，直连 ZXUI 源码 hooks，通过真实 Axios XHR 调用本机 FastAPI / MySQL。回环代理只暂存真实上游响应，以稳定控制返回顺序。

- 27 项检查通过、0 个未处理拒绝：五类最新选择与真实保存、同 ID 关闭重开、四类编辑切新增、当前失败阻止写入并重试、卸载取消、四个生产父级编辑入口、真实 401 重新登录反馈与恢复、清理校验。
- 只保存最新选择的记录，另一条临时记录不变；角色菜单与角色部门权限通过真实接口回读核对。
- 404 验证将一次详情 URL 定向到不存在的子路径，接收后端真实 404；没有伪造业务响应。未将“缺失实体返回什么”扩入本轮后端范围。
- 使用独立命名的临时记录，按现有删除接口清理。最终原有参数 7 条、字典类型 21 条、部门 10 条、角色 2 条，原有列表所有字段与总数一致。早期探针触发部门后端祖先状态传播的时间戳更新，已按先前值精确恢复；最终探针保存临时停用部门，避免触发此无关副作用。
- 这属于真实网络、API、保存与读取状态验证；原生表单、弹层动画及权限树视觉交互未在浏览器验收。未使用 computer use。

## 工作区与证据

业务工作区原有大量未提交改动。哈希核对确认，本轮只有 19 个实现/测试文件发生增量变化，另新增本报告与证据；无关文件、HEAD、暂存区保持原样。ZXUI 共 7,935 个基线文件无变化。本轮临时启动的后端已停止，未提交或发布。

证据位于 [2026-10-16-editor-read-lifecycle](evidence/2026-10-16-editor-read-lifecycle/)，包含验证日志、真实业务检查结果与探针、工作区保护核对、本轮相对开始状态的差异和命令清单。
