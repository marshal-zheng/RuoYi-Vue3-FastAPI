# 导航统一配置与验证记录（2026-10-22）

统一入口：[navigation-tokens.css](../../ruoyi-fastapi-frontend/src/assets/styles/navigation-tokens.css)。

本轮仅修改业务导航。ZXUI 没有新增若依、ThingsBoard、菜单路由或侧栏规则；业务通过既有公开语义令牌消费主题。导航的尺寸、状态映射和动效不再分散声明在各组件中。

## 怎么调整

直接修改入口文件中的既有变量声明，不要再到 Sidebar、Navbar、Hamburger 或浮层样式中追加数值。尺寸默认值位于 `:root`；主题相关映射在同文件的主题作用域重绑。前者能继承到所有主题 Host，后者在各 Host 内消费正确主题，传送到 body 的菜单也读取同一配置。这沿用 [CSS 自定义属性的继承与作用域机制](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Cascading_variables/Using_custom_properties)。

| 可调项 | 入口中的变量 | 当前默认值 / 映射 | 生效范围 |
| --- | --- | --- | --- |
| 侧栏宽度 | `--app-nav-sidebar-width`、`--app-nav-rail-width` | 展开 250px，收起 50px | 侧栏、header/main 对齐、折叠过程、移动抽屉；浮层默认宽度从展开宽度派生 |
| 菜单图标 | `--app-nav-icon-size`、`--app-nav-icon-gap` | 24px；间距由基础间距派生，默认 12px | 侧栏、TopNav、顶部更多菜单；缩进和图标栏居中随之计算 |
| 行高与基础间距 | `--app-nav-item-height`、`--app-nav-space`、`--app-nav-item-gap` | 44px；基础间距 4px；行间距 4px | 展开/收起/移动菜单、两类浮层；header 与内容间距也由基础间距派生 |
| 背景边距 | `--app-nav-item-inset` | 0px | 菜单 hover/active 背景铺满内容区；文字缩进独立计算 |
| 层级缩进 | `--app-nav-content-start`、`--app-nav-child-content-start`、`--app-nav-nesting-step`、`--app-nav-guide-start` | 默认文字起点 22px；子项 66px；每层 16px；根辅助线 34px，均从基础间距和图标计算 | 各层文字、箭头与辅助线，不缩窄选中背景 |
| Header 与折叠入口 | `--app-nav-header-height`、`--app-nav-control-size`、`--app-nav-control-end` | 56px；按钮 40px；位置从收起宽度和按钮尺寸计算 | header、侧栏品牌区、移动恢复入口与左右对齐 |
| 品牌图与辅助图标 | `--app-nav-brand-size`、`--app-nav-compact-logo-size`、`--app-nav-action-icon-size`、`--app-nav-chevron-size` | 品牌 32px、收起 Logo 28px、用户图标 20px、箭头 15px | 本轮导航品牌与操作区 |
| Hover | `--app-nav-hover-fill`、`--app-nav-hover-text`、`--app-nav-group-hover-fill` | 主题 hover 填充、主题表面强调文字；展开的分组标题默认透明背景 | 侧栏叶子、图标栏、TopNav、两类浮层；分组标题仍保留 ThingsBoard 的标题语义 |
| Active | `--app-nav-active-fill`、`--app-nav-active-text`、`--app-nav-active-highlight`、`--app-nav-active-shadow` | 现有主题 selected 表面对应角色 | 侧栏选中叶子、收起组选中、TopNav、两类浮层 |
| 指示条 | `--app-nav-indicator-width`、`--app-nav-indicator` | 3px、主题强调色 | 侧栏与浮层的左标记、TopNav 下划线 |
| 圆角与焦点 | `--app-nav-item-radius`、`--app-nav-control-radius`、`--app-nav-focus-width`、`--app-nav-focus` | 菜单圆角 = 主题 control 圆角 × 1.5（默认主题为 6px）；折叠按钮圆形；焦点宽度 2px、主题焦点色 | 菜单状态区域及导航按钮 |
| 字体 | `--app-nav-font-family`、`--app-nav-font-size`、`--app-nav-font-weight`、`--app-nav-emphasis-weight` | 字体/字号/强调字重消费主题，普通字重 400 | 菜单与导航操作区 |
| 品牌与面包屑文字 | `--app-nav-brand-font-size`、`--app-nav-brand-line-height`、`--app-nav-brand-font-weight`、`--app-nav-breadcrumb-current-size`、`--app-nav-breadcrumb-muted-opacity` | 主题 medium 字号、主题行高、品牌字重 600；面包屑末级用主题 large 字号，其他层级透明度 0.7 | header 品牌和面包屑 |
| 动效总倍率 | `--app-nav-motion-scale` | 1；非负，0 关闭导航过渡 | 侧栏宽度、子菜单、间距、箭头、Logo、hover/active、面包屑、两类导航浮层、移动抽屉及遮罩 |
| 各类动效时长 | `--app-nav-motion-fast`、`--app-nav-motion-control`、`--app-nav-motion-panel`、`--app-nav-motion-group`、`--app-nav-motion-arrow` | 基础/快速时长消费主题并乘总倍率；整栏 ×2、分组 ×2.5、箭头 ×1.5 | 同一入口可分别调各类节奏；默认主题整栏 360ms、分组 450ms，森绿随主题变为 280ms、350ms |
| 动效曲线 | `--app-nav-ease-panel`、`--app-nav-ease-group`、`--app-nav-ease-control`、`--app-nav-ease-state` | 整栏 `.25,.8,.25,1`；分组 `.35,0,.25,1`；控件 ease-in-out；状态 ease | 对应导航过渡，不再在组件中散写曲线 |
| 响应式分界 | `--app-nav-mobile-breakpoint` | 992，单位为 CSS px 的数值 | 应用设备判定及对应移动 header 组合；调整后刷新或改变视口应用判定 |
| 导航层级 | `--app-nav-header-layer`、`--app-nav-sidebar-layer` | 9、1001 | header、隐藏 header 的恢复入口与侧栏 |
| 浮层/滚动条/文字截断 | `--app-nav-popup-min-width`、`--app-nav-scrollbar-size`、`--app-nav-scrollbar-track`、`--app-nav-scrollbar-thumb`、`--app-nav-avatar-max-width` | 浮层默认继承侧栏展开宽度；滚动条由间距派生并消费主题色；昵称上限 12em | 两类导航浮层、导航操作区 |

系统开启“减少动态效果”时，统一入口将导航快速/基础时长归零，派生时长与两类浮层一起停用。菜单是否只展开一条分组路径继续由业务 `src/settings.ts` 的 `uniqueOpened` 控制。整体复核及后续修复见 [Header / Sidebar 复核记录](2026-10-22-navigation-final-review.md)。

颜色与材质优先调整这里对现有主题角色的映射，不在业务中覆盖核心 `--zx-*` / `--el-*`，不复制 ThingsBoard 的配色。登录品牌尺寸仍由登录变体拥有；通用组件内部行为继续由组件库拥有。

## 对齐结果与实现边界

- 本地 ThingsBoard 桌面规则实际为展开 250px、收起 50px、图标 24px；名义的 200px token 被桌面规则覆盖，未机械照抄。
- 按用户明确要求消除选中区域两侧空隙。修改前左侧 51px、右侧 11px；现在左侧 0px，右侧仅有侧栏自身 1px 分隔边，内容区内没有间隙。浮层行左右均为 0px。
- 内容与辅助线按数字 depth 递归缩进，背景独立铺满行。分组标题与叶子选中语义参考 ThingsBoard；颜色、圆角、字体和节奏继续消费当前主题。
- Sidebar、Navbar、Hamburger、TopNav、Breadcrumb 及导航浮层消费统一变量。仅通过 ElMenu 公开 `popper-class` 让顶部更多菜单接入同一配置，没有新增库 API。
- 删除已无消费者的 `variables.module.less`，清除旧菜单宽度/配色的误导入口；旧导航别名和面包屑动效的散落定义已移除。

## 验证

- 真实业务源码直连 ZXUI，资源路径记录在 checks.json。浏览器运行错误 0。
- 38 项检查通过，包括默认/森绿深色、hover/active、各级背景范围、50px 图标栏、层级缩进、Logo hover、键盘、反向收起、移动焦点/Escape、TopNav、浮层和系统减少动态效果。
- 只在根节点覆盖一组几何值：300px 展开、64px 收起、28px 图标、48px 行高、64px header、5px 基础间距。侧栏、header、菜单、浮层同步更新；浮层宽度 300px、行高 48px、行间距 5px。
- 在一份全局配置块中替换 hover/active 映射、圆角和动效倍率，侧栏与浮层共同变化；panel、row、arrow、toggle、breadcrumb 均为 0s。顶部更多菜单也验证了 28px 图标、20px 字号、44px 行高、同一 hover 与 0 动效。
- 移动导航面板及遮罩都消费倍率：设 0 后没有活动动画；恢复 1 后两者都使用默认主题 180ms。OS reduced-motion 同时禁用两者。
- 只编辑入口文件的行高 44→46→44，页面通过 HMR 更新并恢复，未改任何额外文件证明联动。
- 临时覆盖均已移除，最终恢复 250/50px、24px 图标、44px 行高、56px header 与主题正常动效。
- 目标文件 ESLint、前端 type-check、diff 空白检查通过；既有 Hamburger/layout policy 共 10 项测试通过，未增加新测试套件。
- 独立复核发现并修正了移动端 scoped CSS、顶部浮层原生 36px 行高以及移动遮罩动效遗漏。最终无剩余 P1/P2。
- 全工作区 convention 脚本仍有既有 3 项问题：缺失的 `AlarmPanelFloating.vue`、`FaultBoardPanel.vue` 裸色规范、`session.test.ts` axios 规范；未宣称全工作区门禁通过。

## 证据

- [完整检查、配置覆盖和帧记录](navigation-contract-2026-10-22/checks.json)
- [默认选中区域](navigation-contract-2026-10-22/default-expanded.png)
- [默认 hover 与 active](navigation-contract-2026-10-22/default-hover.png)
- [50px 图标栏](navigation-contract-2026-10-22/default-rail.png)
- [森绿深色状态](navigation-contract-2026-10-22/army-dark-hover.png)
- [移动导航](navigation-contract-2026-10-22/army-dark-mobile.png)
- [全局几何覆盖](navigation-contract-2026-10-22/global-override-popup.png)
- [全局状态覆盖](navigation-contract-2026-10-22/global-state-override.png)
- [顶部更多浮层覆盖](navigation-contract-2026-10-22/global-topnav-popup.png)

## Plan-stage checkpoint

STATUS: PLAN_DRAFTED
FILES_WRITTEN: docs/plans/2026-10-22-navigation-contract.md
EVIDENCE: READ local ThingsBoard shell/menu and current business navigation; SEARCH existing aliases and consumers; COMMAND plan structure checks passed.
PLAN_CHANGES: Central app-owned defaults and public theme-role mapping; migrate consumers; verify source-linked business and global overrides.
WORK_ITEM_SYNC_SUGGESTION: none
NEXT_ACTION: current-session execution (subsequently performed; execution evidence is recorded above)
BLOCK_REASON: none
UNBLOCK_ACTION: none
