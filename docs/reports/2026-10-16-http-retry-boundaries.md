# HTTP 重试边界收敛

本轮已完成。通用修复落在 ZXUI `@zxio/http`；业务 HTTP 配置未改，自动重试继续关闭。没有提交、发布 npm 或混入其他优化。

## 选型与边界

定向核对 [axios-retry 官方文档](https://github.com/softonic/axios-retry)和[源码](https://raw.githubusercontent.com/softonic/axios-retry/master/src/index.ts)。直接采用可复用其拦截器和计时能力，但仍需改写默认方法策略、映射现有 HttpError、处理 Axios 转换阶段；其网络错误分支没有写请求方法门槛，默认还包含 PUT/DELETE 的幂等策略，不满足本项目保守写请求要求。

选择保留 RetryManager，局部借鉴方法约束、传输与语义分离、signal 终止退避的设计。不新增依赖或配置框架；代价是继续维护这段较小的重试逻辑。Axios adapter 的位置和取消检查由[官方 dispatchRequest 源码](https://raw.githubusercontent.com/axios/axios/v1.18.0/lib/core/dispatchRequest.js)核实；[getAdapter 源码](https://raw.githubusercontent.com/axios/axios/v1.18.0/lib/adapters/adapters.js)也确认了 peer 最低版本的 config-aware fetch 解析行为。本机真实链路使用 Axios 1.20.0。

| 职责 | 最终行为 |
| --- | --- |
| 默认策略 | 库默认关闭；显式开启后，仅 GET/HEAD/OPTIONS 的网络、超时、5xx 传输失败默认重试；缺少请求上下文不自动重放 |
| 写操作 | POST/PUT/PATCH/DELETE 不默认重放；业务确认安全后才能用现有 retryCondition 显式选择 |
| 真正重试边界 | 仅 Axios adapter；请求准备、Axios 请求转换、响应转换、拦截器和 ZXUI afterResponse/successResolver 不随重试重新执行 |
| 最终反馈 | 中间失败不执行 onError、错误通知或鉴权钩子；最终错误只进入一次管线 |
| 错误语义 | 保留业务 onError 增强再抛同一错误；响应转换、成功判定、鉴权和错误钩子异常不会重新发请求，语义异常保持原身份 |
| 取消 | 取消、准备失败、未知本地异常不由宽松条件放行；退避立即清理 timer/listener，保留 reason、最近 HttpError→原 Axios cause 链及请求 config |
| Axios 契约 | 保留 config.env.fetch/Request/Response；对外 config 恢复原 adapter，显式重发不会叠加旧重试闭包；每次传输的超时语义保持 |

任意普通响应钩子／解析异常按原对象抛出，不伪装成传输故障。明确的 ZXUI HttpError 业务拒绝仍进入一次错误管线。Axios 的最终失败响应只转换一次后再规范化；取消不被其二次 signal 检查覆盖。

## 验证与复核

| 验证 | 结果 |
| --- | --- |
| ZXUI HTTP | 9 文件、134 项通过；新增 32 项必要边界回归 |
| 库构建、受影响文件 lint/格式、HTTP 源码和测试类型检查 | 通过 |
| 业务 HTTP、反馈、下载、operation、上传与用户表单 | 7 文件、68 项通过；测试实际解析安装的本地 tgz |
| 业务 yarn lint:check / yarn type-check | 通过 |
| 生产构建：源码直连 / 安装包 | 分别通过，26.62s / 23.51s |
| 独立复核 | 发现 4 个 P2 均已复现、补回归并修复；最终 32 项边界测试独立通过，无直接相关遗留问题 |
| 仓库约定脚本 | 仍失败于 VersionList.vue 的既有 console；文件哈希与基线相同 |

回归先有失败证据：最初 25 项中 21 项失败；进一步发现 Axios transformResponse 和取消原因边界后，新增回归出现 3 项失败；fetch 环境与配置复用回归也先出现 3 项失败。详见[最初失败](evidence/2026-10-16-http-retry-boundaries/red.log)、[第一次复核失败](evidence/2026-10-16-http-retry-boundaries/review-red.log)、[adapter 复核失败](evidence/2026-10-16-http-retry-boundaries/adapter-red.log)及[最终库测试](evidence/2026-10-16-http-retry-boundaries/library-final-tests.log)。

构建保留 CSS 压缩语法、Browserslist 数据年龄、较大 chunk 和安装依赖 peer 提示，本轮未处理。HTTP 没有触及相关样式或依赖版本。测试类型检查使用隔离 tsconfig 并关闭 preserveSymlinks，以正确解析 pnpm 的测试依赖类型。

## 真实业务闭环

源码与安装包两种模式各 **14 项检查通过**，使用生产 TS HTTP/API/反馈/operation/下载模块、Axios XHR、本地 FastAPI 和 Docker MySQL。仅 UI 反馈投递用 stub；loopback HTTP 代理在读取前或真实写入成功后注入 503。没有用内存 adapter 结果替代真实业务证据，也没有使用 computer use。

- 真实登录与读取：业务 retry 未配置；默认读取 503 只发一次。单次显式开启读取重试后，503→真实列表成功共两次，错误反馈为零，分页解包保留。
- 最终失败：三次传输后只反馈一次，业务增强后的 Problem Details、最终 Axios cause、response/config 继续保留。
- 模拟“服务端已提交、客户端收到 503”：业务默认客户端和显式开启重试的库客户端均只发送一次 POST；均能回读到真实写入值。operation pending 释放，未出现第二次写入或冲突重放。
- 真实 409：原始 cause/context 和业务错误明细保留，已写入值不变。
- 退避取消：1000ms 等待在源码／安装包模式分别约 **0.34ms / 0.32ms** 结束，只有一次传输，pending 释放，通知为零，reason 和最近原始 Axios 错误链保留。
- 真实响应语义：afterResponse、successResolver、Axios transformResponse 各自抛出异常时均只有一次请求，原异常对象身份保留。
- 真实 401：显式条件允许的两次 GET 后，最终鉴权钩子只运行一次，其异常身份保留；业务重新登录提示也仅出现一次，有效会话恢复后仍可读取。
- 真实 Excel 下载及 404：成功文件有 XLSX ZIP 头，失败不保存文件，原错误和 loading 释放行为保留。
- 每轮创建的两条参数记录均已删除，原有 7 条完整明细和总数逐项比较一致，COUNT 缓存移除改动保持。

详见[源码证据](evidence/2026-10-16-http-retry-boundaries/actual-source.json)、[安装包证据](evidence/2026-10-16-http-retry-boundaries/actual-installed.json)及[可复现脚本](evidence/2026-10-16-http-retry-boundaries/actual-probe.cjs)。这些属于真实模块与真实 HTTP 验证；未做浏览器点击、视觉或原生表单交互验收。

## 本地交付与保护

业务现引用 `vendor/zxio-http-1.0.0-retry.20261016.tgz`，锁文件同步，Axios 保持 1.20.0。归档、打包暂存目录和安装目录的 53 个文件一致（manifest 按 JSON 语义比对）；LICENSE 随包保留。开发继续使用既有源码直连能力。详见[归档一致性](evidence/2026-10-16-http-retry-boundaries/package-integrity.json)。

README、中英文 HTTP 指南与组件文档已更新。通过当前生成器在隔离输出目录生成，仅回写 HTTP 类型元数据和 llms-full 的四段 HTTP 全文，非 HTTP 聚合条目保持不变，详见[生成记录](evidence/2026-10-16-http-retry-boundaries/metadata.json)。

基线哈希比较覆盖业务 3413 个、ZXUI 7934 个既有文件；只有本轮允许的 HTTP 源码、测试、文档和业务依赖文件发生变化，既有文件无丢失、暂存区未变。此前其他未提交／未跟踪工作全部保留。仅停止本轮启动的后端 PID 81071，未停止既有 MySQL、Redis 或其他项目进程。详见[工作区保护](evidence/2026-10-16-http-retry-boundaries/baseline-preservation.json)和[验证汇总](evidence/2026-10-16-http-retry-boundaries/verification.json)。
