# HTTP 源码联调与超时优先级验证

日期：2026-10-15。范围仅包括 HTTP 源码接入、超时优先级修复及真实业务导出验证。

## 改动与归属

- ZXUI `packages/http/package.json` 为本地工作区提供公开 `source` 条件。
- ZXUI 公共 `zxuiSourcePlugin` 支持显式启用 `@zxio/http`，负责源码解析、排除依赖预构建及 Axios 去重。
- 业务仅在既有 `VITE_ZXUI_LOCAL` 链路启用 HTTP。compiler 本地验证包同步交付新增公开配置的类型，未发布 npm。
- 超时修复位于 ZXUI `packages/http/src/client.ts`。业务现有导出函数中的 `timeout: 120000` 无需改写。
- 前一轮 Axios 1.20.0 升级保留；本轮未修改取消、重试、去重或响应插件管线。

## 超时契约

优先级由高到低：

1. 单次请求第二参数 `options.timeout`。
2. 单次配置 `requestOptions.timeout`。
3. 单次 Axios 配置 `timeout`。
4. 客户端默认 `requestOptions.timeout`。
5. 客户端分类型超时。

`0` 表示禁用超时。普通请求按 `timeout.default`、`axiosConfig.timeout`、内置 10000ms 回退；上传、下载仍保留独立的 60000ms 默认值，或使用各自显式配置。客户端数值形式 `timeout` 继续适用于所有类型。

## 源码解析证据

实际业务 Vite 配置与开发服务确认：

- `@zxio/http` → `/Users/hqz/Downloads/element-plus/packages/http/src/index.ts`。
- HTTP 源码导入的 Axios → 业务 `node_modules/axios/index.js`，版本 1.20.0。
- `@zxio/http` 已排除依赖预构建，Axios 去重已开启。
- 开发服务返回的业务 HTTP 模块直接导入上述源码路径。

结构化记录：[resolution.json](evidence/2026-10-15-http-source-timeout/resolution.json)。

## 真实业务导出

通过现有业务 `login()`、版本导出函数、ZXUI HTTP 源码、Axios 1.20.0 和 JSDOM XHR，连接本机 FastAPI。仅替换界面反馈及文件保存入口，实际请求、后端鉴权、导出生成与二进制传输均真实执行。未进行浏览器页面点击验收。

选用本地已有 `projectId=1`、`versionId=1`，未新增或修改业务记录。保存入口同时核对文件名及字节一致性。

| 验证 | 实际字节数 | XHR timeout | 结果 |
| --- | ---: | ---: | --- |
| Word 导出 | 5336 | 120000ms | 成功，内容为业务生成的 Word HTML |
| Excel ZIP 导出 | 165 | 120000ms | 成功，ZIP 完整性通过 |
| XML 导出 | 603 | 120000ms | 成功，可解析为 InterfaceControlDocument |
| XML 实际响应延迟 65 秒 | 603 | 120000ms | 65043ms 完成，跨过旧 60 秒限制 |

延迟验证使用本地代理转发真实 XML 导出，取得后端生成内容后延迟 65000ms 再交付；未替换导出响应数据。

当前版本没有协议数据，Excel ZIP 内为 `说明.txt`。本次覆盖 ZIP 生成、下载及超时配置，未覆盖含协议数据的工作表生成。

结构化记录：[exports.json](evidence/2026-10-15-http-source-timeout/exports.json)。

## 质量检查

- ZXUI：HTTP 全套现有测试及源码插件测试，9 个文件、53 项通过；新增覆盖集中在一组超时案例和一条源码解析案例。
- 业务：API、工具层及登录状态测试，17 个文件、72 项通过；默认安装包链路与临时 HTTP 源码别名链路分别执行通过。
- HTTP、compiler 类型检查与构建通过；构建后 HTTP manifest 已确认剥离工作区专用 `source` 条件。
- 业务 `yarn type-check`、`yarn lint:check`、前端约定检查通过。
- 业务显式启用 `VITE_ZXUI_LOCAL=true` 的 `yarn build:prod` 通过。
- 两边改动通过 ESLint／相关格式检查和 `git diff --check`；只读审查无阻断问题。

## 生效范围

超时修复当前通过本地源码模式生效。本轮未替换业务 `@zxio/http` vendor 包；关闭 `VITE_ZXUI_LOCAL` 后仍使用原安装包及其原有超时行为。正式分发修复需后续更新 HTTP 包。
