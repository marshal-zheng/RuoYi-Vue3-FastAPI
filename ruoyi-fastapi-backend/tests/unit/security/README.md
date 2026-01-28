# 安全测试套件

## 概述

本目录包含所有安全相关的测试，确保系统能够抵御常见的安全攻击。

## 测试覆盖

### SQL 注入防护测试 (`test_sql_injection.py`)

测试所有数据库查询是否能够抵御 SQL 注入攻击。

**测试场景**:
- ✅ 用户名查询注入防护
- ✅ 数据权限查询注入防护（最关键）
- ✅ 部门查询注入防护
- ✅ 角色查询注入防护
- ✅ LIKE 查询注入防护
- ✅ ORDER BY 注入防护
- ✅ IN 子句注入防护
- ✅ 原始 SQL 使用限制
- ✅ 批量操作注入防护

**攻击向量测试**:
```python
# 经典 SQL 注入
"admin' OR '1'='1"

# 删除表
"admin'; DROP TABLE sys_user; --"

# UNION 注入
"admin' UNION SELECT * FROM sys_user WHERE '1'='1"

# 布尔盲注
"admin' AND 1=1 --"

# 时间盲注
"admin' AND SLEEP(5) --"

# 命令执行
"'; EXEC xp_cmdshell('dir'); --"

# 代码执行（eval 漏洞）
"__import__('os').system('rm -rf /')"
```

## 运行测试

### 运行所有安全测试
```bash
cd ruoyi-fastapi-backend
pytest tests/unit/security/ -v
```

### 运行 SQL 注入测试
```bash
pytest tests/unit/security/test_sql_injection.py -v
```

### 运行特定测试
```bash
pytest tests/unit/security/test_sql_injection.py::TestSQLInjectionProtection::test_user_query_sql_injection_username -v
```

### 生成覆盖率报告
```bash
pytest tests/unit/security/ --cov=module_admin --cov-report=html
```

## 安全最佳实践

### ✅ 推荐做法

1. **始终使用参数化查询**
```python
# 正确 ✅
query = select(SysUser).where(SysUser.user_name == username)
```

2. **使用 SQLAlchemy 表达式 API**
```python
# 正确 ✅
from sqlalchemy import and_, or_
conditions = [
    SysUser.user_name == username,
    SysUser.status == "0"
]
query = select(SysUser).where(and_(*conditions))
```

3. **使用数据权限构建器**
```python
# 正确 ✅
from module_admin.aspect.data_scope_builder import DataScopeContext

context = DataScopeContext(user_id=1, dept_id=100, role_scopes=[...])
condition = context.build_condition(SysUser)
query = select(SysUser).where(condition)
```

### ❌ 禁止做法

1. **禁止使用 eval()**
```python
# 错误 ❌ - 严重安全漏洞
eval(data_scope_sql)
```

2. **禁止字符串拼接构建 SQL**
```python
# 错误 ❌
query = f"SELECT * FROM sys_user WHERE user_name = '{username}'"
```

3. **禁止使用字符串格式化**
```python
# 错误 ❌
query = "SELECT * FROM sys_user WHERE user_name = '%s'" % username
```

4. **禁止直接执行原始 SQL**
```python
# 错误 ❌
await db_session.execute(text(f"SELECT * FROM sys_user WHERE user_name = '{username}'"))
```

## 验收标准

### P0-002: SQL 注入防护测试

- [x] 所有测试用例通过
- [x] 覆盖所有常见注入向量
- [x] 测试数据权限查询安全性
- [x] 测试边界情况
- [x] 文档完整

### 测试通过标准

1. **所有测试用例通过**: 100% 通过率
2. **无安全漏洞**: 所有注入尝试都被安全处理
3. **性能可接受**: 测试执行时间 < 30 秒
4. **代码覆盖率**: 安全相关代码覆盖率 > 90%

## 持续集成

### CI/CD 集成

在 CI/CD 流程中自动运行安全测试：

```yaml
# .github/workflows/security-tests.yml
name: Security Tests

on: [push, pull_request]

jobs:
  security-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      - name: Run security tests
        run: |
          cd ruoyi-fastapi-backend
          pytest tests/unit/security/ -v --cov=module_admin
```

## 安全审计

### 定期审计

建议每月进行一次安全审计：

1. 运行所有安全测试
2. 检查新增代码是否遵循安全最佳实践
3. 更新测试用例覆盖新的攻击向量
4. 审查依赖库的安全漏洞

### 安全检查清单

- [ ] 所有数据库查询使用参数化
- [ ] 没有使用 eval() 或 exec()
- [ ] 没有字符串拼接构建 SQL
- [ ] 所有用户输入都经过验证
- [ ] 敏感数据已加密
- [ ] 日志不包含敏感信息
- [ ] 错误消息不泄露系统信息

## 参考资料

### OWASP Top 10

- [A03:2021 – Injection](https://owasp.org/Top10/A03_2021-Injection/)
- [SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)

### SQLAlchemy 安全

- [SQLAlchemy Security](https://docs.sqlalchemy.org/en/20/faq/security.html)
- [Avoiding SQL Injection Attacks](https://docs.sqlalchemy.org/en/20/core/tutorial.html#using-textual-sql)

### Google 安全标准

- [Google Security Best Practices](https://cloud.google.com/security/best-practices)
- [Secure Coding Practices](https://google.github.io/styleguide/pyguide.html#security)

## 联系方式

如果发现安全漏洞，请立即联系安全团队：
- Email: security@example.com
- 内部工单系统: 创建 P0 安全工单

---

**最后更新**: 2026-01-27  
**维护者**: Backend Security Team
