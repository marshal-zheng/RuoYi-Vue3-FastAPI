# 编辑器库与候选包验证

日期：2026-10-22。本轮交付本地候选及源代码，没有发布 npm。真实七入口、主题、density、浮层焦点和键盘操作由用户手测。

## 最终交付组合

| 包 | 版本 | vendor SHA-256 |
| --- | --- | --- |
| @zxio/text-editor | 1.0.0-remark-a.20261022.9 | `8fa94fd6c39140c5d011581bb0b870f3aea7c82bf6d74aa4f8f616565d0ab26a` |
| @zxio/schema-form | 0.1.0-remark-a.20261022.1 | `1fadc9526ab14583a82172a88216fc126a1cf731b0479ca386be6c29c7545be2` |
| @zxio/zxui | 3.0.0-next.0-remark-raw.20261022.1 | `9a8b2540581fdee21da846ab71e4086d97c4d17a20bb6d17495ff7b7f22fc555` |

通过 file:vendor 及 yarn.lock 安装。ZXUI组合候选保留源图标基线和源已有InputNumber raw API，来源与窄范围输入见candidate-provenance.json。应用其余依赖、resolutions和icons:check保留源当前版本。部署theme-compiler和主题资产保持原配套协议；源码plugin使用所属源码编译器。旧本轮候选隔离或移除，摘要见superseded-candidates.json，未清理既有供应包。

## 库与字段验证

公开root/core提供A profile、预算、Document/href接纳；root/ui提供ZxTextEditorField，公开style交付样式。父表单拥有唯一正文，capture/restore只保存交互草稿和选区；未完成输入法或链接阻止提交。已有完整编辑器保留其职责。

最终编辑器5文件158项通过：99契约/profile、16真实runtime、43既有link/full/paste回归。共享102向量为25 valid、73 invalid、4 plaintext；99不是向量总数。覆盖实际clipboard空白与软换行、字节拒绝保留选区、清空撤销、超限typing与hide/show恢复、IME/link draft隔离、disabled和权威回填等。

IME测试显式使用真实Teleport，断言input属于portal且不属于Field根。此前全局teleport stub把portal原地渲染，造成合成组合事件错误进入正文监听；原失败、探针及修正证据保留，未靠改产品键盘逻辑或放宽断言消除。源产品实现完成后去除全部诊断探针。

最终默认 `pnpm build` 在ZXUI源码依赖链接下通过，包含vue-tsc、四组Vite、声明与代码块出口边界；随后pack成功。编辑器自身tsconfig按同仓build约定显式preserveSymlinks:false。内部Icon/Button/Dialog使用公开core入口，避免legacy capabilities静态带入完整图标目录。所属Field/LinkPopup/InsertIframe显式ESLint通过；19处导入文件规则计数与输入27项相同、无新增，不声称旧库全量lint清零。

Vue3.5 named template ref会推导整个组件实例树进公开声明。Field、LinkPopup、InsertIframe采用私有callback ref，保持同一内部handle和交互，公开Field声明只保留字段契约。最终strict/noEmit/skipLibCheck:false公开root/core内存消费者探针，无consumer诊断、新Field诊断清零；相对.6候选27→18诊断、无新增。18项在当前原源仓ignored产物中同现，但该旧产物无75fc构建指纹，因此只作为辅助对照，不伪作精确输入基线或全库声明零错。详细JSON由独立审查报告保存。

最终流水：`/tmp/remark-editor9-release.json`、`/tmp/remark-editor9-tests.log`、`/tmp/remark-editor9-source-build.log`、`/tmp/remark-editor9-owned-eslint-final.json`。首次误打包的失败.6 SHA `50976d54c5bc020e9f6e09b591df294fa23280d30775999c2a815ad8d5eda98a`已隔离，不会安装；中间声明有缺陷的.7/.8同样不交付。

SchemaForm port幂等退场、mounted恢复与单一正文责任的125项、typecheck/build/所属ESLint通过，见frontend-generator-verification.md。

## 实际应用与源码一致性

最终9安装包公开测试33项、源码直连31项覆盖全部合法文档往返、真实Formily/native和链接IME；同版本源码与安装包生产构建、类型、lint、manifest图标审计结果见source-delivery.md及final-integration-verification.json。安装模式无源码alias，测试主题owner/portal是明确替身，不能证明真实浏览器主题或焦点已验收。
