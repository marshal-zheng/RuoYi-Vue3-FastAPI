# 部门资源真实浏览器验收

本入口使用生产 `DeptList.vue` 和两个 `DeptDlg.vue`，通过同一个应用 `DataClient` 读取真实 FastAPI。两个树订阅使用生产 `departmentResource.userTree`。不替换 HTTP，不安装 MSW，不访问用户已有浏览器会话。

先按根 AGENTS.md 启动本地后端，再在前端目录启动源码直连：

```sh
BROWSER=none VITE_ZXUI_LOCAL=true \
  VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus/worktrees/ruoyi-department-source \
  yarn dev --host 127.0.0.1 --port 3100 --strictPort
```

本次 clean worktree 位于 ZXUI 项目内，固定交付提交 `1b7c3236666f862afc44c23b1c72f49c7dffdb55`，复用已安装依赖和独立包。原因是主工作区未提交的主题契约 hash 与业务安装的 dashboard 扩展不一致。一般情况下可直接指定主源码目录；这里保留用户主题改动，未修改主题校验或禁用 dashboard 扩展。

Vite 配置忽略 `tests/**` 的监听；修改本验收入口后须重启服务。验收时不要同时执行会生成 Vite 配置时间戳文件的 Vitest 或编辑生产源码，以免热更新中断浏览器。

另一个终端运行（密码只进入进程环境）：

```sh
read -s CODEX_DEPT_PASSWORD
export CODEX_DEPT_PASSWORD
CODEX_DEPT_QUERY_WRITE=1 node tests/manual/department-resources/browser.mjs
unset CODEX_DEPT_PASSWORD
```

默认地址为 `http://127.0.0.1:3100`，可通过 `CODEX_DEPT_UI_BASE` 覆盖，只允许 loopback。账号默认 admin，可通过 `CODEX_DEPT_USERNAME` 覆盖；需本地关闭验证码的开发环境。

脚本先用真实 API 创建唯一前缀的临时部门，在生产 `/system/dept` 页面通过表单保存并检查列表刷新；随后进入同一应用的双编辑器入口，检查两个树订阅只发送一个读取、同时打开两个编辑器只发送一个详情读取、两份表单可独立输入、保存左侧只写一次并自动刷新列表和两棵树、右侧草稿保持不变、重开右侧读到已保存值。创建和清理是 API 测试数据准备，断言中的两次编辑保存均由生产 UI 触发。

finally 重新进入真实路由，只删除本次唯一前缀记录并确认不存在，再注销本次登录。失败证据会记录清理结果，若清理失败须按该次 marker 精确恢复，不可批量删除其他测试数据。新运行结果和截图按模式保存在 `docs/reports/evidence/2026-11-02-department-resources/source-browser/` 或 `installed/`，初次源码验收证据保留在上一级目录，只保存方法、路径计数和临时记录证据，不保存令牌、请求头或既有用户数据。

这是同一应用内的缓存共享验收，不声称跨浏览器或跨标签页共享内存缓存。刷新失败、结果未知和权限切换通过组件/资源回归覆盖，真实 HTTP 探针见相邻 `department-query/README.md`。


## 安装模式验收

当前 3100 服务使用安装模式。复跑时应停掉自己启动的源码服务，再显式启动以下服务，不要同时运行两个占用 3100 的实例：

```sh
BROWSER=none VITE_ZXUI_LOCAL=false VITE_APP_RUNTIME_MODE=real VITE_ENABLE_MOCK=off \
  yarn dev --host 127.0.0.1 --port 3100 --strictPort
```

另一个终端按前述方式安全设置 `CODEX_DEPT_PASSWORD`，执行：

```sh
CODEX_DEPT_QUERY_WRITE=1 CODEX_DEPT_MODE=installed \
  node tests/manual/department-resources/browser.mjs
CODEX_DEPT_QUERY_WRITE=1 VITE_ZXUI_LOCAL=false \
  CODEX_DEPT_EVIDENCE=../docs/reports/evidence/2026-11-02-department-resources/installed/http.json \
  yarn vitest run --config tests/manual/department-query/vitest.config.ts
unset CODEX_DEPT_PASSWORD
```

浏览器脚本现在创建唯一前缀的父子部门，额外断言生产树表折叠/展开不触发读取；finally 按后代优先清理。安装模式同时断言没有加载本工作区的 ZXUI 源码，不仅依赖命令行标签。`CODEX_DEPT_EVIDENCE_DIR` 可覆盖浏览器结果目录。

原安装版树表接口本已存在，先前失败来自测试读取子组件内部代理。树表集成测试现通过父组件的真实模板 ref 检查公开 API，未替换组件或放宽断言。

完整相关回归：

```sh
VITE_ZXUI_LOCAL=false yarn vitest run \
  src/queries/context.test.ts src/queries/system/dept.test.ts src/queries/system/user.test.ts \
  src/queries/system/dict.test.ts src/queries/system/dict-management.test.ts src/utils/http.test.ts \
  tests/unit/components/DeptList.test.ts tests/unit/components/DeptDlg.test.ts \
  tests/unit/components/UserFormDialog.test.ts tests/unit/components/DictSelectQuery.test.ts \
  tests/table-render-tree-integration.test.ts --reporter=dot
yarn type-check
```
