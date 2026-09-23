# ZXUI 表单、输入与主题接入交付说明

日期：2026-09-23。业务仓：`/Users/hqz/dev/RuoYi-Vue3-FastAPI`；ZXUI：`/Users/hqz/Downloads/element-plus`。

## 最终范围和结论

用户收尾指令依次为“设备、仿真、工程不用管”和“监控、生成器也不用管”。本次后续任务已收束到 **系统管理、登录/资料页，以及 ZXUI 通用输入、弹框、主题与本地候选包**。这个范围的实现、当前页面验证和最终检查已结束。移出范围的既有改动保留，剩余分支不再推进，也未标成验收通过。

原始16项任务没有机械全勾：14项按当前适用范围完成；任务5剩余业务验证由用户取消；任务1实现完成但保留R9.AC3的历史证据缺口。完整逐条状态见 [tasks.md](../../specs/zxui-form-dialog-convergence/tasks.md) 和 [peer审阅](peer-review-final.md)。原始需求ID仍可追溯，不能把当前收尾结论解释为原始所有模块均验收通过。

## 已交付内容

- 修复状态字典集合、异步选项ref和并发请求，以及部门树、菜单树、用户详情/个人资料、角色已分配/待分配用户的响应消费。添加用户从0个radio恢复为0/1两个真实选项，没有业务硬编码兜底。
- 业务使用 `useFormDialog`、原生 `ElForm` 和纯布局 `FormGrid`。列数单一声明，尺寸640/880/1120，标签/横向间距集中维护；控件高度与纵向间距消费库density，保留原生FormInstance校验与重置。
- ZXUI `ZxInput`统一原生输入语义，数值步进独立为`ZxInputNumber`；四插槽、tooltip两分支、公开实例能力、输入事件与外部Popover锚点已修复。业务`ElInputNumber`和`ElSelect`未机械替换。
- 九主题由单一登记源驱动，使用公开Host/Provider及主题资产部署API；清除业务反向alias、主色竞争写入和重复autofill处理。通用density、局部scope、嵌套浮层和真实autofill由库提供。
- 严格AST门禁已接入业务命令和GitHub/GitLab CI，无baseline/allowlist。原始迁移库存184个input/68文件、18个原生dialog/16文件为历史代码覆盖口径；用户缩减范围后不将这些数字等价为全部页面验收。

## 三类证据

| 类别 | 结果与边界 | 证据 |
| --- | --- | --- |
| 当前真实业务 | B01–B13系统管理/登录资料页已按记录操作；用户表单九主题×明暗18组，新增/编辑/导入、必填和焦点，菜单条件字段及图标浮层、角色用户列表等 | [路线清单](browser-route-coverage.md)、[九主题矩阵](browser/business-nine-theme-matrix.json) |
| 响应式补充 | 真实UserFormDialog在独立fixture的640×700与390×630实际视口中单列、可滚动、页脚可见，关闭恢复焦点；纯FormGrid容器3/2/1列。不是整个业务shell的移动端全覆盖 | [fixture证据](browser-fixture-coverage.md) |
| 库公开能力 | 相同公开表单SFC分别源码/安装包运行；24组主题/明暗/density度量、slots/expose、原生number/search、嵌套scope及4个外部Popover场景。真实ElInput与ZxInput autofill明暗通过；公开CSS入口修正后复验 | [库验收](library/browser/README.md)、[静态与浏览器汇总](library/static-verification.json) |
| 本地安装产物 | 真正隔离目录安装tarball，公开imports/类型/样式/构建/主题资产通过，Vue/EP单实例，无source alias/workspace fallback；业务安装文件逐字节核对一致 | [安装收据](library/packed-receipt.json)、[业务部署](business-theme-deployment.json) |

ZXUI版本为 **3.0.0-next.0**。候选SHA-256：`085dfd40069635098fa97a8e29dd5764a9d5d4bd558492b5caf1df3e5453317a`。业务Vue3.5.43、Element Plus2.13.0；隔离消费者Vue3.5.40、Element Plus2.13.0。业务vendor中的同名tarball是本地可安装产物，下一主版本输入语义迁移见ZXUI中英文input/input-number文档及公开表单示例。

## 最后一次检查

[机器可读结果与完整命令](verification/closeout-results.json)：

| 检查 | 结果 |
| --- | --- |
| 完整业务vue-tsc | exit 0 |
| UI严格门禁 | 496文件、0违规；门禁/输出契约14测试通过 |
| 本轮系统数据/表单/主题偏好聚焦回归 | 5文件、42测试通过 |
| 最后一批9个源文件/fixture ESLint | 0 errors、4 warnings |
| 最终业务生产构建 | exit 0，26.78秒 |

ZXUI聚焦输入22项、主题/对话框/Host/结构回归、1458个主题变体生成漂移检查、本地真实打包安装均有独立记录，最终库源码及tarball未在这些检查后再变更。角色后端和后续生成器缓存最小回归已有历史结果，用户缩减范围后未继续展开。

全量业务历史日志仍有未通过项：Vitest为73文件通过/1文件失败、694测试通过/1失败，未改动的`mocks/store/datasource.test.ts`预期菜单4项、seed实际6项；全仓lint历史结果860 errors/1232 warnings。没有批量格式化无关代码，也没有把局部检查通过描述为全仓全绿。生产构建保留既有大chunk警告。

## 证据限制与已停止范围

严格R9.AC3同视口改前/改后截图仍缺证：旧图1124×1000、新图1280×720，旧DOM未保存可核对的viewport。已有同页面同主题DOM/颜色对照：工厂蓝深色背景与label计算色保持一致，表单从440×600、0个radio变为880px宽、2个radio。这个结果支持布局/数据修复和颜色来源清理，但不冒称已补齐严格同视口历史截图。

设备、工程、监控、生成器中的已执行交互仍保留在`browser/resumed`和fixture报告。未完成的完整协议模板、版本表单、日志详情、生成器编辑页等随用户要求停止。N02–N06只保留测试入口，未验收，不计通过。仿真始终不属于本轮实施和验证范围。

## 本地环境与数据

为此前原范围验收启动的本地前后端仍可使用。临时浏览器标签已关闭、临时视口覆盖已恢复。公开同源autofill临时目录已经移出业务public，fixture没有加入产品路由。

本地测试过程保留了测试工程“ZXUI 本地布局验收”、默认新设备及`sys_post`生成器元数据；仅补建原来缺失的`gen_table`、`gen_table_column`两张本地元数据表，旧35表保留，详见[初始化收据](verification/generator-schema-init.json)。用户停止相关范围后没有继续改动或删除这些数据。

本地候选没有发布npm或部署生产；Git提交以仓库历史为准。工作区原有修改按baseline快照保留，验收报告区分本轮变更、历史失败、取消范围和当前通过证据。
