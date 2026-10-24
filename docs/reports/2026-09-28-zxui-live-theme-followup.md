# 业务主题与用户管理按钮复核

> 后续更正：颜色来自主题，不代表每个状态的显示效果都正确。用户追加深色按钮截图后，确认了 ZXUI 实心按钮禁用文字沿用品牌文字色的缺陷，并已在组件库修正。详见 [按钮禁用文字修正](2026-09-28-zxui-button-disabled-foreground.md)。下文保留初次排查的范围与证据；其中“没有修改 ZXUI”仅指初次业务排查阶段。

## 结论与证据边界

当前业务已登记全部 9 套内置主题：default、defense-green、army-pine、air-gray、pap-olive、rocket-moss、factory-blue、tech-blue、industrial-blue。没有发现“某一套主题未接入”的配置缺口。问题按消费者分布，同一个固定白底会影响多套主题。

运行中的 `http://localhost/src/main.ts` 确认 `@zxio/zxui` 和其样式入口指向 `/Users/hqz/Downloads/element-plus/packages/`。本轮检查源码、运行中 Vite 模块输出和用户提供的截图；未取得本轮浏览器自动化许可，未执行页面操作或声称完成浏览器视觉验收。旧报告的浏览器证据仅作历史线索。

两仓开始时已有大量修改。本轮保留既有工作，仅在业务 15 个 Vue 文件增加颜色修正；没有修改 ZXUI、按钮类型、主题种子或生成产物。

## 截图中的五个按钮

真实页面源码为 `ruoyi-fastapi-frontend/src/views/system/user/index.vue:4`，五个按钮都是 `ZxButton`，没有颜色内联覆盖。ZXUI `packages/components/button/src/button-core.vue` 将类型和 disabled 透传给 Element Plus，颜色来自 ZXUI 的主题适配产物。

| 按钮 | 业务声明 | 截图状态 | 颜色来源 |
| --- | --- | --- | --- |
| 新增用户 | primary | 可用 | 主题 accent，截图主体色为 RGB(102,148,112)，与 rocket-moss 深色主色一致 |
| 修改 | success | `single` 为真时禁用 | success 的禁用底色，截图 RGB(63,106,69) |
| 删除 | danger | `multiple` 为真时禁用 | danger 的禁用底色，截图 RGB(133,68,59) |
| 导入 | info | 可用 | 主题信息色，截图约 RGB(142,166,184) |
| 导出 | warning | 可用 | 主题警告色，截图约 RGB(225,169,53) |

截图各色与 `packages/theme-rocket-moss/generated/element-plus/resolved/mode-dark__density-default__contrast-normal__motion-full__radius-default.css` 的相应颜色一致或仅有 1/255 级别的像素取整差异。因此，从颜色来源判断，这组按钮已经跟随“火箭军苔藓绿”深色主题，并非业务写死的 Element Plus 默认配色。明亮实心按钮的黑字来自主题 foreground 配对，不能按“深色主题必须白字”判错。

这是依据截图色值与源码的判断，不是从浏览器读取当前主题身份。禁用态的鼠标反馈、选中用户后的状态与 hover/active 状态尚未现场验证。ZXUI 文档 `docs/examples/button/types.vue` 使用相同类型入口；本轮未操作 docs 页面做并排视觉验收。

从业务操作语义看，“修改=success、导出=warning”是当前页面的显式选择，不是组件库强制指定，也不表示所有操作都必须染成主色。本轮保留该产品选择。

## 侧边栏与顶部归属

当前源码中，顶部由 `layout/index.vue` 声明 `data-zx-surface="header"`，侧边栏由 `Sidebar/index.vue` 声明 `panel`，Logo 由 `Sidebar/Logo.vue` 声明 `brand`；颜色、边框、阴影来自 ZXUI 的 surface roles。内部菜单背景透明，交互态使用 selected 的 fill/on-text。

历史发现过 ZXUI 全局链接底色遮住 Logo brand 表面的缺陷；现有 `packages/theme-chalk/src/structural.css` 和生成镜像已经包含透明链接背景修复。本轮不能仅凭用户最初描述断言当前导航仍有同一个缺陷，也没有通过再加业务覆盖来掩盖它。仍需得到浏览器许可后，在用户所见主题和布局下复核当前计算样式。

## 本轮修正：业务所有

以下路径相对于 `ruoyi-fastapi-frontend/src/`。

| 消费者 | 确认的问题 | 修正 |
| --- | --- | --- |
| `components/ui/Pagination/index.vue` | 包装层固定白底 | 透明承接宿主表面，分页控件继续消费主题 |
| `components/ui/IconSelect/index.vue` | hover 与选中项固定浅灰 | hover 读取 fill-hover；选中项读取 selected fill/on-text |
| `components/ui/FileUpload/index.vue`、`ImageUpload/index.vue` | 大小/类型提示固定红色；文件列表固定灰边 | danger-on-surface 与 border-subtle |
| `components/ui/ImagePreview/index.vue` | 加载/失败占位固定灰底灰字与灰色光晕 | field fill/on-text-secondary/inner |
| `layout/components/Copyright/index.vue` | 开启页脚后固定浅灰背景 | header fill/on-text-secondary/edge |
| `components/business/Protocol/ImportFileDialog.vue` | 导入说明固定深灰字 | text-secondary |
| `components/business/Protocol/templates/` 下 Ethernet、CAN、RS422、1553B 四个协议模板 | 局部 VXE hover 固定浅灰，绕过已存在的统一适配 | 删除局部背景覆盖，由 `assets/styles/vxe-theme.css` 的行悬停变量负责 |
| `views/project/components/ProtocolConfigDrawer.vue` | 标题同时在 utility 与 scoped CSS 中写死深灰 | 单一 text-primary |
| `views/project/components/VersionList.vue` | 空态说明固定灰色 | text-secondary |
| `views/project/topo.vue` | 加载提示固定蓝白色块 | overlay fill/on-text/edge/depth |
| `views/tool/gen/editTable.vue` | 字段选项辅助说明固定灰色 | text-secondary |

这些都是业务组件的颜色消费问题，ZXUI 已提供对应角色，不需要改主题种子或给每套主题单独补丁。

## 扫描中保留的内容

- `FloatingPanel`、`HeaderSearch`、`Screenfull`、`ThemeValidation` 等仍包含固定色，但非仿真范围内只发现统一导出，没有确认实际页面调用。没有把导出等同于活动页面证据。
- `views/dashboard` 保留旧配色，当前静态路由入口已注释；动态后端是否再提供入口未实测。
- `DagMatrixView`、`DagMatrixViewSimple`、`DagSearchInput` 仍有固定 UI 色。当前 DAG 中矩阵弹框导入/挂载均已注释。复核调用链后，本轮撤回矩阵视图的试改，最终不触及该文件。
- 设备壳体、端口颜色、图数据与导出背景属于设备表现或持久化内容，没有机械替换成主题色。
- `simulation/**`、`.simulation-dark` 专用 VXE/NodeEditDrawer 材质、仿真结果与状态面板继续遵守既定排除范围。
- `theme.module.css`、`tailwind.css` 中的历史品牌色阶与 utility 定义仍存在；本轮没有做影响全部消费者的全局灰阶重映射。

## 本轮检查

- 15 个最终修改的 Vue 模块从运行中 Vite 取得 HTTP 200；其 14 个样式模块均取得 HTTP 200。生成器页面无本地样式块，其模板内联颜色经 SFC 转换。
- 最终修改文件引用的 17 个 ZXUI semantic token，在全部 9 个主题的公开 CSS 中均有定义。
- 聚焦 `git diff --check` 通过。
- 按用户要求，没有跑 lint、生产 build 或测试套件，没有新增测试用例。
- 没有刷新用户浏览器，没有变更用户主题偏好，没有保存业务数据；本轮浏览器验证仍待许可。

检查数据见 [source-check.json](evidence/2026-09-28-zxui-live-theme-followup/source-check.json)。以上证明源码接入与转换可用，不替代真实页面视觉验收。
