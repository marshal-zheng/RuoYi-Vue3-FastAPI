# JWT 直调与 iframe 嵌入零信任安全改造 实现任务

- [x] 1. 建立安全改造基线与配置开关
  - 在后端配置层新增安全改造所需配置项（JWT 算法、JWKS、embed grant、ws ticket、CSRF、CSP）。
  - 定义并落地标准映射清单结构（ASVS/RFC/NIST），用于发布证据自动汇总。
  - 在文档中固定“硬切上线”约束，禁止兼容路径回退逻辑进入实现清单。
  _需求追溯: R1.AC1, R1.AC2, R1.AC3_

- [x] 2. 实现密钥管理与 JWKS 发布能力
  - 新增签名密钥注册、激活、轮换、吊销的服务与存储结构。
  - 提供 `/.well-known/jwks.json` 只读公钥端点，支持多 `kid` 共存窗口。
  - 为密钥生命周期操作补充审计日志记录。
  _需求追溯: R8.AC1, R8.AC2, R8.AC3, R8.AC4_

- [x] 3. 重构 JWT 签发与验证剖面
  - 将 token 签发统一收敛到新 Token 服务，强制 claim 完整性与最长期限。
  - 在验证链路上启用算法白名单、`aud` 校验、时钟偏移控制。
  - 引入 `jti` 防重放存储并在鉴权阶段执行判重拒绝。
  _需求追溯: R2.AC1, R2.AC2, R2.AC3, R2.AC4_

- [x] 4. 落地 m2m `private_key_jwt` 令牌签发
  - 新增 `/auth/m2m/token` 并仅接受 RFC 7523 形式客户端断言。
  - 拒绝 `client_secret`、Basic、API Key 作为 token 签发凭据。
  - 补齐 m2m 客户端公钥注册与轮换管理接口（或后台管理能力）。
  _需求追溯: R3.AC1, R3.AC4, R8.AC4_

- [x] 5. 收敛 API 鉴权来源并移除高风险入口
  - 将后端受保护接口鉴权入口统一为 `Authorization: Bearer`。
  - 移除/禁止 query、cookie、form token 来源解析逻辑。
  - 调整 CORS 策略为显式白名单与最小权限配置。
  _需求追溯: R3.AC1, R3.AC2, R3.AC3_

- [x] 6. 实现 iframe 白名单策略与 grant 签发
  - 新增“租户+集成应用”粒度的 origin/path 白名单模型与管理能力。
  - 实现 `/auth/embed/grants`，签发一次性、短时、绑定上下文的 `embed_grant`。
  - 对来源不匹配、策略禁用、重复请求场景补全拒绝与审计逻辑。
  _需求追溯: R4.AC1, R4.AC5, R9.AC1_

- [x] 7. 实现 iframe grant 交换链路
  - 新增 `/auth/embed/exchange`，仅允许一次性 grant 兑换短时 access token。
  - 明确禁止给 iframe 下发 refresh token。
  - 对过期、复用、来源不匹配等失败场景返回标准错误并记录事件。
  _需求追溯: R4.AC2, R4.AC3, R4.AC4_

- [x] 8. 改造 WebSocket 为 ws-ticket 鉴权
  - 新增 `/auth/ws-ticket` 签发一次性 ticket（短 TTL，单次消费）。
  - 改造 `/simulation/.../ws` 握手逻辑，仅接受 ticket 并校验 Origin。
  - 删除现有 query token / cookie token 回退行为，违规返回 1008。
  _需求追溯: R5.AC1, R5.AC2, R5.AC3, R9.AC1_

- [x] 9. 实现 CSRF 防护中间件与端点接入
  - 新增 Cookie 身份端点统一 CSRF 守卫（Origin/Referer + X-CSRF-Token）。
  - 将 `/auth/refresh`、`/auth/logout`、`/auth/embed/*`、`/auth/ws-ticket` 接入守卫。
  - 对 GET/HEAD/OPTIONS 保持可配置豁免并记录策略命中日志。
  _需求追溯: R6.AC1, R6.AC2, R6.AC3_

- [x] 10. 实施安全响应头与前端 XSS 基线
  - 新增安全响应头中间件（CSP nonce、frame-ancestors、HSTS、nosniff 等）。
  - 在前端构建规则中禁止危险渲染模式并引入净化器封装。
  - 将违规规则纳入 CI 失败条件。
  _需求追溯: R7.AC1, R7.AC2, R7.AC4_

- [x] 11. 前端鉴权链路硬切（内存 token）
  - 替换 `Admin-Token` Cookie 存储为内存态 Token Store。
  - 改造 HTTP 拦截器注入逻辑，统一从内存读取 access token。
  - 移除“记住密码”持久化逻辑，仅保留合规的最小化记忆信息。
  _需求追溯: R7.AC3, R7.AC5, R3.AC1_

- [x] 12. 实现 iframe 前端桥接机制
  - 新增 parent/iframe `postMessage` 双向 origin 校验桥接模块。
  - 实现 grant 交换、短 token 生命周期管理与过期重取流程。
  - 校验 URL 中无 token 传递路径并建立自动化断言。
  _需求追溯: R4.AC2, R4.AC4, R4.AC5_

- [x] 13. 建立安全可观测与告警闭环
  - 统一安全事件模型（认证失败、重放、origin 拒绝、ws 1008）。
  - 对接现有日志与指标体系，输出结构化审计日志与阈值告警。
  - 生成可用于发布审查的安全事件与合规汇总报表。
  _需求追溯: R9.AC1, R9.AC2, R9.AC3_

- [x] 14. 构建测试矩阵与发布门禁
  - 新增后端安全单测/集测：JWT profile、CSRF、iframe grant、ws-ticket。
  - 新增前端安全测试：token 存储约束、iframe bridge、XSS 规则阻断。
  - CI 集成 SAST、依赖漏洞扫描与安全回归，失败即阻断发布。
  _需求追溯: R10.AC1, R10.AC2, R10.AC3, R1.AC1_
