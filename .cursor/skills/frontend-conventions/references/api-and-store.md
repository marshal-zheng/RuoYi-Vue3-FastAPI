# API and Store Reference

Patterns aligned with the current `ruoyi-fastapi-frontend` codebase.

## 1. API Modules (TypeScript-first)

### File organization

```
src/api/
├── login.ts
├── menu.ts
├── common.ts
├── system/*.ts
├── monitor/*.ts
├── <feature>/*.ts
└── _shared/
```

Use `<feature>` as a placeholder for current business domains. Do not assume fixed feature names.

### Standard CRUD shape

```ts
import request from '@/utils/request';

export function listXxx(query?: Record<string, any>) {
  return request({
    url: '/module/entity/list',
    method: 'get',
    params: query,
  });
}

export function getXxx(id: number | string) {
  return request({
    url: '/module/entity/' + id,
    method: 'get',
  });
}

export function addXxx(data: Record<string, any>) {
  return request({
    url: '/module/entity',
    method: 'post',
    data,
  });
}
```

### Naming conventions

| Operation | Pattern |
|---|---|
| List | `listXxx(query)` |
| Detail | `getXxx(id)` |
| Create | `addXxx(data)` |
| Update | `updateXxx(data)` |
| Delete | `delXxx(id)` |
| Status toggle | `changeXxxStatus(id, status)` |

### Rules

1. Use `@/utils/request` for business requests.
2. Do not add runtime `axios` imports outside `src/utils/request.ts`.
3. Keep API modules thin; business composition belongs in composables/views.

## 2. Request Layer

`src/utils/request.ts` is a compatibility wrapper over `src/utils/http.ts`.

Use:

```ts
import request from '@/utils/request';
```

Optional behavior through custom headers:

- `isToken: false` to skip token injection.
- `silentError: true` to suppress default error message UI.

## 3. Pinia Store Modules

Current modules live in:

```
src/store/modules/
```

Typical responsibilities:

- App-level runtime state
- User/auth state
- Permission/route state
- UI preference state

## 4. Global plugin usage

Through `getCurrentInstance().proxy`:

| API | Example |
|---|---|
| `$modal` | `proxy.$modal.msgSuccess('操作成功')` |
| `$tab` | `proxy.$tab.refreshPage()` |
| `$auth` | `proxy.$auth.hasPermi('system:user:edit')` |
| `useDict` | `const { sys_normal_disable } = proxy.useDict('sys_normal_disable')` |
| `download` | `proxy.download(url, params, filename)` |

## 5. Brownfield rules

1. Match the local module style first (naming, typing strictness, response mapping).
2. For new APIs, default to TypeScript signatures and explicit parameter types.
3. If an existing module already has specialized payload handling, preserve it.
