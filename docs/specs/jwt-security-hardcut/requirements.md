# JWT 直调与 iframe 嵌入零信任安全改造 需求规格

## 简介
本规格定义 RuoYi-Vue3-FastAPI 在“JWT 直调 API + iframe 嵌入页面”双场景下的统一安全要求，目标是在不引入兼容分支的前提下，以一次性硬切方式达到国际主流安全基线。规范对齐以下标准：
- OWASP ASVS 4.0.3（应用安全验证）
- OWASP API Security Top 10 (2023)
- RFC 7519（JWT）、RFC 8725（JWT BCP）、RFC 7517（JWK）、RFC 6455（WebSocket）
- NIST SP 800-63B（数字身份鉴别）
- W3C Content Security Policy Level 3

## 需求列表

### R1: 标准合规与安全基线落地
**用户故事:** 作为安全负责人，我希望系统的鉴权和前端防护明确映射到国际标准，以便审计、验收和长期演进都有客观依据。
**验收标准 (EARS):**
- R1.AC1: WHEN 安全方案发布 THEN 系统 SHALL 提供“需求-设计-任务-测试”全链路追溯，并对每项控制标注对应标准条款（如 ASVS、RFC、NIST）。
- R1.AC2: WHEN 任一安全控制无法映射到已声明标准 THEN 系统 SHALL 阻止进入发布阶段并输出差距清单。
- R1.AC3: IF 安全基线发生版本升级 THEN 系统 SHALL 在下一迭代更新映射矩阵并重新执行验收。

### R2: JWT 令牌剖面与签发约束
**用户故事:** 作为 API 调用方，我希望 JWT 的结构、签名和生命周期被严格约束，以便降低伪造、重放和误用风险。
**验收标准 (EARS):**
- R2.AC1: WHEN 系统签发 access token THEN token SHALL 使用非对称算法（EdDSA 或 RS256）并包含 `kid`。
- R2.AC2: WHEN 系统签发任意 JWT THEN token SHALL 包含 `iss/aud/sub/jti/iat/nbf/exp` 且 `exp` 不超过 10 分钟。
- R2.AC3: WHEN 系统校验 JWT THEN 系统 SHALL 按 RFC 8725 执行严格算法白名单、`aud` 校验与时钟偏移控制。
- R2.AC4: IF 同一 `jti` 在有效期内被重复使用 THEN 系统 SHALL 拒绝请求并记录安全事件。

### R3: JWT 直调 API 场景安全约束
**用户故事:** 作为外部系统集成方，我希望通过 Bearer JWT 直接调用接口，同时确保接口不会被浏览器自动凭证机制滥用。
**验收标准 (EARS):**
- R3.AC1: WHEN 客户端调用受保护 API THEN 系统 SHALL 仅接受 `Authorization: Bearer <token>` 作为身份凭证。
- R3.AC2: WHEN 请求在 URL、Cookie、表单中携带 token THEN 系统 SHALL 拒绝该身份来源并返回标准化错误。
- R3.AC3: WHEN CORS 规则生效 THEN 系统 SHALL 默认 `allow_credentials=false` 且仅允许显式白名单来源。
- R3.AC4: WHEN 机器客户端申请 m2m 令牌 THEN 系统 SHALL 使用 `private_key_jwt`（RFC 7523）完成客户端认证，并拒绝 `client_secret`、HTTP Basic 与 API Key 作为签发凭据。

### R4: iframe 嵌入授权与令牌交换
**用户故事:** 作为嵌入方平台管理员，我希望 iframe 能安全地完成单点嵌入访问，而不会泄露长期令牌。
**验收标准 (EARS):**
- R4.AC1: WHEN 父系统请求嵌入授权 THEN 系统 SHALL 签发一次性 `embed_grant`（有效期 <= 60 秒）并绑定 `origin/path/user/tenant`，且 `origin` 必须命中“按租户+集成应用”登记白名单。
- R4.AC2: WHEN iframe 完成令牌交换 THEN 系统 SHALL 返回短期 access token（有效期 <= 5 分钟）且不签发 refresh token。
- R4.AC3: IF `embed_grant` 过期、重复使用或来源 `origin` 不匹配 THEN 系统 SHALL 拒绝交换并审计。
- R4.AC4: WHEN 前端传递嵌入凭据 THEN 系统 SHALL 通过 `postMessage` 且强制双向 origin 校验，不得通过 URL query 传递 token。
- R4.AC5: WHEN 安全管理员维护 iframe 来源策略 THEN 系统 SHALL 支持以“租户+集成应用”为粒度配置、启停与审计 `origin` 白名单。

### R5: WebSocket 握手与会话安全
**用户故事:** 作为实时功能使用者，我希望 WebSocket 连接在跨站场景下不会被劫持。
**验收标准 (EARS):**
- R5.AC1: WHEN 客户端建立 WebSocket 连接 THEN 系统 SHALL 仅接受一次性 `ws_ticket` 进行握手认证。
- R5.AC2: WHEN 握手发生 THEN 系统 SHALL 校验 `Origin` 白名单并拒绝不匹配来源，白名单策略 SHALL 与“按租户+集成应用”来源策略一致。
- R5.AC3: IF 客户端使用 query token、Cookie token 或复用 `ws_ticket` THEN 系统 SHALL 关闭连接并返回 1008。

### R6: CSRF 防护体系
**用户故事:** 作为安全工程师，我希望所有依赖浏览器 Cookie 的敏感端点具备可审计的 CSRF 防护。
**验收标准 (EARS):**
- R6.AC1: WHEN 请求命中 Cookie 身份端点（如 `/auth/refresh`、`/auth/logout`、`/auth/embed/*`） THEN 系统 SHALL 同时校验 `Origin/Referer` 与 `X-CSRF-Token`。
- R6.AC2: IF 缺失或伪造 CSRF 相关校验项 THEN 系统 SHALL 返回 403 且不触发业务副作用。
- R6.AC3: WHEN 请求方法为 `GET/HEAD/OPTIONS` THEN 系统 MAY 免除 CSRF token 校验但仍执行来源策略。

### R7: XSS 防护与前端安全编码
**用户故事:** 作为平台用户，我希望页面不会因脚本注入导致账号和业务数据泄露。
**验收标准 (EARS):**
- R7.AC1: WHEN 服务端返回页面或静态资源响应头 THEN 系统 SHALL 下发 CSP Level 3（含 nonce）与 `frame-ancestors` 白名单策略。
- R7.AC2: WHEN 前端渲染用户可控内容 THEN 系统 SHALL 禁止直接使用 `v-html/innerHTML`，必要场景必须先做白名单净化。
- R7.AC3: WHEN 登录流程处理“记住我” THEN 系统 SHALL 禁止存储明文或可逆密码信息。
- R7.AC4: IF 检测到内联脚本或 DOM XSS 违规 THEN 构建与发布流程 SHALL 失败。
- R7.AC5: WHEN 浏览器端持有 `access_jwt` THEN 系统 SHALL 仅允许内存态保存，并禁止写入 `localStorage`、`sessionStorage` 与可读 Cookie。

### R8: 密钥管理与 JWKS 轮换
**用户故事:** 作为运维与安全管理员，我希望签名密钥可轮换、可吊销、可追溯。
**验收标准 (EARS):**
- R8.AC1: WHEN 服务发布 THEN 系统 SHALL 提供 JWKS 端点并仅暴露公钥。
- R8.AC2: WHEN 进行密钥轮换 THEN 系统 SHALL 支持多 `kid` 并保证轮换窗口内验签连续可用。
- R8.AC3: IF 密钥疑似泄露 THEN 系统 SHALL 支持紧急吊销并在 15 分钟内使相关 token 全部失效。
- R8.AC4: WHEN 注册或更新 m2m 客户端密钥 THEN 系统 SHALL 以“每客户端独立 JWKS”方式管理公钥，并记录密钥启用/停用/轮换审计轨迹。

### R9: 安全可观测与审计闭环
**用户故事:** 作为安全运营人员，我希望能实时发现并追踪认证滥用与攻击行为。
**验收标准 (EARS):**
- R9.AC1: WHEN 出现认证失败、token 重放、origin 拒绝、ws 1008 事件 THEN 系统 SHALL 记录结构化审计日志（含 request_id、subject、reason、source_ip）。
- R9.AC2: WHEN 安全事件触发阈值 THEN 系统 SHALL 发送告警并保留可追溯证据。
- R9.AC3: WHEN 安全审计执行 THEN 系统 SHALL 输出按标准分类的合规报表。

### R10: 发布门禁与安全验收
**用户故事:** 作为发布负责人，我希望发布前自动验证安全控制，避免将高危缺陷带入生产。
**验收标准 (EARS):**
- R10.AC1: WHEN 代码进入主干 THEN 系统 SHALL 在 CI 执行 SAST、依赖漏洞扫描、JWT/CSRF/WS/XSS 回归测试。
- R10.AC2: IF 任一高危或严重安全检查失败 THEN 系统 SHALL 阻断发布。
- R10.AC3: WHEN 发布完成 THEN 系统 SHALL 提供“标准映射+测试结果+风险豁免（如有）”的发布证据包。

## Clarifications

### Session 2026-03-03
- Q: iframe 可信来源白名单应采用哪种管理粒度（全局静态/按租户+集成应用/运行时动态）？ -> A: 按租户+集成应用登记白名单（Option B）
- Q: m2m 客户端认证采用何种机制（client_secret/private_key_jwt/API Key）？ -> A: 采用 private_key_jwt（Option B）
- Q: 浏览器端 `access_jwt` 存储位置采用何种策略（仅内存/localStorage 或 sessionStorage/HttpOnly Cookie）？ -> A: 仅内存（Option A）
