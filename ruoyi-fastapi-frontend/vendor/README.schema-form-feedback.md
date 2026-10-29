# Schema Form 字段反馈归属包（2026-10-29）

当前安装 `zxio-schema-form-0.1.0-feedback.20261029.tgz`，包内版本仍为 `0.1.0-remark-a.20261022.1`，SHA-256 `1957af51e9838ff95483f7fda7f0341cc66dc45fb3237ef7918b55c6b75b840c`。未发布 npm。`@zxio/zxui` 继续使用 `zxio-zxui-3.0.0-next.0-completion.20261028.tgz`。

相对 declarations.20261029：

- 字段级反馈统一由 `ZxField` 呈现，顺序为控件、帮助说明、反馈行；各类字段都预留同一行反馈空间，帮助说明不再紧贴下一个字段。
- 复合字段报告的未完成输入（blocking）显示在字段反馈行，并暂时替代该字段已过期的规则提示。
- 对象与数组容器不再套 `ElFormItem`，容器错误不会把子字段标红。
- 附件上传 callback 可抛出 `FieldUploadError` 给出失败原因；字段自身的拒绝原因（标识重复、表单未接受等）显示各自文案。

业务侧配套：

- 用户、岗位表单的备注绑定声明 `presentsBlocking: true`，`ZxTextEditorField` 继续自己显示未完成提示，字段只显示规则反馈，同一提示不重复。
- `useSchemaAttachmentUpload` 以静默反馈发起上传：带错误码的 4xx 业务拒绝转为 `FieldUploadError`，只在字段显示原因；服务端与网络失败保持全局提示及追踪号，字段显示通用文案。`useAuthenticatedUpload` 与 `uploadFileAsset` 新增可选 `feedback`，其他上传组件默认行为不变。

来源：ZXUI 仓库 `packages/schema-form/dist` 构建后，经 `scripts/contracts/check-form-conditional-edit-packed.mjs` 的打包流程生成，复制前核对 SHA-256。安装命令 `YARN_ENABLE_NETWORK=0 corepack yarn install --mode=skip-build`，`yarn.lock` 只变更 schema-form 条目。

验证：全量 `./node_modules/.bin/vue-tsc --noEmit` 通过；`VITE_ZXUI_LOCAL=false` 下用户、岗位、SDK 与附件上传 12 个文件 139 项通过。证据见 ZXUI 仓库 `docs/reports/evidence/schema-feedback-2026-10-29/`。
