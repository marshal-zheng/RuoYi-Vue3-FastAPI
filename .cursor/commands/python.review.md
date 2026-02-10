# /python-review - Python Code Review

FastAPI 后端代码全面审查：类型安全、安全漏洞、框架最佳实践。

## Review Checklist

Get changed files: `git diff --name-only HEAD | grep '\.py$'`

For each changed Python file:

**Security (CRITICAL):**
- SQL injection (字符串拼接 SQL、未使用 ORM)
- Command injection (`os.system`、`subprocess` 不安全)
- Hardcoded credentials/tokens
- Sensitive data in logs
- Missing auth decorators (`@require_permission`)
- Unsafe serialization (eval/exec/pickle)

**Type Safety (HIGH):**
- Missing type hints (mypy strict mode)
- FastAPI routes without `response_model`
- Pydantic models without `model_config = ConfigDict(populate_by_name=True)`
- Mutable default arguments

**Database (HIGH):**
- SQLAlchemy N+1 queries (use `joinedload`/`selectinload`)
- Direct `text()` SQL instead of ORM
- Missing soft delete checks (`del_flag`)
- Multi-step ops without transaction manager
- Alembic migrations missing `upgrade()`/`downgrade()`

**Code Quality (MEDIUM):**
- Ruff violations (run: `ruff check .`)
- Format issues (run: `ruff format --check .`)
- `print()` instead of logging
- Sync blocking calls in async functions

## Automated Checks

```bash
cd ruoyi-fastapi-backend

# Type check (strict mode, Python 3.11+)
mypy .

# Lint & format (Ruff replaces black/isort/flake8/pylint)
ruff check .
ruff format --check .

# Tests (target: 15%+ coverage)
pytest --cov=module_admin --cov=utils --cov=config

# Or run all checks
pre-commit run --all-files
```

## Common Fixes

**SQL Injection:**
```python
# ❌ Bad: f"SELECT * FROM users WHERE id = {user_id}"
# ✅ Good: db.query(User).filter(User.user_id == user_id).first()
```

**Type Hints:**
```python
# ❌ Bad: def get_user(user_id):
# ✅ Good: def get_user(self, user_id: int) -> User | None:
```

**FastAPI Response Model:**
```python
# ❌ Bad: @router.get('/users')
# ✅ Good: @router.get('/users', response_model=list[UserVo])
```

**Pydantic Config:**
```python
# ❌ Bad: class UserVo(BaseModel): ...
# ✅ Good: 
class UserVo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
```

**Auto-fix:**
```bash
ruff check --fix .    # Fix linting issues
ruff format .         # Format code
```

## Report Format

Generate report with:
- Severity: CRITICAL, HIGH, MEDIUM
- File:line location
- Issue description + code snippet
- Suggested fix

Block merge if CRITICAL or HIGH issues found.

**Project:** Python >= 3.11, FastAPI + SQLAlchemy + Pydantic