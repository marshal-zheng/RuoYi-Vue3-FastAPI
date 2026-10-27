# Schema Form 本地快照

当前安装快照为 `zxio-schema-form-0.1.0-aicontext-hardening.20261027.tgz`，SHA256 为 `83b206337ba96cef3dbaf23500b83308217c086848081e7ec61909cb94daa9b7`。内部 manifest 版本保持 `0.1.0-remark-a.20261022.1`，快照通过独立文件名和 SHA256 识别，未发布 npm。

产物来自 `/Users/hqz/Downloads/element-plus/packages/schema-form/dist`，由包 build 和 npm pack 生成。公开入口为 `@zxio/schema-form/formily`；宿主使用 Element Plus `2.14.7`，以及精确 `2.3.7` 的 `@formily/core`、`@formily/vue`、`@formily/reactive`、`@formily/validator`。root 与 `/fields` 继续保持无 Formily 依赖。

岗位表单关闭保护分别检查 canonical 修改 `dirty`、未完成输入 `hasUncommittedInput` 和异步活动 `fieldPending`；保存中或结果待核对时仍不能关闭。动态岗位字典只更新 `dataSource`。当前快照合并 AI 字段上下文接线与既有校验反馈、字段交互、实例生命周期修复，详见 ZXUI 当前实现和回归测试。

源码联调使用 `VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus`。普通消费使用 package.json 中的本地 tarball，无需源码开关。`PostSchemaSession.test.ts` 在两种模式运行相同公开契约：真实 PostDlg、SchemaForm、数字与字典控件，网络和备注编辑器使用 mock；它覆盖未完成数字输入的关闭/换记录保护、纠正后关闭和字典更新。

本次合并交付验证（2026-10-27）：实际安装模式 9 个文件、118 项测试通过，包含岗位关闭与保存边界；源码直连模式 7 个 AI/备注集成文件、110 项测试通过。AI 定向类型检查、manifest 检查及生产构建通过。当前 tarball 的 68 个文件与实际安装内容逐一一致，JS/CJS 同时包含 AI 接线与 `hasUncommittedInput`。

原 hardening 快照的历史验证记录：源码模式与 installed 模式各 3 个文件、20 项测试通过，没有按模式跳过测试。两模式的岗位表单定向 vue-tsc 和改动文件 ESLint 均通过；现有 tsconfig.schema-form.json 的完整类型检查也通过。定向类型检查继承该配置并限于岗位表单及其测试；源码模式额外映射 schema-form 公开入口到本地源码，installed 模式使用实际安装声明。原 tarball 的 67 个文件与当时 dist、node_modules 内的安装内容逐一一致；当时 package.json 和 yarn.lock 只改变 schema-form 依赖与对应锁记录。

组件与保存边界回归命令（在前端目录执行）：

```sh
VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus yarn vitest run --reporter=dot tests/unit/components/PostSchemaSession.test.ts tests/unit/components/PostSaveFeedback.test.ts src/views/system/post/components/post-form.test.ts
VITE_ZXUI_LOCAL=false yarn vitest run --reporter=dot tests/unit/components/PostSchemaSession.test.ts tests/unit/components/PostSaveFeedback.test.ts src/views/system/post/components/post-form.test.ts
yarn vue-tsc --noEmit -p tsconfig.schema-form.json
```

本轮验收限定为源码及安装包的组件挂载、岗位保存边界、定向类型检查与 lint，不沿用此前任务的真实 HTTP、浏览器视觉或后端读写结论。
