# 菜单、协议、公告、岗位、工程与字典数据编辑读取生命周期

日期：2026-10-16。范围仅为本轮编辑读取归属及用户编辑 401 恢复反馈；未混入 DTO、缓存、重试或其他 HTTP 优化。

## 结果与选型

六类业务的七个实际编辑入口，以及已有用户编辑，统一复用 `src/utils/editor-read.ts` 的 `useEditorRead`。工程同时覆盖 `views/project/components/ProjectFormDialog.vue` 与 `views/system/project/components/ProjectDlg.vue`，避免只覆盖管理入口。

读取由本次打开持有：立即展示保留 ID 的加载态，关闭、重开、切目标和卸载取消旧请求；回填前检查读取实例；旧成功、错误与 finally 均不能影响新打开。当前失败保留编辑身份、禁用保存并允许按原目标重试。详情 API 延续上一轮的返回 ID 校验。

菜单详情和父菜单树共用一次打开的 signal，并行读取后统一回填；保留新增根菜单、指定父级新增和空树语义。公告内容、岗位字段、工程创建结果、协议配置及模板校验保持原有业务处理。字典数据沿用内联表单结构，固定本次编辑目标，保留新增字典类型和自定义 footer；footer 与提交函数同时阻止加载中/失败保存。

用户编辑移除重复的手写读取控制，接入同一 helper。当前 401 经 `presentRequestError` 恢复既有重新登录策略；过期打开的 401 静默，原错误及请求配置保持。新增用户仍读取岗位和角色选项，合法空集合可正常完成读取。

选择已有 helper 的收益是跨业务共享归属与反馈策略，避免继续复制控制器/finally 实现；代价是详情获取移动到拥有打开状态的组件、父调用只传目标并承接已反馈拒绝。保留现有布局与领域字段映射，未引入第二套基础设施。

## ZXUI 责任核对

检查源码 `packages/components/hooks/use-dialog/index.ts` 和 `use-drawer/index.ts`：已有 generation 隔离确认/finally、异步关闭与 late closed，足够支撑本轮。缺口在业务显式读取未接入生命周期，因此本轮无需修改 ZXUI。源码直连构建与真实探针使用 `/Users/hqz/Downloads/element-plus`，本轮未修改库源码。结束核对时另有外部工作新增 `docs/specs/http-vue-query/` 下的 spec 文件，已原样保留，不纳入本轮变更。

## 验证

- 新回归先红，覆盖乱序成功、旧错误/finally、同 ID UI 关闭重开、编辑切新增、当前失败重试、卸载和当前/陈旧 401；菜单另验证选项归属。最终 277 项聚焦测试通过（含 57 项新组件回归和 7 项 API 参数透传）。
- ZXUI dialog/drawer hooks：20 项通过；UI standards：14 项通过。
- `yarn lint:check`、`yarn type-check` 通过。
- `VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus yarn build:prod` 通过；保留既有 chunk/Browserslist 提示。
- 前端约定脚本 `bash .cursor/skills/frontend-conventions/scripts/validate.sh --changed` 未通过：仅命中既有、相对本轮基线未修改的 `src/views/project/components/VersionList.vue` console 用法。本轮不顺带处理。
- 两轮独立只读审查未发现本轮确证问题或范围遗漏。

## 真实业务证据与边界

43 项真实业务检查通过。加载生产 SFC setup/open/confirm、生产 API/HTTP、ZXUI 源码 hooks，以真实 Axios XHR 访问本机 FastAPI/MySQL。回环网关仅延迟真实上游响应，用于乱序、关闭重开和取消验证；未伪造业务详情。

八个编辑器各验证：切换并保存最新记录且旧记录不变；同 ID 关闭重开时旧 finally 不释放 loading；编辑切新增并保留合法选项；真实 404 阻止保存并重试原 ID；卸载取消。另验证七个父事件入口承接错误、用户真实 401 登录恢复与重试，以及清理。协议配置、公告内容和用户空角色集合得到实际保存/读取核对。

仅使用临时业务记录。探针适配过程中修正了创建用户返回值不含 ID、无渲染模式的表单 ref，以及父事件异步等待等验证器问题；失败轮次临时记录均已清理。最终成功轮次清理后，菜单、岗位、公告、工程、协议、字典类型/数据和用户的列表与总数，与验证前快照严格相等。未处理原有业务数据。

真实探针未渲染原生表单、协议子模板或浏览器视觉界面；不声称人工 UI 验收。组件挂载回归负责事件和提示按钮验证。全程未使用 computer use；仅启动并停止本轮自己的后端进程。

证据位于 [evidence/2026-10-16-remaining-editor-read-lifecycle](evidence/2026-10-16-remaining-editor-read-lifecycle/)；精确 task.diff 以开工脏工作区为基线重建并 SHA256 校验，未把之前工作混入本轮差异。完整业务快照及后端运行日志仅留临时目录，未复制进仓库。
