# Display Scaling 消费者清单（任务 1）

日期：2026-09-27。状态：源码盘点；除单独注明的用户列表外，下表仅证明组件/菜单来源，不表示比例适配通过。菜单来源为 `ruoyi-fastapi-backend/capabilities/modules/platform.module.yaml` 的可见、启用 C 项；前端 `src/store/modules/permission.ts` 在登录后按服务端菜单动态装载。部署数据库可另含菜单，所以源码页和运行时可达性分别记载。

缩写：UI=普通操作界面，展示=现有监控/展示用途，领域=业务数据/画布/文档，模型导出=后端或数据模型生成，渲染导出=当前或离屏图形生成。所有行的 Display Scaling 状态均为**待实施**，此前的 theme/density 证据不替代本功能的四档验证。`@zxio/zxui` 公开控件/Host 为通用 UI 接口；Element Plus 2.13.0 由 ZXUI 主题适配；VXE 4.17.15 由业务插件接入。

| 消费者 / 路由 | 组件与用途 | 所有者 / 尺寸接口 | 导出来源与状态 |
| --- | --- | --- | --- |
| `/system/user` | `system/user/index.vue`；UI 首条链，筛选、GridList、ElTable、分页、增改表单、下拉 | 业务布局 + ZXUI/EP；`UserFormDialog.vue` 用 FormDialog | Excel/API 模型导出；列表运行时可达，显示大小待实施 |
| `/system/role` | `system/role/index.vue`；UI 列表、权限抽屉 | 业务 + ZXUI/EP | 常规 API/Excel；待实施 |
| `/system/menu` | `system/menu/index.vue`；UI 树、表单 | 业务 + ZXUI/EP | 常规 API；待实施 |
| `/system/dept` | `system/dept/index.vue`；UI 树、弹框 | 业务 + ZXUI/EP | 常规 API；待实施 |
| `/system/post` | `system/post/index.vue`；UI 列表、弹框 | 业务 + ZXUI/EP | 常规 API/Excel；待实施 |
| `/system/dict` | `system/dict/index.vue`、`system/dict/data.vue`；UI 列表、字典数据 | 业务 + ZXUI/EP | 常规 API；待实施 |
| `/system/config` | `system/config/index.vue`；UI 筛选、列表、弹框 | 业务 + ZXUI/EP | 常规 API；待实施 |
| `/system/notice` | `system/notice/index.vue`；UI 公告、Quill 编辑工具栏与文档正文 | 业务接入 + Quill 1.2.0 | 文档正文是领域内容；Quill 工具栏待显示大小适配 |
| `/monitor/online` | `monitor/online/index.vue`；UI 在线用户操作 | 业务 + ZXUI/EP | 常规 API；待实施 |
| `/monitor/job`、`/monitor/job-log/...` | `monitor/job/index.vue`、`monitor/job/log.vue`；UI 任务和日志 | 业务 + ZXUI/EP | 常规 API/Excel；待实施 |
| `/monitor/druid` | `monitor/druid/index.vue`；监控外部页面 | 业务 iframe 外壳；内部来源单列 | 宿主页待实施；内部样式须核对同源/控制权 |
| `/monitor/server` | `monitor/server/index.vue`；真实 `getServer` 数据，办公操作兼远距离展示基准 | 业务 + ZXUI/EP | 数据模型；两场景及真机待实施 |
| `/monitor/cache`、`/monitor/cacheList` | `monitor/cache/index.vue`、`monitor/cache/list.vue`；监控操作 | 业务 + ZXUI/EP | 数据模型；待实施 |
| `/tool/build` | `tool/build/index.vue`；表单设计器 | 业务 + ZXUI/EP | 生成代码/配置是领域模型；UI 待实施 |
| `/tool/gen`、`/tool/gen-edit/...` | `tool/gen/index.vue`、`tool/gen/editTable.vue`；生成器 | 业务 + ZXUI/EP | 生成代码/模板是领域模型；UI 待实施 |
| `/tool/swagger` | `tool/swagger/index.vue`；iframe 接口文档 | 业务 iframe 外壳 | 宿主页待实施；内部独立文档不声称可控 |
| `/project/project` | `project/index.vue`；项目 UI 列表/编辑 | 业务 + ZXUI/EP | 项目包模型导出；待实施 |
| `/project/operlog`、`/log/operlog`、`/log/logininfor`、`/log/audit` | 日志 UI 列表 | 业务 + ZXUI/EP | 常规 API/Excel；待实施 |
| `/login`、`/register`、`/user/profile` | 静态路由；登录、注册、个人资料 | 业务 + ZXUI/EP | 无 UI 渲染导出；待实施 |
| `/system/user-auth/role/:id`、`/system/role-auth/user/:id`、`/system/dict-data/index/:id` | 前端权限路由；授权和字典子页 | 业务 + ZXUI/EP | 无 UI 渲染导出；待实施 |
| `src/views/device/**`、`src/views/protocol/index.vue` | 设备与协议 UI；前端组件存在，未见于当前 platform manifest | 业务 + ZXUI/EP；协议表走 VXE | 路由/权限来源待部署复核，不能仅按文件判断可达；待实施 |
| `src/views/project/{detail,entry,topo}.vue` | 工程详情、入口和拓扑编辑；部分前端权限路由可达 | 业务 + ZXUI/EP + X6 2.18.1 | 项目包模型与拓扑 PNG/SVG 渲染导出分开；待实施 |
| `src/views/dashboard/index.vue` | 当前模板 ThemeDemo | 业务 + ZXUI | 不算真实监控展示验收；待实施 |
| `src/views/project/simulation/**` 及专用组件 | 仿真 UI / TableV2 / 图表 | 仿真所有者 | 本 spec 排除；共享改动影响不算其验收 |

## 共享消费与第三方边界

| 消费者 | 所有者、公开能力、状态 |
| --- | --- |
| `src/layout/**`、`src/assets/styles/theme.module.css` | 业务外壳；Header/Sidebar/Tags/内容区有 50/84/54/200px 等现行尺寸，任务 11 迁移到业务显示角色。 |
| `src/components/ui/FormDialog/**` | 业务 FormGrid 的列数/标签/横向 gap/minWidth 与 ZXUI 控件 density 分工已存在；显示大小横向角色待接入。 |
| `ZxGridList`、`ZxListToolbar`、ElTable、Pagination | 公开 ZXUI 控件及 EP 适配；已有 density 不等于显示比例；任务 6、8、12。 |
| `src/plugins/vxe-table.ts`、`src/plugins/vxe-layout.ts`、`VxeSchemaTable` | 业务 VXE 4.17.15 集成；已接 ZXUI 布局事务和逐行阅读锚点，5000 行浏览器样例通过 100%↔125% 与手动行高检查。未重新渲染的可变高度虚拟行仍可能持有 VXE 旧高度；编辑/选择、失败可见重试及真实业务路由未验收。 |
| Quill `src/components/ui/Editor` | 业务适配第三方公开 UI；正文 HTML/用户颜色属领域内容，工具栏待迁移。 |
| wangEditor `src/components/ui/RichEditor` | 用户本次明确暂不处理；登记为**延后消费者**，不参与本批实现/完成声明，文档正文仍需保持。 |
| `echarts` 5.5.1、`@antv/g2plot` 2.4.31、X6 2.18.1 | 使用入口须逐项核对是否非仿真可达；显示标签/工具栏与领域图数据、渲染导出分离。 |
| `vue-virtual-scroller` 2.0.0-beta.8 | 已安装；当前尚未证明非仿真路由可达，不把包导入当消费者通过。 |
| `src/components/ui/iFrame`、`layout/components/InnerLink` | 外层业务 UI 可控；独立文档内部需显式协议或列为外部边界。`iFrame` 当前用视口减 94.5px 计算高度。 |

证据来源：菜单 manifest、前端静态/权限路由、对应 SFC、`package.json` 与安装包版本；当前列表截图见 [task1-user-office-baseline.png](evidence/task1-user-office-baseline.png)。新增用户表单运行时请求因既有 token 失效未打开；只用源码记录其布局基准，待首条链验收时重新操作。
