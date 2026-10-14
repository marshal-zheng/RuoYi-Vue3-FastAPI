# Application 分组独立交叉 review

最终结论：**本次复核没有剩余 P0/P1/P2；发现的三项 P2 已关闭。**

范围：application-scope.json 所列相对 `/tmp/ruoyi-lint-cleanup-baseline-20261013` 的增量，公开 ZXUI GridList / HTTP SDK 接口与后端字段，下游回归测试，以及 `scripts/postprocess-openapi.mjs`、`scripts/openapi-client/` owner 与正式生成脚本。只读 application 源文件；生成复现实验仅写隔离 `/tmp` 目录。

## 已关闭发现

1. **P2 — 生成客户端丢失公开 RequestFn 实现检查。已关闭。** 最终 `request` 保留 `Client['request']` 约束和 TData/TError/ThrowOnError/TResponseStyle，method/SSE factory 均受公开泛型接口检查，整体结果使用 `satisfies Client`。没有 whole Client/handler casts。unknown 仅在真实响应解析及 TS 无法随运行时判别收窄的条件返回边界绑定 RequestResultValue。真实 Fetch 组合覆盖 data/fields、成功/204/错误/throwOnError、空 200、URL path/query/body 与 validator/transformer。

2. **P2 — SDK 输出修复没有进入确定性生成链路。已关闭。** 正式生成脚本在锁定 CLI 后调用 owner postprocess，再执行真实格式化。三份维护模板存于非 generated owner 目录；版本必须为 0.97.0，原 SDK helper 结构 hash 或已审模板 hash 必须匹配。独立重跑生成 → 两次 postprocess → 同一 formatter → strict TypeScript：所有阶段 exit 0；16 个新生成 SDK 文件 lint 0 错误/0 警告。三份新生输出、当前 source 与 owner 模板逐字节一致。独立注入未知上游结构后处理 exit 1，三目标均未发生部分改写。

3. **P2 — SSE unknown catch 被声称为任意 TError。已关闭。** 复核曾实际证明 native fetch TypeError 无 ApiError.code，因而禁止 `error as TError`。最终 error hook 保留 unknown transport 边界，删除不存在实际 typed error result 的 TError 泛型；正常 completion 为 void，不再向 TReturn 断言 undefined。新增 network TypeError、HTTP 503 Error 和 validator 对象异常回归，全部 14 个 SDK 运行时与调用类型测试通过。

## 独立证据

- `sdk-cross-review-final.log` 与 `sdk-cross-review-final-receipts.json`：独立执行最终生成、两次 postprocess、格式化、strict tsc、SDK 14/14 回归；所有命令 exit 0。
- `sdk-cross-review-final-lint.json`：真实再生成 16 文件，0 错误/0 警告。
- `sdk-cross-review-template-proof.json`：三份 regenerate/source/owner 字节一致。
- `sdk-cross-review-owner-negative.json`：未知结构拒绝，三目标均保持原值。

## 已核对其他边界

- 公开 `ZxGridListInstance` 的 `updateState(key, value)` 与 `getStateSnapshot()` 调用符合安装包 API。
- GridList loadData 收到 query/pager 状态；有限 TS 页面映射为真实 HTTP page/pageSize，JS 监控页面保留 HTTP normalize 的查询、分页与升降序转换。未发现新增筛选路径或排序回归。
- HTTP afterResponse 仍添加安装版 GridList 所需 pager；DTO 类型收紧没有移除实际运行时分页 metadata。
- 协议/设备/系统字段主要引用生成 Model；Notice bytes 的 JSON 字符串 wire 差异单独说明。没有业务 any 同义类型或无根据的局部双重断言。
- 权限路由转换不修改共享后端快照；错误记录保留；布局设置从 unknown storage 输入按允许的布尔键验证。数据源缓存与失败路径没有本轮运行时改变。
- VXE 错误类保留真实 ValidationResult；row/Context 泛型沿规则与全局校验器传播；依赖 row 的 message 在真实 row 上评估。

## 真实业务浏览器回归

独立执行既有授权 headless `node scripts/check-overlay-business.mjs`，没有 CUA/用户浏览器操作。首次在并行编辑期间被 Vite error overlay 阻挡，exit 1；随后新独立 context 未重现 overlay，同一脚本重跑 exit 0，**8/8 场景、pageErrors 0、角色/用户 writes 0**。首次失败保留，不隐藏历史。

证据目录：`business-browser/`；最终 `execution.json`/`execution.log`、`browser.json` 与 8 张桌面/移动截图。首次失败见 `attempt-1-execution.*`；失败后只读页面诊断见 `failure.json`/`fresh-page-after-first-failure.png`。

80/8088 原服务没有停止或重启；最终端口仍由前端 PID 63231 与后端 PID 63230/63602 监听，首页与 API docs 均 HTTP 200。验证只登录和切换主题/打开关闭 Drawer/Dialog，未提交角色或用户业务记录。
