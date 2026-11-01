# TableRender 真实业务离线预览

挂载实际角色选择器、部门页以及它们原有的 Vue Query 和领域命令。fixture 只替换 Axios transport：所有请求均在内存终止，不连接真实后端。用于跨页选择/禁选/会话失效、部门树、错误旧数据、主题与键盘验收；未支持的编辑端点明确报错。

构建与预览（前端目录）：

```sh
VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus/worktrees/table-render-optimization yarn vite build --config tests/fixtures/table-render/vite.config.ts
VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus/worktrees/table-render-optimization yarn vite preview --config tests/fixtures/table-render/vite.config.ts
```

地址 `http://127.0.0.1:5198/`，不自动打开浏览器。产物在 node_modules/.cache/table-render-pilots，通过真实源码插件消费本轮 ZXUI。完整业务应用原有 dashboard 依赖问题不属于此 fixture。

浏览器验收须取得用户 computer use 授权。构建成功仅证明产物可生成，不代表页面/主题/可访问性已通过。

性能入口为 `http://127.0.0.1:5198/?benchmark`。它通过源码别名直接挂载 ZXUI 文档中的同一个 `performance-workbench.vue`，使用相同 Vue/ElTable/ZXUI peers、production 构建和主题；不复制基准逻辑，也不挂载业务页面。这样避免文档站其他示例的 DOM 与订阅污染生命周期计数。先在 ZXUI 执行 `pnpm -C docs generate:table-render-baseline` 准备固定历史运行时，再构建本 fixture。最终报告须注明使用的是独立工作台入口。
