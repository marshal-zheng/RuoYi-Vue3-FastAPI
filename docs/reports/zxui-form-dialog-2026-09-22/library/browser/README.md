# 公开表单样板浏览器证据

2026-09-23 最终候选公共样板浏览器验收已通过，包括 R5.AC2 / R13.AC3 的真实 autofill：源码和隔离安装包、raw ElInput 和 ZxInput、浅色与深色均获得真实伪类及主题着色实证。

最终 ZXUI `3.0.0-next.0` SHA-256：`085dfd40069635098fa97a8e29dd5764a9d5d4bd558492b5caf1df3e5453317a`。隔离安装使用 Vue `3.5.40` 和未打工作区补丁的 Element Plus `2.13.0`；第三方单实例及包解析证据见 [packed-receipt.json](../packed-receipt.json)。

同一个 SFC 位于 `/Users/hqz/Downloads/element-plus/docs/examples/dialog/public-form-contract.vue`。源码页面 `https://localhost:3101/FormDialogContract`，最终隔离包 `http://localhost:3105/`。两者均使用 EP 公开基础 CSS、ZXUI 公开样式和主题部署交付，不加载 RuoYi CSS。

## 最终观测

[原始逐项记录](final-browser-2026-09-23.json) 在操作后增量保存，包含源码/安装包 × default/defense-green × light/dark × compact/default/comfortable 的 24 个组合。四个初始紧凑读数捕获到 CSS transition 的小数高度，后续同组合稳定读数已重新采样，原始记录未删除。

| 主题 | density | 普通 / raw ElInput / tooltip / disabled | FormItem small | 显式 large |
| --- | --- | --- | --- | --- |
| default | compact | 28px | 20px | 36px |
| default | default | 32px | 24px | 40px |
| default | comfortable | 36px | 28px | 44px |
| defense-green | compact | 26px | 18px | 34px |
| defense-green | default | 30px | 22px | 38px |
| defense-green | comfortable | 34px | 26px | 42px |

军绿的 control-y 为 5/7/9px。Form size small/large 实测继承为 24/40px；显式 FormItem small 与控件 large 保持 24/40px。父 dialog 为 880px，嵌套 dialog 为 640px。

两条路径均核验：

- 普通及 tooltip 输入外部 ElPopover 引用可点击打开，各自出现对应内容；共 4 个案例。tooltip 分支也显示内部 tooltip。
- 普通四 slots 为 `https:// @ ✓ .example`，tooltip 四 slots 为 `Email @ .com Verified`。
- 输入选择暴露方法聚焦真实 INPUT，选择范围 0–10；clear 后值为空。公开 expose 检查显示 INPUT、TEXTAREA 与真实 textareaStyle。
- 空名称校验显示 `Name is required`；reset 清空名称并清除错误。
- 原生 number DOM type=number，未产生 `.el-input-number` 容器；显式 Search append 正常处理搜索值。
- 提交得到 `nativeNumber: "7"`、`nativeSearch: "needle"`、`quantity: 3`，随后关闭 dialog。原生 number 保留字符串，独立步进器保留 number。
- parent light/default 与 child dark/comfortable 同时存在；切换后 parent dark、child light 同时存在。子 Select 与子 Input tooltip 的最近 scope 均为 `.public-form.public-form-nested`，主 Select 为 `.public-form`。明暗背景随各自 scope 生效，关闭重开仍正确。
- 最终 packed 无 warn/error。源码捕获到 Chrome Vue devtools 扩展来源的 `Object` warnings，没有应用错误文本；因此不声称源码控制台绝对无警告。

嵌套模式第一次在下拉打开时点击未证明变为 light，记录保留为未成功尝试；关闭后重新打开，在无遮挡状态切换，最终 `nested-mode-switch-confirmed` 读数及截图证明 light child / dark parent。一次按 Escape 后 dialog 已关闭的空尺寸读数标记为 invalid，未计作验收。

## 截图

最终截图文件均带 `-final.png`：source/packed 的 `nested-dark`、`nested-light-parent-dark`、`default-dark-popup`，以及 `source-defense-compact` 和 packed 三个 compact 稳定复采。已人工查看源码军绿紧凑与最终包 light child / dark parent 截图，字段、槽位与浮层布局可见且正确。

## 真实 autofill

独立端口首次聚焦 username 并按 ArrowDown 后，raw ElInput 与 ZxInput 的 `matches(':-webkit-autofill')` 均为 false，此失败触发记录保留。之后完整同一 SFC 分别生产构建，在已有 localhost 凭据的父任务 IAB 同源入口触发成功。没有读取 profile、保存新凭据、强制伪类或用 fill 冒充 autofill，DOM 证据不含字段值。

真正 autofill 暴露了源码生产构建缺样式：公开 `@zxio/zxui/style` 指向纯副作用 style.ts，source package 只声明 CSS/SCSS sideEffects，生产构建裁剪了这条 TS 入口。play bootstrap 改为公开 `@zxio/zxui/style.css`；重新构建后确认输出含通用 autofill 规则，ESLint 和构建均通过，并重测源码 12 个 density 组合全部为预期整数高度。最终包本来已直接交付 CSS，无需改变 085dfd40 候选。

父任务 IAB 保存了以下真实 DOM 记录；本报告已逐份核对：

- [源码浅色](../../browser/resumed/public-source-fixed-autofill-light.json) / [源码深色](../../browser/resumed/public-source-fixed-autofill-dark.json)
- [安装包浅色](../../browser/resumed/public-packed-autofill-light.json) / [安装包深色](../../browser/resumed/public-packed-autofill-dark.json)

四组记录的 raw ElInput 与 ZxInput password 均为 `autofill: true`。浅色 inset paint 为 `color(srgb 0.991 0.9928 0.9964)`，文字为 `color(srgb 0.12 0.14 0.18)`；深色 inset paint 为 `color(srgb 0.096 0.1101 0.1383)`，文字为 `color(srgb 0.93 0.95 0.98)`，与当前 scope 的 semantic token 一致。浏览器 computed background 仍报告 UA 蓝色，但实际由 1000px inset paint 覆盖；`-webkit-text-fill-color` 使用 getPropertyValue 读取，不能以错误的 camel 属性空字符串代替实测。

旧源码失败记录 `public-source-autofill-*` 保留，不与修复后 `public-source-fixed-autofill-*` 混淆。对应 PNG 已保存。父任务补充 [源码深色可见字段](../../browser/resumed/public-source-fixed-autofill-dark-visible.png) 与 [安装包深色可见字段](../../browser/resumed/public-packed-autofill-dark-visible.png)，已查看确认自动填充文字可读、密码遮罩、主题深色填充正常；原滚动下半段截图只作历史记录。

同源样板没有业务入口、业务 CSS 或 RuoYi token 修补，构建与临时托管路径见 [同源托管收据](autofill-same-origin-hosting.json)。验收后的两个临时目录已移出业务 public，归档于 `/private/tmp/zxui-public-autofill-verified-2026-09-23`；收据记录完整路径。

## 历史证据

[2026-09-22 恢复记录](observed-evidence-2026-09-22.json) 对应旧 bd267 候选，只作历史证据；旧 PNG 不替代最终候选复验。

浏览器曾暴露并已修复：Host 默认 portal target 未注入、named ZxDialog 缺局部 loading、play 缺 EP 基础 CSS、play 固定资产列表不覆盖嵌套 variant，以及 ZxInput fragment 不能作为外部 Popover reference。源码与最终包已复验这些核心行为；静态回归见 [static-verification.json](../static-verification.json)。
