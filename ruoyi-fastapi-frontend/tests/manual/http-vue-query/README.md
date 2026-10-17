# 共享字典真实 API 浏览器验收

按项目日常方式启动后端与源码直连 Vite，先在 `http://localhost/` 登录，再在**同一个标签页**打开：

`http://localhost/tests/manual/http-vue-query/index.html`

此独立 HTML 入口安装应用原生 `setupQueries` / `queryClient`、Pinia、Element Plus、ZXUI 与主题 Host，以当前用户的真实 `getInfo` 建立 query scope。没有 HTTP mocks，也不改生产路由。沿用同标签页的 sessionStorage 令牌，避免新标签页恢复 cookie 会话后影响其他标签页的认证状态；不修改认证机制。

默认只读 `sys_normal_disable`（另两组为 `sys_user_sex`、`sys_yes_no`），不包含任何已删除验收数据的 ID。需要验证写后扇出时，先在真实字典管理页面创建可清理的 `codex_` 前缀临时字典及其选项，记下类型名、字典 ID、选项 ID，再在同一个标签页打开：

```text
http://localhost/tests/manual/http-vue-query/index.html?type=codex_你的临时类型&dictId=实际字典ID&itemId=实际选项ID
```

三个参数均需显式提供：`type` 必须以 `codex_` 开头，两个 ID 必须为安全正整数；缺参或格式错误会禁用写控件。真实写入前会读取类型与选项详情，核验两个 ID 对应同一指定临时类型及当前会话范围，然后只修改标签。有效参数会将该临时类型作为首组读取。结束后回真实页面删除临时选项和类型。

- 默认 8 行同类型：每行真实 `DictSelect`、`DictAutocomplete`、`useDict → DictTag`、`DictStatus` 共享同一原生 query。
- 新增一行验证 fresh 缓存；冷启按钮只在卸载消费者后取消并移除当前 scope 的字典查询；3 类型按钮使用输入框前三个类型各 3 行。
- 选中值在每行右侧展示；在 Autocomplete 内保持焦点输入草稿，再点击刷新按钮观察建议及草稿。
- 标签保存与刷新按钮阻止鼠标按下导致输入框失焦，可手动输入 Autocomplete 草稿后点击按钮检查刷新期间的草稿。标签保存调用现有 `dictCommands.updateItem`，不重建任何行，不额外手动刷新；观察写命令自身失效后的订阅扇出。
- 刷新按钮调用实际 `queryClient.invalidateQueries`，组件本身展示加载、后台错误与重试、暂停状态。浏览器可拦截 `/api/system/dict/data/type/*` 失败或离线；此入口不内置故障模拟。
- 等待超过 30 秒再展开选择器可观察 stale 读取。类型输入框支持专用可清理的验收字典。
- 页面单独展示 mount、nextTick、rAF、data-ready、ready-paint、network-settled marks，另展示资源条目数量。精确请求数量（特别是失败/取消）以 Network 为准；资源条目不代表业务响应成功。

浏览器文档各有独立 JS 模块实例。另一个标签页的生产写入不会对本页的内存 QueryClient 自动失效；写后订阅者扇出使用本页真实写命令，管理列表另在真实字典管理页面验证，不能把跨标签页刷新当作 Query 保证。

从 `ruoyi-fastapi-frontend/` 重跑样本静态检查：

```bash
yarn vue-tsc -p tests/manual/http-vue-query/tsconfig.json --noEmit
yarn eslint tests/manual/http-vue-query/main.ts tests/manual/http-vue-query/Acceptance.vue tests/manual/http-vue-query/DictRow.vue
```

页面的结束/恢复查询范围按钮只操作当前文档的查询 scope；卸载第一行可验证剩余订阅者仍能共享读取。
