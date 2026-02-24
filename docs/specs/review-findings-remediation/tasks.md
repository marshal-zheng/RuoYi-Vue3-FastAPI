# 中间件安全加固与分类删除校验 实现任务

- [x] 1. 扩展配置模型并统一中间件安全参数
  - 在 `config/env.py` 中新增 `idempotency_max_request_body_bytes` 与 `rate_limit_trusted_proxies` 配置项，并提供默认值。
  - 在 `.env.example` 中补充同名环境变量说明，保持现有开关语义不变。
  - 校验配置读取路径与 `middlewares/handle.py` 装配逻辑不冲突。
  _需求追溯: R2.AC1, R2.AC2, R3.AC1_

- [x] 2. 重构客户端地址解析逻辑并限定可信代理
  - 在 `middlewares/rate_limit_middleware.py` 中实现“可信代理判断 + 条件读取 X-Forwarded-For”。
  - 保留 `scope.client` 回退路径，确保无代理或不可信代理下行为稳定。
  - 补充必要日志字段，便于定位来源判定分支。
  _需求追溯: R2.AC1, R2.AC2_

- [x] 3. 为幂等缓存键引入身份作用域隔离
  - 在 `middlewares/idempotency_middleware.py` 中解析用户身份（`Authorization` token 中 `user_id/userId`）并构造 `scope_key`。
  - 将 `scope_key` 纳入 `cache_key` 与 `lock_key` 的计算，避免跨用户缓存复用。
  - 处理匿名请求作用域，保证匿名与已认证作用域不共享缓存。
  _需求追溯: R1.AC1, R1.AC2_

- [x] 4. 增加幂等请求体上限保护
  - 为幂等中间件请求体读取增加上限控制，超限时跳过缓存流程但继续请求处理。
  - 记录结构化告警日志（包含路径、大小、阈值），满足审计可观测性。
  - 确保与现有响应体上限 `idempotency_max_response_body_bytes` 配置协同工作。
  _需求追溯: R3.AC1, R3.AC2_

- [x] 5. 增加设备分类删除前引用校验
  - 在 `DeviceRepository` 增加按分类 ID 统计/存在性查询接口。
  - 在 `DeviceCategoryService.delete_device_category_services` 调用该接口，发现引用时抛出明确业务异常。
  - 保持无引用路径的删除行为与返回结构不变。
  _需求追溯: R4.AC1, R4.AC2_

- [x] 6. 补齐并更新单元测试
  - 在 `tests/unit/middlewares/test_idempotency_middleware.py` 增加跨用户同 key 不应重放用例。
  - 在 `tests/unit/middlewares/test_idempotency_middleware.py` 增加请求体超限跳过缓存用例。
  - 在 `tests/unit/middlewares/test_rate_limit_middleware.py` 增加伪造 `X-Forwarded-For` 绕过失败用例。
  - 在 `tests/unit/services/test_device_category_service.py` 增加“被引用删除失败/无引用删除成功”双路径用例。
  _需求追溯: R5.AC1, R5.AC2, R5.AC3, R1.AC1, R2.AC2, R3.AC1, R4.AC1_

- [x] 7. 执行回归验证并整理交付
  - 运行中间件与设备分类相关单元测试，确认新增安全行为无回归。
  - 复核需求追溯矩阵，确保所有任务映射到有效 AC ID。
  - 更新变更说明，明确风险收敛点与配置变更项。
  _需求追溯: R1.AC1, R1.AC2, R2.AC1, R2.AC2, R3.AC1, R3.AC2, R4.AC1, R4.AC2, R5.AC1, R5.AC2, R5.AC3_
