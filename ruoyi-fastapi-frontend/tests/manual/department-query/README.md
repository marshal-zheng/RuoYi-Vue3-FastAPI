# 部门业务 Query 真实本地验证

这是显式启用的 Vitest 手工探针，不进入日常测试匹配；不加载项目测试 setup、MSW 或 HTTP mocks。它调用真实业务 `deptCommands`、查询工厂、原生 `useQuery`（独立 effectScope、显式传入应用 QueryClient）与 HTTP 适配，连接本机后端。没有渲染组件或使用 computer use，不能证明浏览器 UI 交互。

后端按根 AGENTS.md 启动，需现有 Docker MySQL、现有 Redis 的宿主端口均可达。不要重置、seed 数据库或改权限。探针只创建 `codex_dept_query_<唯一后缀>` 父子部门，不创建/修改用户；在 finally 中只删除本次前缀对应的记录（先子后父），并检查列表中已不存在。失败证据也会写入，但不会包含凭据、请求头、完整响应或用户记录。

从 frontend 目录运行，密码通过环境传入，避免写入脚本或命令历史：

```sh
read -s CODEX_DEPT_PASSWORD
export CODEX_DEPT_PASSWORD
CODEX_DEPT_QUERY_WRITE=1 VITE_ZXUI_LOCAL=true \
  VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus \
  corepack yarn vitest run --config tests/manual/department-query/vitest.config.ts
CODEX_DEPT_QUERY_WRITE=1 VITE_ZXUI_LOCAL=false \
  corepack yarn vitest run --config tests/manual/department-query/vitest.config.ts
unset CODEX_DEPT_PASSWORD
```

验证码开启时，先通过真实 `/captchaImage` 取得并人工识别新验证码，将其 code/uuid 作为 `CODEX_DEPT_CAPTCHA_CODE` / `CODEX_DEPT_CAPTCHA_UUID` 传入。也可传入自己新建会话的 `CODEX_DEPT_TOKEN` / `CODEX_DEPT_CSRF`；探针不会注销外部传入的会话。不要将这些值写入证据。未设置 `CODEX_DEPT_QUERY_WRITE=1` 时只显示 skipped，绝不进行登录或写入。

默认 API 为 `http://127.0.0.1:8088`，只允许 loopback；`CODEX_DEPT_API_BASE` 可指定本机不同端口。`CODEX_DEPT_USERNAME` 默认 admin。证据默认写入仓库 `docs/reports/evidence/2026-10-17-department-query-convergence/{source,installed}-actual.json`；可用 `CODEX_DEPT_EVIDENCE` 更改路径。

验证内容：双 user-tree 订阅共享真实读取；父子创建后自动扇出；改名后管理列表与两份树订阅更新、用户列表真实重读；停用仍留在管理列表但退出正常部门树，启用重新出现；后端排除自身/后代；编辑快照；真实非法 status HTTP 422；finally 清理。用户列表以本次临时部门过滤，故只能证明刷新请求依赖，不声称既有用户行的部门名称视觉显示已验收。权限差异源于真实后端：管理列表/排除树为 `system:dept:list`，用户树为 `system:user:list`；探针使用实际当前权限，不制造受限账号或修改权限。

创建等待超时时，额外读取独立真实列表/树，并只保留本次 marker 对应的 ID、父 ID、status 和类型及订阅是否仍在读取；不保留已有部门/用户数据。连续创建本身不等待第一个写后的刷新，也不主动失效查询。
