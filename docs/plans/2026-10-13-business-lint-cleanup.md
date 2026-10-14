# 业务 lint 警告清零

目标：按实际公开 API 和数据模型修复全部 1230 条源码 lint 警告，规则、解析范围与 TypeScript 严格选项保持原有强度，完成后重跑组件库和业务的标准全量验证。

范围：业务 frontend 200 个告警文件及因类型收紧揭露的调用/测试边界；仿真仅做 lint、类型和必要行为回归，不迁移 UI。保留已有未提交工作，不提交或发布。

- [x] 保存完整 src/tests 起始快照、规则计数、逐文件分组和 SHA256。
- [x] 分组修正 API/列表/公共表格、协议/图编辑器、项目/仿真、基础工具与全局声明。
- [x] 审查增量，确认无新增关闭规则、any 同义替代或无依据类型断言；对实际行为问题跑 RED/GREEN 回归。
- [x] 业务 ESLint --max-warnings 0、type-check、完整 Vitest、UI standards、mock contracts/overlays、生产构建、官方离线 E2E及当前 Drawer/Dialog 浏览器验证。
- [x] 组件库 lint、typecheck、UI contracts、完整 test:run 与 build:theme/build；本轮仅库测试夹具变化，不重打安装包。
- [x] 更新验收报告与完整退出码/数量证据。

证据：`docs/reports/evidence/2026-10-13-business-lint-cleanup/`；起始快照 `/tmp/ruoyi-lint-cleanup-baseline-20261013`。
