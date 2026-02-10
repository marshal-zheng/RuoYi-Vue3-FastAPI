# Pattern Map

Use this file to detect local coding patterns before editing.

## 1. Local Pattern Detection Checklist

1. Router pattern
- Open the touched controller and adjacent controllers.
- Reuse existing prefix style, dependency placement, and permission key shape.

2. Service method style
- Inspect nearby service files.
- If methods mostly use `*_services`, keep that style in the same module.
- If methods are verb-style (`create_xxx`, `update_xxx`), keep that style in the same module.

3. Response boundary
- Check whether nearby endpoints wrap service outputs in controller, or service already returns response payloads.
- Preserve existing boundary for that module unless a refactor is explicitly requested.

4. Model naming style
- Check DO/VO class naming used by neighboring files.
- Preserve local class/file naming pattern for consistency.

## 2. Data Access Map

- Active data layer is `module_admin/repository/*` and `BaseRepository`.
- `module_admin/dao/*` still exists mainly for compatibility and tests.
- Policy for new production code: use Repository, do not add new DAO dependencies.

## 3. Foundation Files To Check Before Editing

- App bootstrap and router registration: `ruoyi-fastapi-backend/server.py`
- DB session lifecycle: `ruoyi-fastapi-backend/config/get_db.py`
- ORM base and mixins: `ruoyi-fastapi-backend/module_admin/entity/do/base.py`
- VO base model: `ruoyi-fastapi-backend/module_admin/entity/vo/base.py`
- Exceptions: `ruoyi-fastapi-backend/exceptions/exception.py`
- Global exception handlers: `ruoyi-fastapi-backend/exceptions/handle.py`
- Response contract: `ruoyi-fastapi-backend/utils/response_util.py`
- Transaction decorator: `ruoyi-fastapi-backend/utils/transaction_manager.py`

## 4. Common Compatibility Traps

1. Preserve historical names unless the task asks for migration.
2. `ResponseUtil.success` prefers `message=`; `msg=` is compatibility path.
3. `AppException` family uses `user_message` + `developer_message` fields.
4. `get_db()` commits/rolls back per request; avoid conflicting manual transaction patterns.
5. Schema/DO changes should include migration updates in the same task.

## 5. Recommended Defaults (Only When No Local Pattern Exists)

1. Service write methods use `@transactional()`.
2. Service returns data; controller wraps HTTP response.
3. New data access goes through repository layer.
4. Keep module-level naming consistent once chosen.
