# Drawer / Dialog 统一浮层布局

## 交付与范围

已在 ZXUI 组件库实现一套共享布局契约，当前业务安装本地构建包。用户后续明确授权在研阶段硬切，因此本轮清理旧布局入口，并同步已知调用；不保留旧布局行为分支。

库源码位于 `/Users/hqz/Downloads/element-plus`，业务位于本仓库。两个工作区原有未提交改动均保留；本轮以 `/tmp/zxui-overlay-layout-baseline-20261013` 的 27 文件快照界定增量。业务 `src/App.tsx` 原有 divider 配置未改动。没有提交、发布 npm 包、创建业务记录或修改仿真页面。

## 最终契约

| 责任 | 实现 |
| --- | --- |
| 默认四边留白 | 从所属主题的 density / display 间距角色派生，组件不写死 16/24px |
| 三段横向对齐 | header、正文和 footer 消费共享横向留白；LTR/RTL 使用逻辑边 |
| 分割线 | 画在分区边缘内；开关、粗细不改变正文几何或滚动位置 |
| 普通内容 | 两组件 `bodyScroll="auto"` 都使用正常文档流，正文视口负责滚动 |
| 编辑器、虚拟表格、分栏 | `bodyScroll="none"` 提供有界 flex 布局，内容自行管理滚动 |
| 配置层级 | 单实例 → `zxDialog` / `zxDrawer` → `overlayLayout` → 所属主题配方 |
| 覆盖粒度 | 共享 `paddingInline`；独立 `headerPadding`、`bodyPadding`、`footerPadding` |
| 参数形式 | CSS shorthand 字符串、非负 px 数字、逐逻辑边对象；支持 `var/calc/clamp` |
| 恢复与清零 | `undefined` 继承；`0` 清零；对象 `all` 重设基准后再覆盖指定边 |
| Hook | 两个 Hook 接受同名选项、ref 和 `updateOptions` |
| 嵌套弹层 | 单实例内部变量在每个根重置，选择器限定直接分区；Provider 正常继承 |
| 扩展 | 移动端 gutter、底部 safe-area、命中区下限；布局不依赖 ZXUI namespace |

主题默认配方先使用已完成 display 投影的间距角色；显式 API 长度保持原值，不重复缩放。公开组件角色包括 `--zx-overlay-padding-inline`、`--zx-overlay-{header,body,footer}-padding-block`，以及共享/逐区 divider 变量。

```vue
<ZxConfigProvider
  :overlay-layout="{ paddingInline: 'clamp(1rem, 2vw, 2rem)' }"
  :zx-dialog="{ bodyPadding: { blockEnd: '2rem' } }"
>
  <ZxDrawer :body-padding="{ blockStart: 0 }" />
  <ZxDialog height="70dvh" :body-padding="0" body-scroll="none">
    <BusinessEditor />
  </ZxDialog>
</ZxConfigProvider>
```

虚拟内容需要宿主、全屏或显式高度形成有限空间；滚动归属本身不将自然高度 Dialog 变为满屏。业务可以组合内部带留白区域、铺满区域和独立滚动区。默认 footer 合并底部安全区；没有 footer 时由正文默认留白合并。显式分区 padding 由调用者决定。

header/footer 保持可见溢出。原生 scrollbar 的实际占宽由既有 ResizeObserver 回调同步到逻辑边距，保持三段与正文 client area 对齐。自动滚动模式在既有 observer 上增加 body 观察目标；没有新增 observer 实例、全局监听或轮询。滚动探针为内容盒内绝对定位元素，不再占流或抵消 padding。

## 硬切迁移

- 移除 `noContentPadding`；统一通过 `bodyPadding: 0` 清空正文留白。
- 移除 `--zx-dialog-{header,body,footer}-padding` / `--zx-drawer-{header,body,footer}-padding` 专属 CSS 别名；分区覆盖走公共 API。
- 移除旧 divider 修饰类及 Drawer 专属 divider 别名；两组件使用共享 divider 状态和角色，逐区外观使用 `--zx-overlay-header-divider` / `--zx-overlay-footer-divider`。
- 库内 ConfirmInput、业务代码预览和 DagMatrixDialog 改为 `bodyPadding: 0`；ProtocolFormDrawer 删除旧布尔绑定。
- RoleFormDrawer 删除额外的 `padding: 0 4px`，正文跟随组件统一 gutter。

主要源码：

- `/Users/hqz/Downloads/element-plus/packages/components/_shared/overlay-layout.ts`
- `/Users/hqz/Downloads/element-plus/packages/components/_shared/use-modal-scroll.ts`
- `/Users/hqz/Downloads/element-plus/packages/theme-chalk/src/structural.css`
- ConfigProvider、Drawer/Dialog props/templates、两套 Hook、公共类型和双语文档/示例。

当前包：`ruoyi-fastapi-frontend/vendor/zxio-zxui-3.0.0-next.0-overlay-layout.20261013.tgz`；package.json/yarn.lock 已更新，现有 hooks resolution 保留。包 SHA256：`e16b07fde09db8ba426e86d0f73623790d7496678da23835799f0a617bec1ce0`。

## 验证

| 检查 | 最终结果 |
| --- | --- |
| 组件/Provider/Hook/ConfirmInput 功能回归 | 23 文件、176 项通过 |
| 更广 ConfirmInput 主题断言 | 176 通过、2 项既有失败，详见下文 |
| ZXUI 构建、公共包契约、build externals | 通过 |
| 源码布局浏览器矩阵 | 156 项通过 |
| 安装包布局浏览器矩阵 | 156 项通过 |
| 源码 / 安装包 divider 生命周期与交互 | 各 26 项通过 |
| 业务 RoleFormDrawer 回归 | 5 项通过 |
| 业务 UI standards | 505 文件、0 违规，14 项测试通过 |
| 本轮文件 ESLint | 0 error，保留已有警告和验证脚本 console 警告 |
| 源码业务生产构建、安装包夹具构建 | 通过 |
| 独立只读审查 | 硬切后的增量无剩余 P0/P1/P2 |
| 实际角色 Drawer / 用户 Dialog | 两主题 × 两组件 × 桌面/移动端，8 项通过；主题/模式归属、四边几何和零业务写入均断言 |

布局矩阵覆盖：1440/390 宽度、默认浅色/军绿深色、两组件、compact/default/comfortable、90/100/125 display scale 和 LTR/RTL。扩展场景检查 shorthand 变量、逐边继承/恢复、显式零、主题角色、距离场景不重复缩放、自然高度、委托滚动、经典 12px 原生 scrollbar、自定义 namespace、嵌套隔离和默认行内流。

40 次间距/divider 更新前后，observer、全局 listener 和几何读取计数相同。5 次关闭/重开循环后，关闭态 observer 目标为 0，活动全局 listener 数恢复基准。divider 性能验证的空闲 layout 数为 0。

浏览器验证使用独立 headless Chromium；真实业务验证只打开/关闭表单，不提交角色或用户记录。安装包夹具使用实际安装的组件/样式，主题通过当前源码 checkout 的公开 deployment API 交付；该项不等同于整套旧主题 vendor 的纯安装模式构建。

### 全局既有门禁问题

- `yarn type-check`：`src/utils/http.test.ts:31` 的调用签名，以及 `vite/zxui-theme-packages.ts:54` 的 `@zxio/theme-tailwind` 类型。新布局公共类型没有新增错误。
- 全工作区 changed gate：其他已修改文件存在 9 个格式错误，涉及 ModalFeedbackProvider、feedback presenter、device detail 和 editTable；本轮文件单独 lint 通过。
- 全库包契约：Drive 的未声明依赖与 Chart 的 dependencies 不完整；本轮 `@zxio/zxui` 目标契约通过。
- `ConfirmInput.theme.test.ts` 两项断言仍期望旧颜色混合百分比。失败所涉及的 surface/disabled 样式在本轮前后完全一致，已保存快照对照证据；本轮修改的 ConfirmInput 参数与绑定功能测试通过。没有用跳过或修改这些断言掩盖全局失败。

### 可复跑入口

业务目录：

```sh
node scripts/check-overlay-layout.mjs
OVERLAY_TEST_URL=http://127.0.0.1:4300 node scripts/check-overlay-layout.mjs
DRAWER_TEST_URL=http://127.0.0.1:4299 node scripts/check-drawer-divider.mjs
node scripts/check-overlay-business.mjs
```

启动布局夹具：`DRAWER_TEST_PORT=4299 vite --config tests/fixtures/drawer-divider/vite.config.ts`；安装模式额外设置 `DRAWER_TEST_INSTALLED=1` 并改用 4300。测试期间服务仅绑定 127.0.0.1。正常开发服务 80/8088 保留运行。

## 证据

- [军绿深色角色 Drawer](evidence/2026-10-13-zxui-overlay-layout/business/army-pine-drawer-desktop.png)
- [军绿深色用户 Dialog](evidence/2026-10-13-zxui-overlay-layout/business/army-pine-dialog-desktop.png)
- [军绿深色移动端 Drawer](evidence/2026-10-13-zxui-overlay-layout/business/army-pine-drawer-mobile.png)
- [军绿深色移动端 Dialog](evidence/2026-10-13-zxui-overlay-layout/business/army-pine-dialog-mobile.png)

- [源码矩阵](evidence/2026-10-13-zxui-overlay-layout/source/browser.json)
- [安装包矩阵](evidence/2026-10-13-zxui-overlay-layout/installed/browser.json)
- [源码 divider](evidence/2026-10-13-zxui-overlay-layout/divider-source/browser.json)
- [安装包 divider](evidence/2026-10-13-zxui-overlay-layout/divider-installed/browser.json)
- [实际业务](evidence/2026-10-13-zxui-overlay-layout/business/browser.json)
- 构建、测试、门禁和基准对照日志见同目录 `verification/`。

## 调研取舍

[Fluent 2 Drawer](https://fluent2.microsoft.design/components/web/react/core/drawer/usage) 明确分离 header/body/footer，并通过 DrawerBody 提供正文滚动；[Ant Design Drawer](https://ant.design/components/drawer/) 提供分区语义样式及分区 token；[MUI DialogContent](https://mui.com/material-ui/api/dialog-content/) 将 dividers、theme defaults 和实例样式作为独立定制入口。

基于这些公开设计，本轮选择共享默认配方、分区/逻辑边覆盖和独立滚动归属，并加入本项目需要的 divider 几何稳定、Provider 层级及主题作用域隔离。这是针对当前业务约束的工程取舍，浏览器证据验证的是本库实现。
