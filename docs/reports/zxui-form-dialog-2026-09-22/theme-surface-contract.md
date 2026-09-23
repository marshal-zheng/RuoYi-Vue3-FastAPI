# 业务主题 surface 契约锁定

记录日期：2026-09-22。由本次 spec 主代理确认，业务选择消费 ZXUI 当前公开的 experimental surface 契约。本文记录消费边界和升级核对要求，不增加运行时主题状态、映射或私有资源协议。

业务 `data-zx-surface` 与公开 `--zx-semantic-surface-*` 消费依赖以下契约身份：

- `contractVersion`: `4.0.0`
- `contractContentHash`: `sha256:e3e799317b957dcda893f9298b18448878afaaccee8e868b6ee5be06022f6852`
- ZXUI 主版本候选：`3.0.0-next.0`。此候选仍需最终源码与 tarball 浏览器终验；记录身份本身不代表验收完成。

本记录从 `src/theme/zx-theme-packages.ts` 唯一登记派生主题包列表，通过各包公开 `manifest.json` export 读取 `identity`，九个主题身份一致：

| 主题包 | packageVersion | contractVersion |
| --- | --- | --- |
| `@zxio/theme-default` | `2.0.0` | `4.0.0` |
| `@zxio/theme-defense-green` | `1.0.0` | `4.0.0` |
| `@zxio/theme-army-pine` | `1.0.0` | `4.0.0` |
| `@zxio/theme-air-gray` | `1.0.0` | `4.0.0` |
| `@zxio/theme-pap-olive` | `1.0.0` | `4.0.0` |
| `@zxio/theme-rocket-moss` | `1.0.0` | `4.0.0` |
| `@zxio/theme-factory-blue` | `1.0.0` | `4.0.0` |
| `@zxio/theme-tech-blue` | `1.0.0` | `4.0.0` |
| `@zxio/theme-industrial-blue` | `1.0.0` | `4.0.0` |

升级时应核对安装后的 manifest identity 与本记录。experimental 身份变化不能按永久兼容接口处理：先检查库迁移说明和业务 surface 消费点，再重验登录/主框架/代表表单的明暗、浮层归属和 density，随后更新这份记录及本地包收据。不要只比较版本字符串或假定同名 token 的行为永久不变。

使用的正式入口仍为公开 `emitThemeDeployment`、`createThemeDeploymentResolver` 与 Host/Provider。业务源码不复制生成目录、不反向写核心变量、不通过 declaration merge 掩盖类型缺口。

相关文档：ZXUI `docs/zh-CN/guide/theming.md` 的“业务主题扩展”说明 experimental 身份边界；本业务设计见 `docs/specs/zxui-form-dialog-convergence/design.md` 的“公开主题接入与可交付资产”。
