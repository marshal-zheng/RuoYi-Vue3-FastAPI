# 测试指南

## 常用命令

```bash
cd ruoyi-fastapi-backend

# 全量
./venv/bin/pytest tests/ -v

# 指定文件
./venv/bin/pytest tests/unit/scripts/test_db_workflow.py -q

# 关键集成测试
./venv/bin/pytest tests/integration/test_business_critical.py -v

# 覆盖率报告
./venv/bin/pytest tests/ --cov=module_admin --cov=utils --cov-report=html
```

## 目录结构

```
tests/
├── conftest.py
├── integration/
├── unit/
└── coverage/
```

## 说明

- 不再使用旧测试包装脚本。
- 优先直接调用 `pytest`，避免多套测试入口并存。
- 覆盖率报告输出到 `tests/coverage/html/index.html`。
