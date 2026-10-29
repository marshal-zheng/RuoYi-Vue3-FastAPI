# 字段反馈归属第二轮：Schema Form 与 TextEditor 包（2026-10-29）

当前安装两个本地包，均未发布 npm：

| 包                   | 文件                                         | 包内版本                     | SHA-256      |
| -------------------- | -------------------------------------------- | ---------------------------- | ------------ |
| `@zxio/schema-form`  | `zxio-schema-form-0.1.0-feedback.20261029.2.tgz` | `0.1.0-remark-a.20261022.1`  | `e52df225658a0aa1d4ca2f74417ead0f562984d7471c0d554dc201d08d65fa14` |
| `@zxio/text-editor`  | `zxio-text-editor-1.0.0-feedback.20261029.tgz`   | `1.0.0-remark-ai.20261023.2` | `f3a8c88e8817a1e007b94ff22f2fe1b0f02467c2ae9c7e4c115a4d7f94ee1525` |

`@zxio/zxui` 继续使用 `zxio-zxui-3.0.0-next.0-completion.20261028.tgz`。

相对 `feedback.20261029` 与 `aicontext.20261027.2`：

- **备注编辑器不再在框内显示报错。** 输入法未完成、超出内容限制等阻止提交的原因只通过 `edit-state` 上报，由所在表单项显示；框内只保留粘贴格式等即时操作提示。超出 5,000 字时，表单项显示"备注正文最多 5,000 个字符，当前输入已保留"，受控值回传后不再被换成笼统提示。
- **Schema Form 删除 `presentsBlocking`。** 所有复合字段上报的 blocking 都显示在字段反馈行，并关联到控件。
- **下拉字段的无障碍关联。** schema 表单中 `ZxSelect` 字段的帮助、报错、必填与标签关联到真正的下拉输入框，不再落在外层 div 上。

业务侧配套：

- 用户、岗位表单的备注绑定删除 `presentsBlocking: true`。
- `RemarkEditor` 记录编辑器上报的原因并通过 `blockingReason()` 暴露；`useRemarkField` 的校验规则先取这个原因交给 `ElFormItem` 显示，原因缺失时才用"请完成备注编辑并检查内容限制"。

来源：

- schema-form：ZXUI 仓库 `16bc1d786`，`packages/schema-form` 构建后经 `scripts/contracts/check-form-conditional-edit-packed.mjs` 的打包流程生成。
- text-editor：独立仓库 `1d11d37`。同仓有其他工作线的未提交改动和与之配套的依赖安装，因此在隔离快照中按已提交的 `package.json` 构建。新包与 `aicontext.20261027.2` 的依赖和导出完全一致；会一并带入该仓已提交的代码块改动，备注字段不涉及代码块。

安装命令 `YARN_ENABLE_NETWORK=0 corepack yarn install --mode=skip-build`，`yarn.lock` 只变更这两个条目。验证见 ZXUI 仓库 `docs/reports/2026-10-29-schema-form-field-feedback.md` 的"后续"一节。
