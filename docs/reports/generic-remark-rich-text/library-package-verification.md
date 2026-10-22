# 编辑器库与候选包验证

日期：2026-10-22。库修改保留在 ZXUI 项目本地 worktree 及其 text-editor 独立 Git 工作区；应用引用本地 tarball，没有发布 npm。真实主题、键盘焦点和七入口浏览器交互尚未验收。

## 候选交付物

| 包 | 实际安装版本 | 应用 vendor 文件 SHA-256 |
| --- | --- | --- |
| @zxio/text-editor | 1.0.0-remark-a.20261022.5 | `42cda3aa6d7cd9528325dbcaabf16149263aa1db3f868a3a1e8adbc3d7ae3f1e` |
| @zxio/schema-form | 0.1.0-remark-a.20261022.1 | `1fadc9526ab14583a82172a88216fc126a1cf731b0479ca386be6c29c7545be2` |

两包均以 `file:./vendor/...` 进入应用 package.json/yarn.lock。`YARN_ENABLE_SCRIPTS=false yarn install` 退出 0，随后直接读取 node_modules 包清单确认版本。旧的本轮候选与未采用的 theme-compiler 候选已移除，摘要保留在 superseded-candidates.json；既有供应包未清理。部署侧 theme-compiler 继续匹配现有主题资产；源码模式仅为 source plugin 使用 host 源码编译器，没有升级部署主题协议。

## 库实现与回归

公开 root/core 提供 A profile、固定预算、Document/href 接纳函数；公开 root/ui 提供 ZxTextEditorField，样式通过公开 style 消费。原完整编辑器保留自身职责，A profile 拒绝附件、非 A 节点、HTML/Markdown/raw JSON 程序化入口等越界内容。字段值为 Document/null，父表单拥有唯一正文；captureEdit/restoreEdit 只保存链接草稿与选区。composition 隐藏前先发布稳定文档，未完成链接/输入法状态参与提交阻断。

专项复现并修复了实际 ProseMirror clipboard 路径中的两个问题：默认 HTML parser 会丢失 TAB/边界空格，超字节粘贴的空投影会删除选中内容。当前 parser 使用独立 preserveWhitespace 配置，拒绝粘贴由 handlePaste 消费，选中正文保留。普通文本连续/末尾空行及软换行保留；全局缓存 parser 未被修改。新事务位置超出旧文档时，placeholder 安全返回空值，避免粘贴触发旧位置 resolve 异常。

最新库组 **5 文件、157 tests 通过**：99 项契约/profile、15 项真实 runtime、43 项现有 link/full/paste 回归。共享 manifest 实际为 102 项，其中 25 valid、73 invalid、4 plaintext；99 项库契约测试包含 98 个文档向量和一项 profile 检查，并非 99 个向量。命令在 ZXUI task 根目录运行：

```sh
pnpm exec vitest run --config packages/text-editor/vitest.config.mts packages/text-editor/__tests__/basic-rich-text.test.ts packages/text-editor/__tests__/basic-rich-text-runtime.test.ts packages/text-editor/__tests__/text-editor.test.tsx packages/text-editor/__tests__/link-features.test.ts packages/text-editor/__tests__/content-paste-extension.test.ts
pnpm -C packages/text-editor build
pnpm -C packages/text-editor pack
```

日志：`/tmp/remark-library-release-tests.log`、`/tmp/remark-editor-release-build.log`、`/tmp/remark-editor-release-pack.log`。build 包含 vue-tsc、四组 Vite 构建、声明生成与公开声明/代码块出口边界检查，退出 0。新增所属文件显式 `eslint --no-ignore` 退出 0，日志 `/tmp/remark-library-release-eslint.log`。

SchemaForm 的 port 幂等退休与 mounted 后恢复修复见 frontend-generator-verification.md；125 项库测试、typecheck、build 与所属文件 ESLint 通过。

## 源码与安装包一致性

同一 `RemarkPackageRoundtrip.test.ts` 对全部 25 个合法文档执行公开 core 接纳、JSON 保存、公开 Field 挂载/读回、销毁后重挂、安全 HTML 投影；另有真实 Formily/native 六项探针。源码模式与正常安装包模式各 **31/31 通过**，日志分别为 `/tmp/remark-public-source-draft-roundtrip.log` 与 `/tmp/remark-public-installed-draft-roundtrip.log`。安装模式无源码 alias，未出现源码模式的 Vue ref-owner warning。

源码 plugin 的 text-editor 公开出口及内部 #runtime source 映射专项 1/1 通过，日志 `/tmp/remark-source-plugin-focused.log`。完整 source-vite 组有一个已有 charts symlink realpath 失败，不能将专项通过写成完整组通过。源码模式生产构建及最终安装包生产构建由总验收记录汇总。

以上为静态、真实组件 DOM 与构建证据；测试主题 owner/portal port 是明确的替身，不能证明真实明暗主题、density、链接浮层归属或浏览器焦点已验收。

受控字段通过私有 injection context 在首次恢复时允许保留输入所超出的字符/字节/节点预算，结构/版本/meta/URL/深度与原始硬防护保持。Field首次watch立即置blocking，超限仍不可提交；公开TextEditor setDocument/setContent与外部watch仍完整预算。真实Formily超限→hide/show→完整可编辑→submit拒绝→改正可提交回归已先红后绿。最终.4的lint/157tests/build日志分别为 `/tmp/remark-library-draft-eslint.log`、`/tmp/remark-library-draft-tests.log`、`/tmp/remark-editor-draft-build.log`。

最终.5补齐链接portal的IME边界：原生URL input持续维护同一交互linkDraft；组合Enter/Escape不确定/取消，不阻止IME默认动作；capture保留未完成URL，组合结束后Enter才提交。同一最终测试在旧.4源码真实失败，新实现库全组158项（99契约+16runtime+43既有）通过，ESLint/build/pack全部退出0。流水证据 `/tmp/remark-editor-ime-release-results.json`，红 `/tmp/remark-portal-ime-final-red.log`，绿 `/tmp/remark-library-ime-final-tests.log`。组合ZXUI来源与实际安装验证见source-delivery.md。
