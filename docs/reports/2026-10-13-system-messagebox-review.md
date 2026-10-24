# 系统提示弹框整体评估

日期：2026-10-13。范围：ZXUI 的 MessageBox 默认布局，以及若依用户管理的删除、启用和停用确认。延续业务直连 `/Users/hqz/Downloads/element-plus` 源码的验证方式。

## 结论与责任归属

桌面横向 24px、小屏 16px，以及墨青默认密度的 92px 正文下限可以保留。原有问题主要在 ZXUI 默认结构：关闭按钮定位没有跟随标题区中心；分隔线开关承担了部分区域布局；多行提示图标居中于整个段落；footer 的按钮间距和小屏点击区域缺少统一收敛。业务的问题是通用“系统提示／确定”文案没有表达具体操作。

本轮调整结构与具体业务文案，没有继续扩大正文下限，也没有把 footer 按钮强制改成统一的大号。分隔线继续复用 Dialog 的轻量线条与主题角色；标题、内容和操作区的层级主要由排版与留白建立。

这些是基于既有设计体系、源码和尺寸计算的判断，不是对真实浏览器渲染效果的验收。此次未使用 computer use，未进行页面视觉、键盘或触摸复测。

## 设计依据

- [Fluent 2 Dialog](https://fluent2.microsoft.design/components/web/react/core/dialog/usage) 将标题、正文和操作区作为完整结构，要求标题与操作文案具体，长正文滚动时保留标题和操作区；没有 footer 时应保留额外底部留白。本轮采用这些结构原则。
- [Carbon Modal specifications](https://www.carbondesignsystem.com/building-blocks/core/components/modal/specifications) 给出了自己的边距和点击区域规格。这说明成熟体系会建立一致的容器与操作网格，并不意味着不同产品都必须使用同一个正文最小高度。ZXUI 的数值继续结合现有密度和显示度量选择。
- [WAI-ARIA Dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/) 要求合理设置初始焦点、保留键盘导航与焦点恢复，并建议不可逆操作考虑最不具破坏性的初始焦点。当前原生公开 API 的 `autofocus: false` 只会将初始焦点留在容器，不等同于聚焦取消按钮。
- [WCAG 2.2 Target Size Minimum](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html) 的 AA 基础目标是 24px，另有间距等例外。本轮小屏采用 44px 作为更舒适的点击目标，不将其表述为 AA 强制值。

## 默认布局决策

以下数值针对 office / 100%、正常按钮尺寸、单行标题和短消息，且视口高度足够。区域高度不包含分隔线；这不是浏览器测量值。

| 项目 | 墨青默认密度 | 判断与调整 |
| --- | --- | --- |
| 左右 padding | 桌面 24px；小屏 16px | 保留。标题起点、正文区域起点、footer 末端共用网格；提示图标后的文字有自然缩进。横向边距不随密度压缩。 |
| 标题区 | 约 48px；标题 18px / 行高 24px / 主题 primary 字重 500 | 保留适量上下留白。关闭按钮改为相对标题区垂直居中；长标题保留独立关闭空间。 |
| 正文区 | 最小 92px；上下 padding 默认 16px | 保留弹性下限。短内容作为整体居中，多行内容自然撑开；提示图标对齐首行。不要继续堆空白高度。 |
| footer | 约 51px；上下 padding 各 10.5px | 与约 48px 的标题区接近，比例协调。继续消费密度，避免独立的大块 padding。 |
| footer 按钮 | 正常尺寸高 30px；最小宽 64px；间距 8px | 桌面保留全局尺寸与密度。小屏点击高度至少 44px，按钮组宽度不足时换行。 |
| 关闭按钮 | 图标尺寸消费主题默认图标角色；桌面点击区域 40px，小屏至少 44px | 使用与 Dialog 相同的 regular SVG；保留中性颜色、hover 和 focus-visible 反馈。显式 closeIcon 优先。 |
| 分隔线 | 与 Dialog 共用三个外观变量 | 只控制线条；开关不再切换头尾 padding、横向铺开方式或关闭位置。线条本身仍占据其边框宽度。 |

墨青三种密度的计算：

| 密度 | 标题区 | 正文下限 | footer | 正常按钮高度 | 含两条默认 1px 分隔线的总高度 |
| --- | --- | --- | --- | --- | --- |
| compact | 48px | 84px | 41px | 26px | 175px |
| default | 48px | 92px | 51px | 30px | 193px |
| comfortable | 51px | 100px | 61px | 34px | 214px |

default 主题对应总高度为 184 / 202 / 226px，正文下限为 88 / 96 / 104px。不同主题继续消费自己的语义密度，不为了凑同一像素值覆盖主题。

正文下限包含内边距，并受 30dvh 上限约束；长内容正常在正文区域滚动。极矮窗口可滚动整个框，避免标题和操作区合计已超出视口时裁掉按钮。无 footer 时，正文底部默认 padding 至少为 24px；显式正文 padding 仍优先。

## 配置与实现位置

长期公共入口继续使用 CSS 变量，并通过已有 Provider / Hook 的 `customStyle` 传递，无需增加互相重叠的布局布尔开关：

| 变量 | 用途 |
| --- | --- |
| `--zx-message-box-padding-x` | 横向共用网格 |
| `--zx-message-box-header-padding-y` | 标题区上下留白；关闭按钮所需最小高度仍保留 |
| `--zx-message-box-body-min-height` | 正文弹性高度下限 |
| `--zx-message-box-body-padding-y` | 正文上下留白 |
| `--zx-message-box-footer-padding-y` | footer 上下留白 |

`modal.customStyle` 提供 ConfigProvider 默认值，`useZxFeedback().modal.confirm({ customStyle })` 提供单次覆盖。分隔线仍由 `modal.divider` 控制，外观复用 `--zx-dialog-divider`、`--zx-dialog-header-divider` 和 `--zx-dialog-footer-divider`。调用者的自定义图标和 class 保留。

修改位置：

- ZXUI：`packages/theme-chalk/src/structural.css`，作为结构源文件。
- ZXUI：`packages/components/_shared/close-icon.vue`，供 Dialog 与主题反馈 MessageBox 共用；Dialog 的旧局部默认图标迁至此处。
- ZXUI：`packages/components/theme-provider/src/feedback.ts`，提供默认关闭 SVG，修正内部反馈返回值类型。
- ZXUI：中英文 `docs/*/component/config-provider.md`，同步配置、密度与焦点语义。
- 业务：`ruoyi-fastapi-frontend/src/views/system/user/index.vue`，改为“删除用户／删除”“停用用户／停用”等明确文案，批量删除显示数量。

删除与停用确认取消自动聚焦确认按钮。删除还关闭点击遮罩取消，保留显式取消、关闭和 Escape。原有取消／关闭拒绝 Promise、删除成功才刷新、状态取消后恢复的业务契约不变。

## 仍值得继续优化的业务体验

1. 其他页面仍有“系统提示／确定”和编号式消息，应由各业务操作提供具体标题、对象与动作，不能靠组件库猜消息文字。此次只调整截图涉及的用户管理操作，未机械替换所有页面。
2. 破坏性操作可以进一步提供明确的危险按钮语义，以及可配置的取消优先焦点。当前 native MessageBox 公开 API 不提供统一的确认按钮类型和取消初始焦点；本轮没有叠加冲突 class 或访问内部 ref。删除按钮目前仍使用原生 primary 外观，不能据此声称已经具备危险操作的完整视觉与焦点策略。
3. 普通非阻断成功消息可评估使用 toast；需要阅读并确认的重要结果仍适合弹框。应按具体业务选择，不全局替换 alertSuccess，例如包含用户必须阅读信息的反馈。
4. 直接调用 ElMessageBox 的其他消费者仍不读取 ZXUI Provider 默认选项；主题结构样式可覆盖，divider 等选项需走既有反馈入口。

## 验证证据

- 既有反馈与 Provider 用例：3 个文件、13 项通过。
- 既有 Dialog 原生关闭保护与本地化关闭名称用例：4 项通过，其余 34 项未运行。
- 三个 Vue SFC 的 script/template 编译与反馈 TypeScript 语法转换通过；未运行完整 type-check。
- PostCSS 解析通过；检查区域居中、分隔线只承担边框、全局按钮高度保留和小屏点击目标。
- 9 个主题 × 2 个模式 × 3 个密度，共 54 个现有变体计算通过；另检查 72 种尺度／横向边距／图标尺寸组合的关闭区域几何关系。数值检查不等同于渲染测试。
- 临时执行真实用户页的删除、批量删除、启用、停用函数，共 12 种 confirm/cancel/close 场景通过；API 均使用桩，未删除或修改真实数据。
- 本机首页、后端 `/docs` 返回 200；Vite 返回更新后的用户页、共享 SVG、Dialog、反馈源码与结构 CSS，确认直连 ZXUI 源码链路。
- 两个仓库 `git diff --check` 通过。

未新增测试文件，未运行 lint、build 或浏览器操作；未编辑 generated 样式产物。页面实际观感、完整键盘行为及触摸体验需另做真实渲染验证。
