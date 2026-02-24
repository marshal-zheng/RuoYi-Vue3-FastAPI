# Shared Kernel 变更影响测试清单

## 适用范围

当以下路径发生变更时，必须执行本清单：

- `ruoyi-fastapi-backend/shared/kernel/**`
- `ruoyi-fastapi-backend/shared/__init__.py`

## 治理规则

1. `shared/kernel` 只允许无业务语义能力（响应模型、通用错误封装、通用类型）。
2. 禁止在 `shared/kernel` 引入上下文字段或术语（如 `user/role/dept/project/device/protocol/simulation`）。
3. 禁止 `shared/kernel` 依赖 `module_admin`、`module_generator`、`module_task` 的业务实现目录。
4. 上下文可依赖 `shared/kernel`，但 `shared/kernel` 不可反向依赖上下文。

## 最小回归命令

```bash
cd ruoyi-fastapi-backend
venv/bin/python -m ruff check shared/kernel
venv/bin/python -m pytest -q -n 0 --no-cov tests/unit/modules/test_shared_kernel_models.py
venv/bin/python -m pytest -q -n 0 --no-cov tests/integration/test_core_modules.py
```

## 审核项

- API 响应序列化（camelCase）是否保持兼容。
- `shared/kernel` 是否新增业务语义枚举/异常。
- 关键集成链路（`core_modules`）是否受影响。
