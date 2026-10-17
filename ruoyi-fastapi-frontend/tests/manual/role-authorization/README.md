# 角色与双向授权真实业务探针

显式启用的本地 Vitest 探针，不加载项目 setup/MSW，不渲染浏览器。它使用真实业务 commands、query factories、原生 useQuery 订阅和 HTTP 适配，只访问 loopback FastAPI。

按根 AGENTS.md 启动标准后端后，配置 `CODEX_ROLE_QUERY_WRITE=1`、`CODEX_ROLE_PASSWORD`，运行：

```sh
VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus \
  corepack yarn vitest run --config tests/manual/role-authorization/vitest.config.ts
VITE_ZXUI_LOCAL=false \
  corepack yarn vitest run --config tests/manual/role-authorization/vitest.config.ts
```

默认账号为 admin，API 为 `http://127.0.0.1:8088`；可用 `CODEX_ROLE_USERNAME` / `CODEX_ROLE_API_BASE` 指定。验证码开启时探针退出，不改配置。不要与其他使用同一账号登录的探针并行，当前后端单会话策略可能替换先前会话。`CODEX_ROLE_EVIDENCE` 指定脱敏 JSON 输出；候选 overlay 验证必须设置 `CODEX_ROLE_RUNTIME=candidate-source-preserving-overlay`，默认值 `standard-no-overlay` 仅用于正常源后端。

探针创建独有 `codex_ra_*` 名称的 3 个角色和 3 个用户，验证同条件共享、pageSize=1 的第二页、增量添加、完整替换、显式清空、单条/批量撤销、目录改名与状态刷新、已关联停用角色保留、角色/数据范围编辑读取和真实 HTTP 422。只操作该次前缀匹配的记录；finally 重新查询该前缀以恢复可能丢失的 POST 响应，清除关联、删除用户和角色、核对列表为空，再注销自建会话。

失败与清理状态都会写入证据。若会话被替换导致清理失败，使用新的自建会话仅清理证据中的 marker，并另存恢复记录，不能把原失败改成通过。证据不包含令牌、密码、请求头或完整用户响应。该探针不证明浏览器视觉交互或所有权限账号组合；后端受控范围/缓存 A/B 的输入和证据另外记录。
