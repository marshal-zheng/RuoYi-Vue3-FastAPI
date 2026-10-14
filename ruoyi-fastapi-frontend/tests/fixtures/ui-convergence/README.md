# 独立组件浏览器 fixture

该页加载真实业务 SFC、已安装 ZXUI 公开组件、业务 Host/Provider 和公开 deployment 资产。它不是产品路由。C/F 编号见仓库 `docs/reports/zxui-form-dialog-2026-09-22/browser-route-coverage.md`。

2026-10-14 已移除无业务消费者的旧 DeviceClazzDialog、ProjectEditDialog、两个模拟 ExportDialog 和 F04/F05/F07/F08 夹具项；设备分类由 CategoryFormDialog（C01）统一处理，真实工程入口使用 ProjectFormDialog，真实导出页面及 VersionExportDialog 保持使用实际服务。历史检查编号保留，当前夹具共 19 项。

在 frontend 目录运行：

```sh
node tests/fixtures/ui-convergence/prepare.mjs
./node_modules/.bin/vite --config tests/fixtures/ui-convergence/vite.config.ts
```

打开 `http://127.0.0.1:4182/`。端口、Vite cacheDir 和输出资产均独立于 80 端口业务服务。准备命令调用真实生成器函数产生 `GeneratedForm.vue`，并从九主题单一登记调用公开 `emitThemeDeployment`；生成物可以重建且被本目录 `.gitignore` 排除。

页顶选择真实组件，按“打开当前组件”调用公开 `open` 或变更 `modelValue`。矩阵编辑、ImageUpload 预览、RightToolbar 显隐列和旧工程详情需点击各自组件内真实入口。旧 GridList 使用固定高度的 flex 宿主，符合该组件 fill 布局要求。

业务 HTTP 客户端使用测试专用内存 Axios adapter，按当前 items/page 数据契约返回样例；没有登录步骤，不把生成物加入生产路由，也不调用真实后端。ImageUpload 只预览本地 SVG，不上传。验收只在当前样例 props/数据边界内成立。

页底 FormGrid 用真实业务布局组件在 1100/650/320px 容器中测试降列；这不是对浏览器 viewport 或完整业务页面窄屏表现的声明。模式/密度选择走既有统一偏好入口，来源隔离在 4182。

生成完整 SFC 的 JSDOM 交互回归：

```sh
./node_modules/.bin/vitest run tests/generator-form-runtime.test.ts tests/generator-form-contract.test.ts tests/ui-standards.test.ts
```

实际浏览器记录见 `docs/reports/zxui-form-dialog-2026-09-22/browser-fixture-coverage.md`。任何组件内嵌 VXE 的全表格行为不由本页输入/弹框检查推导通过。
