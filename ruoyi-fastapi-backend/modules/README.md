# Modules Vertical Slice Skeleton

This package hosts bounded contexts using a vertical-slice layout:

- `modules/<context>/api/`
- `modules/<context>/application/`
- `modules/<context>/domain/`
- `modules/<context>/infrastructure/`
- `modules/<context>/ports.py`
- `modules/<context>/tests/`

## Contexts (P3 baseline)

- `identity`
- `project`
- `simulation`
- `device`
- `protocol`
- `system`
- `codegen`
- `scheduler`

## Naming Rules

1. Context directory names use `snake_case` and domain nouns.
2. Cross-context collaboration must be defined in `ports.py`.
3. `domain/` must not import other contexts' `infrastructure/`.
4. HTTP router adapters stay in `api/`, use-case orchestration stays in `application/`.
5. Infrastructure adapters (repository, external gateway) stay in `infrastructure/`.
6. Tests for a context stay under `modules/<context>/tests/`.
