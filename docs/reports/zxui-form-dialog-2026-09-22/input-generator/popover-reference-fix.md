# ZxInput 外部 Popover 引用兼容修复

日期：2026-09-23。此项由业务菜单抽屉真实交互发现。输入/生成器实施者接续完成修复和聚焦测试，不能作为该部分独立审阅证据；最终浏览器复核由主线程及主题代理承担。

## 原因与实现

`ElPopover` 的 reference 使用 Vue directive 把事件绑定到子组件真实根元素。`InputTooltip` 的条件 slot 会形成 Fragment，原 `ZxInput` 没有稳定元素根，Vue 发出 `non-element root` warning，readonly 图标输入的外围 Popover 因此无法打开。

`packages/components/input/src/input-core.vue` 使用单个稳定的 `span.zx-input-boundary`。根节点承接调用方 class/style 与 flex/固定宽度；内部 ElInput 填满根，不重复应用调用方宽度。其余原生 attrs/listeners 仍交给 ElInput。slots、七项 expose 和单个 model/event 所有者未变。没有把业务 Popover 包一层作为绕过方案。

中英文 input 文档已更新 attrs/layout 契约。公开同一代表样板 `docs/examples/dialog/public-form-contract.vue` 新增 plain/tooltip 两个外部 ElPopover reference，供源码和隔离包使用同一输入场景验证。

## 聚焦验证

- `pnpm exec vitest run packages/components/input/__tests__/input.test.tsx packages/components/input-number/__tests__/input-number.test.tsx`：18 + 4 = 22 项通过。保留原生 ElInput 对照；两个 tooltip 路径外部 Popover 可见，click 回调一次，未出现 non-element root warning。动态 class/style/aria 更新、slots、native number/search、IME、expose、size 继承和数值组件回归均通过。
- `pnpm exec eslint packages/components/input/src/input-core.vue packages/components/input/__tests__/input.test.tsx`：exit 0。
- `pnpm exec vue-tsc -p scripts/contracts/fixtures/form-dialog/tsconfig.source.json --noEmit`：exit 0（追加外部引用样板前执行；打包检查再次检查最终同样板）。
- 原始输出：`/private/tmp/zxui-popover-final-tests.log`、`/private/tmp/zxui-popover-lint.log`、`/private/tmp/zxui-popover-source-types.log`。

最终候选包收据和真实业务/公开样板浏览器证据由完成后的报告补入；此文不将静态测试等同浏览器通过。

## 本地可安装候选

- 版本：`@zxio/zxui@3.0.0-next.0`。
- Tarball：`/var/folders/80/8sfxkvmx2l755p0cgcrkv3740000gn/T/zxui-packed-install-rApuws/tarballs/-zxio-zxui-CPDqIK/zxio-zxui-3.0.0-next.0.tgz`。
- SHA-256：`085dfd40069635098fa97a8e29dd5764a9d5d4bd558492b5caf1df3e5453317a`，另行读包重算一致。
- `pnpm build` exit 0；`ZXUI_PACKED_KEEP=1 ZXUI_PACKED_REUSE_BUILDS=1 node scripts/contracts/check-zxui-packed-install.mjs` exit 0。隔离 app 内 Vue 3.5.40 / pristine Element Plus 2.13.0 单实例，无 source alias/workspace fallback；最终相同样板通过 public import、vue-tsc、Vite build 与 public deployment。
- 永久收据：`../library/packed-receipt.json`；日志 `/private/tmp/zxui-popover-candidate-build.log`、`/private/tmp/zxui-popover-packed-check.log`。
- 此候选替代 `6qv3zy` 的旧包hash；不代表 npm 发布，浏览器最终证据由主线程及主题代理单独记录。
