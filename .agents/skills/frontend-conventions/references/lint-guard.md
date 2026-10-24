# Lint Guard Reference

Guardrails aligned with current frontend configs.

## 1. Tooling sources of truth

- ESLint config: `ruoyi-fastapi-frontend/eslint.config.js`
- TypeScript config: `ruoyi-fastapi-frontend/tsconfig.json`
- Package scripts: `ruoyi-fastapi-frontend/package.json`

## 2. Current command set

```bash
cd ruoyi-fastapi-frontend
yarn lint:check
yarn lint
yarn type-check
yarn test:run
```

Skill helper:

```bash
bash .cursor/skills/frontend-conventions/scripts/validate.sh --changed
bash .cursor/skills/frontend-conventions/scripts/validate.sh --full --with-tests
```

## 3. Key ESLint behavior

Observed from current config:

- `no-console`: `warn`
- `no-debugger`: `warn`
- `@typescript-eslint/no-unused-vars`: `warn`
- `@typescript-eslint/no-explicit-any`: `warn`
- `vue/require-v-for-key`: `error`
- `vue/no-use-v-if-with-v-for`: `error`

### Practical policy for new edits

1. Treat warnings as quality debt; do not add new warnings in changed code.
2. Keep Vue files on `<script setup>` unless editing legacy files under explicit scope.
3. Keep formatting compatible with Prettier settings embedded in ESLint config.

## 4. TypeScript baseline

Current `tsconfig.json` includes:

- `strict: true`
- `noUnusedLocals: true`
- `noUnusedParameters: true`
- `noImplicitReturns: true`
- `allowJs: true` and `checkJs: false` (hybrid migration mode)

### Practical policy

1. New files should be TypeScript-first.
2. Existing JS modules can be edited in place; do not force migration unless requested.
3. Prefer explicit parameter/return types in shared APIs and composables.

## 5. Skill-enforced checks

The skill validation script checks:

1. Lint
2. Type check
3. New hex colors in non-token files
4. Runtime axios imports outside request wrapper
5. Options API regressions in changed Vue files
6. New console usage in business code
