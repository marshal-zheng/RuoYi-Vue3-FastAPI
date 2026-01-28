# Sensitive Data Standard

This project standardizes sensitive data handling via a single flow:

1) Define encrypted columns using the factory from `utils.sensitive`.
2) (Recommended) define a hash column for equality search and disable deterministic encryption.
3) Query sensitive fields with equality only (no `LIKE`).
4) Rely on automatic decrypt on read and audit masking.
5) Run data migration to backfill existing plaintext.

## Usage

Model definition:

```
from utils.sensitive import sensitive_string, sensitive_string_with_hash

class SysUser(...):
    phonenumber = sensitive_string(default='', comment='mobile')
    # or with hash support:
    phone, phone_hash = sensitive_string_with_hash('phone', comment='联系电话')
    id_card, id_card_hash = sensitive_string_with_hash('id_card', comment='身份证号')
```

## Querying

- Use equality filters (`==`, `in_`) only.
- Do not use `LIKE` on encrypted columns.

If a hash column is defined, prefer it:

```
from utils.sensitive import sensitive_equals

cond = sensitive_equals(SysUser, 'phone', query.phone)
```

Encryption can be deterministic to allow equality lookups, which leaks duplicate patterns.
For stronger confidentiality, define a hash column and set `SENSITIVE_DATA_DETERMINISTIC = false`
(run the backfill before switching).
If you need fuzzy search, add a dedicated searchable column (e.g., prefix or token table),
and document it explicitly in the migration.

## Audit Masking

Audit masking merges:
- `AuditConfig.audit_mask_fields`
- All columns declared with `EncryptedString`

So encrypted fields are masked by default without extra config.

## Migration Checklist

- Update column length to accommodate ciphertext (recommend `VARCHAR(255)` or larger).
- Add hash columns for equality search (`*_hash`).
- Backfill existing plaintext/encrypted values into hash columns.
- Add indexes only on fields that will be queried with equality.

Backfill command:

```
python scripts/data_migrate.py
```

Static check:

```
python scripts/check_sensitive_queries.py
```

One-click DB check (columns + backfill):

```
python scripts/check_sensitive_data.py
```

## Config

Environment variables:

- `SENSITIVE_DATA_ENABLED`
- `SENSITIVE_DATA_KEY` (recommended; empty will fallback to `JWT_SECRET_KEY` with a warning)
- `SENSITIVE_DATA_DETERMINISTIC` (set false when using hash columns for equality)
