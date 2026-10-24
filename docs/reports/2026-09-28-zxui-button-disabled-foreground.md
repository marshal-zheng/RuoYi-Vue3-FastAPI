# ZXUI 深色按钮禁用文字修正

## 判断

用户指出深色模式中的黑色按钮文字显得异常。此前只确认了颜色来自主题，未进一步检查禁用文字与禁用背景的配对，因此“配色正确”的结论过于宽泛。

最新截图的浅蓝主按钮、青色导入、橙色导出使用深色字有可读性依据：按截图底色计算，黑字对比度约 7.15、9.22、10.36，白字则约 2.94、2.28、2.03。深色页面并不意味着所有实心按钮都应使用白字。

但深绿的修改、深红的删除处于禁用态。它们的背景已经变暗，文字却仍来自全局品牌文字色，当前主题为黑色；这属于 **ZXUI 的按钮状态适配缺口**，不是业务硬编码。

## 根因与修正

Element Plus 的有色实心按钮默认将 `--el-button-disabled-text-color` 设为 `--el-color-white`，禁用背景使用各类型的 `light-5`。ZXUI 已把全局 `--el-color-white` 映射为品牌表面文字色，正常、hover、active 文字也已有独立配对，但遗漏了 disabled 状态。

在 `/Users/hqz/Downloads/element-plus` 中修正：

- `packages/tokens/src/contracts/theme-contract-v4.ts`：增加 accent/success/danger/info/warning 的 `on-fill-disabled` 角色，introducedIn 为 4.5.0。
- `packages/tokens/src/kernel/derivation.ts`：沿用已有对比度文字算法，对解析后的 tint-5 背景计算 disabled 前景；派生版本更新为 1.3.0。
- `packages/theme-compiler/src/adapters/element-plus/mapping.ts`：有色实心按钮按类型映射 disabled 前景，适配版本 2.4.0。
- `packages/theme-compiler/src/adapters/tailwind/mapping.ts`：同步公开角色，适配版本 1.6.0。
- `packages/tokens/theme-contract-v4.baseline.json`：通过现有生成入口更新，保留工作区已有 release evidence。
- `docs/examples/button/disabled.vue`：在现有禁用示例中补齐状态色按钮，便于文档站检查同一问题。

原有正常、hover、active 的文字策略、所有底色、业务按钮类型和禁用条件保持不变。没有在业务页面覆写按钮颜色，也没有把所有按钮强制改为白字。本修复针对有色实心按钮，不宣称覆盖所有 button 变体的视觉状态。

## 本地交付与验证

9 套主题及 Tailwind 资产由原有 compiler/writer 从源码重新生成；没有手工编辑生成 CSS。由于新适配版本无法通过旧 manifest 的严格覆盖校验，使用同一 compiler/writer 先在临时目录生成、全部成功后再替换，旧产物保留在本机临时备份中。

为了使本地源码直连实际加载新的适配版本，更新了 theme-compiler 本地工具产物，并重启业务前端 Vite（仍为端口 80）。没有发布 npm、修改后端或保存业务数据。

| 检查 | 结果 |
| --- | --- |
| 9 主题 × 明暗模式 × 5 种有色实心按钮 | 90 个生成色值组合的禁用前景检查通过，最低对比度约 5.59 |
| 18 个主题/模式的原有 Element Plus 调色板 | 与修改前相同 |
| 截图所对应 air-gray 深色 success 禁用态 | 黑字约 3.58 → 浅色字约 5.86 |
| air-gray 深色 danger 禁用态 | 黑字约 2.69 → 浅色字约 7.81 |
| 实际 Vite 部署注册 | 9 主题均为 EP 适配 2.4.0 / Tailwind 适配 1.6.0 |
| 实际 HTTP 样式资产 | air-gray 主题 CSS 和 EP aliases 均含新角色，返回字节与 manifest 哈希一致 |
| 既有契约基线校验 | 通过 |
| 聚焦 diff 空白检查 | 通过 |

证据：[色值检查](evidence/2026-09-28-zxui-button-disabled/contrast-check.json)、[实际提供的主题资产](evidence/2026-09-28-zxui-button-disabled/served-assets.json)、[修改前调色板](evidence/2026-09-28-zxui-button-disabled/before-palette.json)。

按用户约束，没有新增测试用例，没有运行 lint、业务生产构建或测试套件；只进行了本地主题生成、所需编译器工具更新、契约及数值/HTTP 检查。未获浏览器操作许可，未执行页面截图或交互验收；当前结论证明修复已由开发服务提供，不冒充浏览器视觉终验。
