---
name: frontend-conventions
description: Brownfield-first frontend standards for ruoyi-fastapi-frontend (Vue 3 + Vite + ZXUI). Use when creating or modifying files under ruoyi-fastapi-frontend/src/, including views, components, API modules, store modules, and styles. Enforce project-local patterns before introducing new abstractions.
---

# Frontend Conventions

Coding standards and execution workflow for `ruoyi-fastapi-frontend/`.

## Project Baseline

| Layer | Baseline |
|---|---|
| Framework | Vue 3 + Composition API |
| Build | Vite 5 |
| UI | Element Plus + ZXUI (`@zxio/zxui`) |
| State | Pinia |
| Router | Vue Router 4 |
| Styling | Tailwind CSS v4 + CSS variables + LESS |
| HTTP | `@/utils/request` wrapper |
| Testing | Vitest |

## AI Execution Contract

Follow this order every time:

1. Read nearby code first
- Inspect sibling files in the same module before editing.
- Copy the local pattern (naming, file extensions, import style, dialog/drawer usage).

2. Choose strategy explicitly
- **Brownfield change (default):** Preserve existing structure and behavior.
- **New module/page:** Use TypeScript-first scaffold and componentized pattern.
- Do not run broad refactors unless explicitly requested.

3. Implement minimal, reversible diffs
- Keep scope tied to user request.
- Avoid incidental rewrites (format-only churn, folder-wide renames).

4. Validate before finishing
- Run `bash .cursor/skills/frontend-conventions/scripts/validate.sh --changed`.
- Use `--full --with-tests` for release-level validation.

## Architecture Rules

### New CRUD pages

Recommended structure:

```
src/views/{module}/{entity}/
├── index.vue
└── components/
    ├── index.ts
    ├── XxxList.vue
    └── XxxDialog.vue / XxxDrawer.vue
```

`index.vue` should stay assembly-oriented for new CRUD pages.

### Existing high-orchestration pages

If a page already contains substantial orchestration, keep its current architecture unless the user explicitly asks for refactor.

### Selector components

For reusable business selectors, prefer:

```
components/selector/
├── index.ts (or index.js if module already uses js)
└── XxxSelector.vue
```

Use `zx-select` wrappers for reusable selector behavior.

## File and Naming Rules

1. For **new files**, default to TypeScript (`.ts`, `<script setup lang="ts">`).
2. For **existing modules**, preserve local extension/style conventions unless asked to migrate.
3. Use `@/` alias for src imports; avoid deep relative imports (`../../../`).
4. Keep component names in PascalCase; view directories in kebab-case module paths.

## API and Data Layer Rules

1. Use `@/utils/request` for HTTP calls.
2. Do not add runtime `axios` import outside `src/utils/request.ts`.
3. Place API modules under `src/api/{module}/{entity}.ts`.
4. Keep request functions explicit (`listXxx`, `getXxx`, `addXxx`, `updateXxx`, `delXxx`).

## Styling Rules

1. Prefer Tailwind utility classes for layout and spacing.
2. Prefer CSS variables for color tokens.
3. Do not introduce new hardcoded hex colors in non-token files.
4. Token source files are under `src/assets/styles/` (see references).

## Error Handling and Logging

1. Avoid adding new `console.log/warn/error` in business code.
2. Use UI feedback (`ElMessage`, `proxy.$modal`) where user-visible.
3. Keep catch blocks actionable; do not silently swallow errors.

## Scaffolding

Generate a new CRUD page:

```bash
bash .cursor/skills/frontend-conventions/scripts/new-view.sh <module> <entity>
```

Preview without writing files:

```bash
bash .cursor/skills/frontend-conventions/scripts/new-view.sh --dry-run <module> <entity>
```

## Validation

```bash
# Fast/local iteration (default)
bash .cursor/skills/frontend-conventions/scripts/validate.sh --changed

# Release-level validation
bash .cursor/skills/frontend-conventions/scripts/validate.sh --full --with-tests
```

## ZXUI Guidance

Prefer ZXUI components and composables when possible. When unsure about props/events/slots, query ZXUI docs/tooling before implementation.

## References

| File | Use when |
|---|---|
| [references/component-patterns.md](references/component-patterns.md) | Designing page/component structure and ZXUI composition |
| [references/api-and-store.md](references/api-and-store.md) | Adding/updating API calls or store interactions |
| [references/lint-guard.md](references/lint-guard.md) | Checking lint/type/format constraints and guardrails |
| [references/tailwind-and-theme.md](references/tailwind-and-theme.md) | Styling with Tailwind/CSS variables/theme tokens |
