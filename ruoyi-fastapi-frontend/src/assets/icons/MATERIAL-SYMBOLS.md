# 导航 Material Symbols

采用 Google Material Symbols 标准款（materialsymbolsoutlined）实心资产：FILL=1、weight=400、optical size=24。仅本地保留导航及菜单选择所需的 31 枚 SVG，复用现有 sprite；不新增字体、图标包依赖或运行时在线请求。

来源仓库：https://github.com/google/material-design-icons
固定版本：`49d4db35df873165d6bd6ba09b063c7dafbac2f4`
源路径：`symbols/web/<name>/materialsymbolsoutlined/<name>_fill1_24px.svg`
版权归 Google / Material Design Authors；完整 Apache-2.0 许可见 LICENSE-MATERIAL-SYMBOLS。

导入时保留原始 path/viewBox，移除固定 width/height，fill 改为 currentColor。尺寸和颜色由 ZxIcon 与现有导航主题配置控制。静态 SVG 的形状与字重是已选资产的属性，不会随 CSS 字体轴动态变化。

业务映射唯一入口：`src/icons/navigation.ts`。菜单旧标识无需改库或数据库；Sidebar、TopNav、IconSelect 与菜单列表预览使用同一解析。明确的自定义图标继续走原有业务契约。Material 资产的 `material-symbols-` 前缀与原有本地 SVG 名称区分。

现有 sprite 会把目录内已选 SVG 一起注入，并非按当前视口可见数量懒加载。当前项目已有的旧 SVG 与 Element Plus 全量图标入口不由本轮删除；不能把本轮按需选择资产解释为整项目已经做到严格逐图标加载。
