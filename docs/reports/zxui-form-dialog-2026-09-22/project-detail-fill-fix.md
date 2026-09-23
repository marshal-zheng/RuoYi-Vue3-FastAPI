# 工程详情页满高链修复（B25）

2026-09-23。root真实浏览器发现工程详情DOM已有版本行，但表格/body/grid高度0且overflow hidden，克隆按钮无法点击；不是dialog.open失效。

独立读码确认：业务ContentDetailWrap声明data-zx-fill="anchor"，但本地 `.content-detail-wrap.is-fill { height:auto }` 的优先级高于库公开anchor `height:100cqh`。后代flex:1 1 0失去可分配空间，出现整页内容塌陷。此height:auto和fill迁移已存在本会话基线 `baseline/business.patch`，并非本轮删除EP dark/业务主题覆盖直接造成。

最小修复仅在 `ruoyi-fastapi-frontend/src/components/ui/ContentDetailWrap/index.vue`：旧height:100%限定非fill；删除fill的height:auto，让fill消费既有公开布局契约。AppMain提供size container，Card body/content和ZXUI Tabs/GridList已有完整flex列传递；ElSkeleton非loading不引入中间DOM层。没有改dialog hook、simulation或增加业务固定高度。

本人调用@vue/compiler-sfc parse/compileStyleAsync（Less + scoped）成功，确认最终fill不再被本地height声明覆盖。CSS布局需要真实浏览器，JSDOM不用于宣称视觉通过；root将复验B25页面尺寸、版本行及克隆入口。修复由本peer实施，明确自审边界。

非作者交叉复核：business_theme_deployment 只读核对非fill保持100%、fill消费库anchor及Card/Tabs/Grid的flex/min-height:0链，未发现新阻断问题。其结论仅代码层，真实浏览器仍由root复验。

真实复验：root于同一授权业务会话验证ContentDetailWrap高度869px、Grid高度683px（当时实际容器宽778px）；克隆dialog640px，必填、3字段输入及取消正常。证据 `browser/resumed/B25-clone-required.json/png` 与 `B25-clone-inputs.json/png`。该结果消除了本次页面塌陷，不等同所有工程互斥状态验收。
