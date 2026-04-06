# Sensitive Data Standard

This project standardizes sensitive data handling via a single flow:

1. Define encrypted columns using the factory from `utils.sensitive`.
2. Prefer a hash column for equality search and keep deterministic encryption disabled.
3. Query sensitive fields with equality only, never `LIKE`.
4. Rely on automatic decrypt on read and audit masking.
5. Backfill historical rows before switching production traffic.

## Usage

```python
from utils.sensitive import sensitive_equals, sensitive_string_with_hash


class SysUser(...):
    phone, phone_hash = sensitive_string_with_hash('phone', comment='联系电话')
    id_card, id_card_hash = sensitive_string_with_hash('id_card', comment='身份证号')


cond = sensitive_equals(SysUser, 'phone', query.phone)
```

## Migration Checklist

- Increase encrypted column length to `VARCHAR(255)` or larger.
- Add `*_hash` columns for equality lookups.
- Backfill existing plaintext or encrypted values into hash columns.
- Only index fields that are queried with equality.

## Commands

```bash
# Backfill sensitive hashes
python scripts/data_migrations/backfill_sensitive_hash.py
```

历史静态治理脚本已从当前仓库移除，不再作为开发与部署入口保留。

## Config

- `SENSITIVE_DATA_ENABLED`
- `SENSITIVE_DATA_KEY`
- `SENSITIVE_DATA_DETERMINISTIC`
