# Demo Offline Runtime Package v2 Runbook

## 交付结构

技术人员执行：

```bash
cd ruoyi-fastapi-frontend
yarn build:demo-offline
```

产物根目录为 `ruoyi-fastapi-frontend/dist-demo-offline/`。当前交付格式已硬切到 v2 Release Store，必须包含：

- `index.html` 与 `assets/**`：通用 demo-offline 程序壳，不由 MCP 修改。
- `demo-contract/contract.json`：当前离线壳 module contract、IndexedDB mapping、handler coverage 和 invariants 摘要。
- `demo-contract/scenario.schema.json`：`DemoScenarioPackage` JSON Schema。
- `demo-contract/default-scenario.json`：离线壳默认场景来源。
- `demo-scenarios/active.pointer.json`：当前 active release 指针。
- `demo-scenarios/releases/bundle-default/manifest.json`：随壳输出的固定 bundle default v2 release。
- `demo-scenarios/releases/<release-id>/manifest.json`、`provenance.json`、`slices/*.json`：MCP 生成并激活的不可变 v2 release。
- `demo-scenarios/timeline.json`：审计日志，缺失或损坏不影响浏览器启动。

新 runtime package 不再生成、读取或迁移 `demo-scenarios/active.json`、`previous.json`、`active.meta.json`。这些文件如果残留，只能视为 legacy residue，不能作为 fallback 输入。

## 非技术人员入口

非技术人员不需要 clone 源码、理解 Git、手写 `scenarioId` 或重新 build。把本地 MCP 指向离线包根目录，然后让 AI Agent 调用：

```json
{
  "topic": "二手电脑回收项目演示",
  "businessDescription": "突出回收评估、检测、报价、入库和环保流转。",
  "target": {
    "kind": "offline-static",
    "root": "/path/to/dist-demo-offline",
    "packageFormat": "v2"
  },
  "activate": true
}
```

MCP 会生成 `.staging/<release-id>`，校验 manifest/hash/provenance/invariants/import dry-run，通过后发布到 `releases/<release-id>` 并切换 pointer。

## 启动方式

现场必须通过 HTTP 静态服务访问，不支持 `file://` 直开：

```bash
cd /path/to/dist-demo-offline
python3 -m http.server 4173 --bind 127.0.0.1
```

然后浏览器访问 `http://127.0.0.1:4173/`。

## Fallback 与恢复

浏览器 demo-offline runtime 启动顺序：

1. 读取 `demo-scenarios/active.pointer.json` 指向的 v2 manifest/slices。
2. active pointer、manifest、descriptor hash、schema/contract 或 IndexedDB import 失败时，回退 `previous.pointer.json`。
3. previous 也不可用时，读取固定 `demo-scenarios/releases/bundle-default/manifest.json`。

手动恢复边界：

- 不要手改 `assets/**`、`index.html`、已发布 `releases/<release-id>/**`。
- 需要恢复时让 MCP 重新激活一个已校验的 release，或重新生成新的 v2 release。
- 不要复制 legacy v1 JSON 文件来恢复现场；v2 激活只切 `active.pointer.json`。

## MCP 写入边界与审计

offline-static target 只允许：

- 读取 `demo-contract/**` 和必要的 `demo-scenarios/**`。
- 写入 `demo-scenarios/**`。
- 发布前写入 `demo-scenarios/releases/.staging/<release-id>/**`。
- 通过校验后 rename 到 `demo-scenarios/releases/<release-id>/**`。
- 激活时把当前 active pointer 保存为 `previous.pointer.json`，再替换 `active.pointer.json`。

MCP 会拒绝写入：

- `assets/**`
- `index.html`
- 任意系统路径
- `..` 路径穿越
- symlink escape
- 已发布且同名的 `releases/<release-id>/**`

审计日志写在：

```text
dist-demo-offline/.audit/demo-offline-mcp.jsonl
dist-demo-offline/demo-scenarios/timeline.json
```

P0 v1 `active.json` 只保留为历史说明；当前 v2 Release Store 不提供 v1 fallback 或 v1 -> v2 migration。

## 未来业务模块 Definition of Done

新增业务模块要进入 demo-offline 生成链路，至少交付：

- module contract：实体、主键、required fields、最小记录量、跨实体引用。
- scenario slice：`DemoScenarioPackage` 中稳定的数据切片。
- IndexedDB mapping：table、sourcePath、primaryKey、indexes。
- repository/service：页面只从 IndexedDB 读取当前 active scenario。
- MSW handler：只做薄适配，不解析外部 release store 文件。
- generator adapter：从受控 draft 生成确定性记录。
- invariants：页面业务流转依赖的最小可运行链路。

缺少以上任一环节时，MCP 必须返回 blocker，不能临时伪造 handler 或让 AI 直接写最终 release 文件。
