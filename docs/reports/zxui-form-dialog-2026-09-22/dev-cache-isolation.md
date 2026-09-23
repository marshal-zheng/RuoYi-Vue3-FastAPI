# 项目路由动态导入阻塞：验收服务缓存隔离

2026-09-23，只代码与本机HTTP读取定位，未登录、未读token、未改业务页面或simulation。

- `/src/views/project/detail.vue`、`topo.vue` 本身HTTP200。沿两个模块的静态依赖读取172个模块，14个优化依赖返回HTTP504 `Outdated Optimize Dep`，包括X6及其插件和WangEditor；不带?v请求仍504。
- 正在服务的80模块引用hash `ce32ddd7`，共享磁盘 `node_modules/.vite/deps/_metadata.json` 已变为 `53eecb2f`，其中没有X6条目。
- 并行4182验收fixture使用同一前端package，缺少独立cacheDir，与80争用默认 `node_modules/.vite`。这解释源SFC200而整页dynamic import失败；不是工程数据或simulation错误。
- fixture负责人已将 `tests/fixtures/ui-convergence/vite.config.ts` 改为 `cacheDir: resolve(frontendRoot, 'node_modules/.vite/ui-convergence')`，由主线程统一重启。最终路由重验另记浏览器记录，修前HTTP图见 `verification/project-import-http-before.json`。
