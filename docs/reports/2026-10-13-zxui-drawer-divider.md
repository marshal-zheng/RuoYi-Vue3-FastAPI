# ZXUI Drawer 与 Dialog 分隔线统一

本轮完成 ZXUI 公共契约、CSS 样式、文档和业务接入。Drawer 的有效默认值为 `false`；组件配置优先于最近的 ConfigProvider，省略或恢复 `undefined` 时继续继承。未提交或发布，保留两个 checkout 的其他已有改动。

## 公共能力与样式

ZXUI 源码位于 `/Users/hqz/Downloads/element-plus`：

- `ZxDrawer` 声明可选 `divider`，通过 computed 根类控制分隔线，不向原生 Drawer/DOM 泄漏属性。
- `ZxConfigProvider` 的 `zxDrawer.divider` 纳入公共类型、嵌套深合并和 Element Plus 配置投影排除。未配置时有效值为 `false`。
- `useDrawer({ divider })` 支持布尔值、ref 和 `updateOptions`，保留 `undefined` 的继承语义。
- modal、inline、push 共用同一分隔线契约。没有增加 watcher、ResizeObserver、全局监听、RAF 或 DOM 测量。

```vue
<ZxConfigProvider :zx-drawer="{ divider: true }">
  <ZxDrawer title="继承全局配置" />
  <ZxDrawer title="单独关闭" :divider="false" />
</ZxConfigProvider>
```

Drawer 原先无条件绘制 header/footer 边框，现在仅在开启 divider 时绘制。样式优先级为分区变量 `--zx-drawer-header-divider` / `--zx-drawer-footer-divider` → Drawer 变量 `--zx-drawer-divider` → 公共 `--zx-overlay-divider` → 与 Dialog 相同的主题默认线条。默认线条使用 blocking surface 的 on-text 色、18% 透明度和 1px 宽度。

Dialog 保留现有开关、组件变量与默认行为，增加同一公共样式 fallback。MessageBox 原先复用 Dialog 变量的两处分隔线也接入公共 fallback，保持该样式家族一致，没有改变其显隐策略。ZXUI 拥有通用能力；业务无需声明替代类型或写内部样式。

修改 structural CSS 的源文件后通过官方脚本生成 aggregate mirror，并检查 Drawer/Dialog leaf 样式包含相同规则。中英文 Drawer、Dialog、ConfigProvider 文档及可交互示例已补齐默认值、继承、迁移和变量说明。

## 业务显式选择

按用户后续要求，业务 App 的 ConfigProvider 通过同一个 `overlayDividers = { divider: true }` 配置 `zxDialog`、`zxDrawer` 和 `modal`，业务浮层默认显示分隔线。ZXUI 库自身的默认值仍为 `false`。以下 5 个编辑 Drawer 保留 `useDrawer` 的显式 `divider: true`，用于分开长表单、权限树或模板编辑内容与固定操作栏：

- `src/views/system/role/components/RoleDataScopeDrawer.vue`
- `src/views/system/menu/components/MenuDrawer.vue`
- `src/components/business/Protocol/ProtocolFormDrawer.vue`
- `src/components/business/Device/PortConfigDrawer.vue`
- `src/views/project/components/ProtocolConfigDrawer.vue`

`src/views/system/role/components/RoleFormDrawer.vue` 已移除局部 `divider: true`，现在真正继承业务全局配置。用户已通过「系统管理 → 角色管理 → 新增」亲自看到分隔线效果。该调整后的聚焦 ESLint 为 0 errors、1 个已有 props unused warning，现有 RoleFormDrawer 测试 5/5 通过；原始日志为 `/tmp/ruoyi-drawer-global-role-lint.log` 和 `/tmp/ruoyi-drawer-global-role-test.log`。

截图对应的 `NodeEditDrawer.vue` 单独显式设置 `divider: false`，覆盖业务全局开启；在工程拓扑中双击节点即可打开，用于用户亲自对比。分组列表 `Device/ProtocolListDrawer.vue` 的源码同样继承业务全局开启，内部卡片自己的分组边框保留；但此前提供设备列表入口时仅核对了源码，遗漏了当前菜单。续接时只读查询本地 `sys_menu`，路径或组件含 `device`、名称含「设备」的记录数为 0；角色管理记录存在（menu_id=101，path=role，component=system/role/index）。因此实际可访问验证入口以角色新增为准，没有为验证分隔线补建或恢复设备菜单。未修改仿真专用组件。

App 与 NodeEditDrawer 的配置调整已通过聚焦 ESLint（0 errors、1 个已有 warning），Vite 实际交付的两个模块均编译成功。业务服务按工作区规定启动在 80/8088；本次仅同步计划与报告，重新确认前端 `http://localhost:80`、后端 `http://localhost:8088/docs` 均为 HTTP 200，Docker `ruoyi-mysql-local` 仍在运行。保持服务运行，未操作用户现有浏览器。整体 changed validation 仍有工作区其他路径的既有 lint 阻塞。

业务通过新的 `vendor/zxio-zxui-3.0.0-next.0-divider.20261013.tgz` 消费公共组件、类型和样式，`package.json` / `yarn.lock` 已更新并安装成功；上一轮布局交付的 hooks resolution 保留。该产物来自当前 checkout，包含其中已有实现，未发布 registry 包。

## 验证结果

| 检查 | 结果 |
| --- | --- |
| TDD 契约测试 | 实施前确认 4 处有效失败，再验证修正 |
| ZXUI Drawer、ConfigProvider、useDrawer、Dialog 回归 | 15 文件，135/135 测试通过 |
| RoleFormDrawer 回归 | 5/5 测试通过 |
| 业务 UI standards | 505 文件，0 违规；相关 14/14 测试通过 |
| ZXUI 聚焦 ESLint | 0 errors |
| 初始 6 个编辑路径 ESLint | 0 errors，保留 2 个已有 warnings；当前为 5 个显式 true + RoleFormDrawer 继承 |
| RoleFormDrawer 移除局部 true 后 ESLint | 0 errors，保留 1 个已有 warning |
| 新浏览器夹具与脚本 ESLint | 0 errors；脚本输出证据的 console 有 1 个 warning |
| ZXUI 构建 | `pnpm build` 通过 |
| 公共 UI 包契约和 build externals | 聚焦检查通过 |
| 业务源码模式生产构建 | 通过，28.03s |
| 安装包 Drawer 夹具生产构建 | 通过，5.00s |
| 独立只读审查 | 无实质问题；另外独立检查配置继承、变量、滚动和主题 |
| 本轮路径 diff 空白检查 | 通过 |

隔离 Chromium 147.0.7727.15 使用真实 Drawer/Dialog/Provider/Hook 和真实业务 ThemeHost。源码模式与安装包模式各验证 26 组矩阵：18 组模式与配置优先级、6 组额外方向与显隐、2 组浅色/深色主题颜色一致性。另验证自定义 footer、footer 关闭、标题内容隐藏、整个 header 移除、长短正文、Hook 更新、CSS 变量覆盖、全屏、拖拽尺寸/复位和 390px 移动端。两种模式均无 pageerror。

普通边框参与正常布局：开启后头尾各占 1px，900px 外层高度保持不变，正文从 786px 调整为 784px。header/body/footer 的 padding 不变；正文接收剩余高度并独立滚动，外层不产生额外滚动，切换 divider 后正文 scrollTop=300 保持。不存在通过 JavaScript 测量边框再扣减高度的路径。

沿用现有 `noTitle` 语义：只隐藏标题内容，header 仍承载关闭按钮；`with-header=false` 才移除整个 header。缺少 header/footer 时没有对应分隔线。

### 性能与生命周期

40 次逐帧 divider 切换前后，源码与安装包模式的 ResizeObserver 创建数、IntersectionObserver 创建数、全局监听注册数、活跃监听、活跃观察目标和整页 `getBoundingClientRect` 调用数均保持不变。已有 3 个活跃观察目标来自组件及依赖的现有行为，本轮 divider 增量为 0。

5 次关闭→打开→关闭后，活跃观察目标仍为 0，活跃全局监听仍为 18。重新打开组件会按原生命周期创建并清理资源，累计创建数会增加，但关闭后没有活跃资源累积。

两种模式动画结束后 500ms 空闲 LayoutCount 均为 0；40 次显隐均对应 40 次正常布局，总 LayoutDuration 分别为源码模式 2.457ms、安装包模式 2.808ms。显隐仍会引起必要的浏览器布局；没有额外测量链或持续重排任务。

耗时仅为本机带探针的诊断值，不是跨设备基准或与旧版本的帧率对照。探针保留观察器实例以统计目标，无法据此证明垃圾回收或所有第三方组件都无内存泄漏。源码栈归属的 ownedBounds/ownedRaf 不用于安装包压缩栈判断；两种模式的整页 totalBounds 均用于切换增量验证。

## 验证边界

- `yarn type-check` 仍报两个已有错误：`src/utils/http.test.ts:31` 调用参数不匹配；`vite/zxui-theme-packages.ts:54` featurePackages 类型不接受 theme-tailwind。本轮 Drawer 路径没有新增类型错误。
- `bash .agents/skills/frontend-conventions/scripts/validate.sh --changed` 的 lint 收集了工作区其他已有修改，仍失败；初始 6 个编辑路径的聚焦检查通过，RoleFormDrawer 改为全局继承后也通过聚焦检查。没有据此宣称全项目 lint 通过。
- 此前已确认普通安装包业务生产构建被旧 vendor Theme Manifest 的 elementPlus/tailwind adapter identity 校验阻塞。本轮完整业务生产构建使用源码模式；安装包夹具使用新安装的 ZXUI 组件/样式和当前 checkout 公开 deployment 生成的主题资产。因此安装包夹具通过不等同于普通安装包业务生产构建通过。
- 没有重新运行上一轮已记录范围外失败的全量业务测试；本轮运行并通过受影响的聚焦测试和 UI 标准检查。

## 复现与证据

```bash
# ZXUI checkout
pnpm exec vitest run packages/components/drawer/__tests__ packages/components/config-provider/__tests__ packages/components/hooks/use-drawer/__tests__ packages/components/dialog/__tests__/dialog.integration.test.tsx
pnpm exec tsx packages/theme-chalk/scripts/build.ts --out-dir /Users/hqz/Downloads/element-plus/packages/theme-chalk/dist --update-mirror
pnpm build
node --import tsx scripts/contracts/check-ui-package-contracts.mjs --packages @zxio/zxui,@zxio/components
node --import tsx scripts/contracts/check-ui-build-externals.mjs --packages @zxio/zxui

# Business frontend
yarn vitest run tests/unit/components/RoleFormDrawer.test.ts
yarn ui:standards
yarn type-check
VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus yarn build:prod
```

- [实施计划与完成证据](../plans/2026-10-13-zxui-drawer-divider.md)
- [隔离夹具及运行说明](../../ruoyi-fastapi-frontend/tests/fixtures/drawer-divider/README.md)
- [浏览器检查脚本](../../ruoyi-fastapi-frontend/scripts/check-drawer-divider.mjs)
- [源码模式原始数据](evidence/2026-10-13-zxui-drawer-divider/browser.json)
- [安装包模式原始数据](evidence/2026-10-13-zxui-drawer-divider/installed/browser.json)
- [默认关闭效果](evidence/2026-10-13-zxui-drawer-divider/disabled.png)
- [显式开启效果](evidence/2026-10-13-zxui-drawer-divider/enabled.png)
