# RuoYi 部门资源接入与真实联调

部门管理已接入 ZXUI 资源能力。后续收尾已完成：全量类型检查零错误，安装模式的 130 项相关回归和真实 HTTP/浏览器验收全部通过。源码直连下，生产 `/system/dept` 页面保存成功后自动刷新；同一应用中的两个生产编辑器共享详情读取，各自持有独立草稿，另一编辑器保存和后台刷新不会覆盖正在输入的内容。

## 实现

- `src/queries/client.ts` 在现有原生 QueryClient 上创建唯一 DataClient；登录、退出和授权变化通过 `src/queries/context.ts` 同步作用域并撤销旧读取。
- `src/queries/system/dept.ts` 定义一个 `departmentResource`，包含管理列表、详情、排除自身与后代的上级选项、正常部门用户树，以及创建、更新、删除命令。保留后端真实权限和筛选差异；移除旧部门 key、query 工厂、命令捕获和编辑读取协调接口。
- `DeptList.vue` 使用 `useResourceList` 管理提交输入和已显示结果；`DeptDlg.vue` 使用 `useResourceDetail` 一次性复制白名单 DTO 到原生表单，表单继续拥有编辑草稿。创建、编辑与删除使用命令凭据，写入成功与随后刷新失败分别处理。未知写入结果不自动重发。
- 用户页面和用户表单的两个真实部门树消费者迁入相同资源身份。用户列表仍由原生 Query 管理，部门写入保留其真实领域失效依赖，不另建缓存。原生用户列表重读错误由其现有状态负责，部门资源刷新凭据覆盖部门读取。
- HTTP 适配转发取消信号，资源命令禁用自动写重试，普通结果反馈由当前组件处理，认证恢复仍归全局边界。两份本地 vendor 包更新了 `@zxio/http` 和 `@zxio/vue-query` 的可安装公开导出；未发布远程包。

复用同一原生引擎，减少部门业务自己维护的 key、版本、读取等待和刷新协调代码；代价是应用会话必须明确同步资源作用域，原生用户列表迁移完成前保留一条真实跨域失效依赖。没有给假设消费者增加兼容层。

## 真实验证

后端使用本机 FastAPI `:8088`、现有 MySQL/Redis；前端 `http://127.0.0.1:3100`，真实登录，无 MSW 或 HTTP 响应替换。所有写操作只针对唯一前缀临时部门。

| 断言 | 证据 |
| --- | --- |
| 生产部门页面保存后显示新值 | `browser.json`：`productionRouteSaveRefresh=true` |
| 两个用户树资源订阅共享读取 | 2 个订阅，1 个真实 GET |
| 同一部门同时打开两个生产编辑器 | 2 个编辑器，1 个真实详情 GET |
| 编辑草稿独立 | 两个表单分别输入 `_saved` 与 `_draft`，彼此不变 |
| 保存后自动刷新 | 1 个 PUT；列表和两个树订阅更新；独立 HTTP 读取确认持久化 |
| 后台刷新不覆盖另一编辑器 | 右侧保留 `_draft`；关闭重开后读取 `_saved` |
| HTTP 完整领域链路 | 源码和安装包模式均通过创建、改名、停用/启用、原生用户列表重读、后代排除、422 独立错误分支 |
| 数据清理 | 两次 HTTP 探针各删除 2 条；成功浏览器运行删除 1 条，均再次读取确认不存在 |

浏览器最终运行无 pageerror。准备阶段的 4 次失败尝试已单独保留在 `evidence/2026-11-02-department-resources/attempts/`：分别为测试入口全量导入、动态导入遇到 HMR 身份、Vite 忽略测试文件监听导致旧入口缓存、缺少主题 ConfigProvider。均为验收宿主准备问题；入口改为叶子导入、真实 API 准备数据、重启服务以及安装与应用一致的主题 Provider。尝试 1 的 finally 被页面导航打断，其唯一临时记录由新建本地会话按精确 marker 删除并确认不存在，见 `attempts/recovery-cleanup.txt`；其余尝试均自行清理。最终成功运行完成数据清理和本次会话注销。

## 检查与边界

- 源码模式：8 个测试文件，119 项通过，包含两编辑器草稿隔离、保存已成功但刷新失败时只有一次写入、HTTP 本地反馈与认证恢复。
- 安装包模式收尾：11 个相关测试文件、130 项全部通过，含原先失败的树表集成测试及字典消费者回归。此前“安装版未公开 expandedKeys”的归因有误，见下方根因更正。
- 两种模式真实 HTTP 探针均通过；本次补跑安装模式真实 HTTP 和完整浏览器验收也通过，安装模式记录独立保存在 `installed/`。
- 本次 19 个代码/验收文件 ESLint 零警告；任务文件 `git diff --check` 通过。
- 全量 `yarn type-check` 已通过，退出码 0、诊断 0。字典、通知、岗位三处绑定按真实字典字段的字符串语义投影 `model-value`，非字符串读作未选择；`update:model-value` 仍回写原 GridList 草稿。不使用断言、any 或拓宽 DictSelect/QuerySafeValue 来隐藏不匹配。收尾 5 个代码文件 ESLint 零警告。
- 刷新失败、未知写入、权限切换是受控回归证据；真实浏览器覆盖成功链路，不声称验证过真实网络故障。共享仅限同一应用客户端，不声称跨标签页共享缓存。

## 源码基线与工作区保留

ZXUI 主工作区存在未提交主题产物，与业务 dashboard 扩展要求的契约 hash 不一致，导致整站主题初始化失败。本次未覆盖这批改动，使用项目本地干净 worktree：

`/Users/hqz/Downloads/element-plus/worktrees/ruoyi-department-source`

固定提交 `1b7c3236666f862afc44c23b1c72f49c7dffdb55`，即已交付资源能力所在提交。前端以 `VITE_ZXUI_LOCAL=true`、`VITE_ZXIO_REPO_ROOT` 指向该路径。端口 80 无绑定权限，采用后端已允许的 3100。干净 worktree 保留。当前 3100 服务已明确切换为 `VITE_ZXUI_LOCAL=false` 的安装模式，真实浏览器验收记录 ZXUI 源码导入数为 0。

业务原有 21 个可哈希脏文件保持原样；原本已脏的 `package.json` 只新增本次两个依赖地址变化，`yarn.lock` 相对接手时仅相应 9 行替换。未修改后端源文件、主题校验、用户原有其他功能改动，也未提交或推送。运行期间另有无关 page-agent 产物出现，未操作。


## 安装模式收尾与根因更正

前次仅凭 `wrapper.getComponent(...).vm.expandedKeys` 返回 undefined，将问题归因于安装包缺失接口，这一判断不正确。当前已安装 `@zxio/table-render/ui.mjs` 同时包含 `expandedKeys` getter、`setExpandedKeys` 和 `__expose(api)`，公开声明也一致，无需更换包或修改库 API。

Vue Test Utils 的 `VueWrapper` 对含 setupState 的开发 SFC 构造额外代理；对于打包后 setup 返回 render 函数的组件，则直接返回内部 vm。旧测试依赖了前一种行为，未读取业务父组件真正得到的公开实例。测试现改为 `wrapper.vm.$refs.refTable`，使用公开 `TableRenderInstance` 类型，保留原有展开、折叠、身份切换清空及新域默认展开断言；安装与源码模式均通过。这与 Vue 的 [组件模板 ref/defineExpose 契约](https://vuejs.org/guide/essentials/template-refs.html#ref-on-component) 一致；相关测试代理实现已核对本机 `@vue/test-utils/dist/vue-test-utils.esm-bundler.mjs`。

安装模式浏览器验证新增了真实父子部门展开/折叠：子行隐藏后恢复，不增加列表读取；随后继续完整保存、共享读取与草稿隔离断言。运行中 ZXUI 源码导入为 0，页面错误为 0。浏览器创建的 2 个临时父子部门、HTTP 探针的 2 个临时部门均已按子先父后删除并再次确认不存在，本次登录均已注销。本轮未修改安装包、package.json 或 yarn.lock。

安装模式复跑命令见浏览器 README；全量检查为 `yarn type-check`，回归命令与输出见 `installed/validation.json` 和 `installed/installed-regressions.txt`。

- [安装模式最终验证汇总](evidence/2026-11-02-department-resources/installed/validation.json)
- [安装模式真实浏览器断言](evidence/2026-11-02-department-resources/installed/browser.json)
- [安装模式真实 HTTP 断言](evidence/2026-11-02-department-resources/installed/http.json)
- [安装模式独立草稿](evidence/2026-11-02-department-resources/installed/independent-drafts.png)
- [安装模式保存后保留另一草稿](evidence/2026-11-02-department-resources/installed/saved-with-other-draft.png)

## 复跑与产物

- 浏览器：[入口与命令](../../ruoyi-fastapi-frontend/tests/manual/department-resources/README.md)
- 真实 HTTP：[探针与命令](../../ruoyi-fastapi-frontend/tests/manual/department-query/README.md)
- [最终浏览器断言](evidence/2026-11-02-department-resources/browser.json)
- [源码 HTTP 断言](evidence/2026-11-02-department-resources/source-actual.json)、[安装包 HTTP 断言](evidence/2026-11-02-department-resources/installed-actual.json)
- [两份独立草稿](evidence/2026-11-02-department-resources/independent-drafts.png)、[保存后保留另一份草稿](evidence/2026-11-02-department-resources/saved-with-other-draft.png)
- [本地包 SHA-256](evidence/2026-11-02-department-resources/artifacts.json)

## 提交独立性检查

按用户要求，只提交部门资源、类型修复与验收相关内容。对已混有其他任务修改的 `package.json` / `yarn.lock` 从 HEAD 精确构造本任务快照，未纳入 Page Agent、vue-element-plus-x、配置页、dashboard 或后端修改。

临时项目内 worktree 仅包含待提交快照。首次独立检查发现 HEAD 的旧 SchemaForm 包缺少已提交 TableRender 所需的 `isValueShape`，先前工作区恰好由其他任务的 SchemaForm 包提供。为使本任务可独立安装，从 ZXUI 已提交的 `1b7c3236666f862afc44c23b1c72f49c7dffdb55` 干净源码重新构建独立 `zxio-schema-form-0.1.0-department-resources.20261102.tgz`，仅补齐此必要依赖。其 11 个 JS/CSS 运行文件与前次真实浏览器验收所用包逐字节一致，未打入其他任务的未提交源码。原工作区其他任务的依赖选择保持原样。

独立快照验证：不可变锁文件安装通过；按仓库现有 `node tests/fixtures/ui-convergence/prepare.mjs` 生成被忽略的临时主题 fixture 后，全量类型检查通过；11 文件、130 项安装回归通过；任务代码 ESLint 零警告。生成的 fixture、依赖目录和临时 worktree 不进入提交。记录见 [提交独立性证据](evidence/2026-11-02-department-resources/commit-isolation.json)。本次提交因此包含 HTTP、Vue Query 和必要 SchemaForm 三个独立依赖更新，不包含其他任务的包地址或代码。
