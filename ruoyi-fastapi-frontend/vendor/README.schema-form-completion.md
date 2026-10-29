# Schema Form 本地配套交付（2026-10-28）

本轮使用已完成自动验证的本地 tarball，未发布 npm。文件名的 `completion.20261028` 用于区分在研产物；包内 semver 沿用现有源码清单，不代表 registry 上相同 semver 的内容。

| 包 | 业务文件 | 包内版本 | SHA-256 |
| --- | --- | --- | --- |
| `@zxio/schema-form` | `zxio-schema-form-0.1.0-completion.20261028.tgz` | `0.1.0-remark-a.20261022.1` | `0d8788f79f3509569b5d9576f88cccb108eefcf7bb0b3ab3b6a738b9c9f304d4` |
| `@zxio/zxui` | `zxio-zxui-3.0.0-next.0-completion.20261028.tgz` | `3.0.0-next.0` | `f4257d0d3f0c6b1a0eaadc69714f0621704412958a0527056a6b2cbca2369a9e` |

来源：`/Users/hqz/Downloads/element-plus/packages/schema-form/dist` 与 `/Users/hqz/Downloads/element-plus/dist/@zxio/zxui` 标准构建后，通过正式 packed checker 的 `pnpm pack` 流程生成。业务复制同一 fixture 的字节，并在复制前核对上述 hash。确切生成文件、来源、hash 与验证日志记录于 ZXUI 仓库 `docs/reports/evidence/schema-completion-2026-10-28/{audit,business}/`。

`package.json` 直接依赖这两个文件，并通过既有 `resolutions.@zxio/zxui` 统一 peer 实例；权威 `yarn.lock` 已更新。旧 tarball 保留，不进入当前这两个包的依赖解析。本地消费验证使用 `YARN_ENABLE_NETWORK=0 corepack yarn install --mode=skip-build`（依赖缓存已备齐）；常规安装仍执行 `corepack yarn install --immutable`。

本轮新增能力包括 Schema Form locale、完整日期/时间 raw 编辑、嵌套作者/错误路径类型、IconSelect 字段，以及业务侧 `useSchemaAttachmentUpload` 对现有鉴权文件服务的回调适配。上传仅使用后端已登记的 generic purpose；移除表单引用不等于删除服务端资产。用户表单没有虚构附件 DTO 字段。

最终验收：全量 `vue-tsc --noEmit`、`VITE_ZXUI_LOCAL=false` 的 12 文件 135 项用户/岗位/SDK/上传回归，以及真实包模式整站生产构建。后端隔离用户 HTTP 与真实 MySQL/MinIO 附件链分别记录。浏览器输入、视觉主题及系统文件对话框验收按用户要求延期。
