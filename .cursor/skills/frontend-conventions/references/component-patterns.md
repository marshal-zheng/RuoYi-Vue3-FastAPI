# Component Patterns Reference

ZXUI component usage patterns extracted from actual project views.

---

## Read First

This repository is brownfield. Apply patterns with this priority:

1. Match the existing module structure first.
2. Use this reference to shape new pages/components or targeted refactors.
3. Do not force module-wide architecture migration unless explicitly requested.

---

## 0. Component Architecture Principles

**Default for new CRUD pages: `index.vue` should be an assembly layer.**

Each view's `index.vue` should act as a pure **composition layer** that imports and assembles child components. It should not contain heavy business logic. All functional modules (lists, forms, selectors, etc.) should be extracted into standalone components and composed inside `index.vue` via `<template>`.

For existing high-orchestration pages, preserve current architecture unless the task is an explicit refactor.

### Directory Structure

```
views/{module}/{entity}/
├── index.vue                      # Assembly layer: imports and composes child components
└── components/
    ├── XxxList.vue                # List component (ZxGridList)
    ├── XxxDlg.vue                 # Form dialog (ZxDialog + useDialog)
    ├── XxxDrawer.vue              # Form drawer (ZxDrawer + useDrawer)
    ├── index.ts / index.js        # Barrel export for all components (match module style)
    └── selector/                  # Selector components directory
        ├── index.ts / index.js    # Barrel export for all selectors
        ├── XxxSelector.vue        # Selector wrapped with zx-select
        └── YyySelector.vue
```

### index.vue Assembly Pattern

```vue
<template>
  <ZxContentWrap>
    <XxxList ref="listRef" @edit="handleEdit" />
  </ZxContentWrap>
  <XxxFormDialog ref="formDlgRef" @success="listRef?.refresh()" />
</template>

<script setup>
import { XxxList, XxxFormDialog } from './components';

const listRef = ref();
const formDlgRef = ref();

function handleEdit(row) {
  formDlgRef.value?.open(row.id);
}
</script>
```

### components/index.ts Barrel Export

```typescript
export { default as XxxList } from './XxxList.vue';
export { default as XxxFormDialog } from './XxxFormDialog.vue';
export { default as XxxDrawer } from './XxxDrawer.vue';
export * from './selector';
```

---

## 0.1 Selector Component Convention

All dropdown selectors should be wrapped with `zx-select`, placed under `components/selector/`, and barrel-exported via `selector/index.ts` (or `index.js` for legacy JS-style modules).

### Naming Convention

- Filename: `{BusinessName}Selector.vue` (PascalCase)
- Component name: `{BusinessName}Selector`

### Selector Template

```vue
<template>
  <zx-select
    v-model="selectedValue"
    :options="options"
    :placeholder="placeholder"
    :disabled="disabled"
    :clearable="clearable"
    v-bind="$attrs"
    @change="handleChange"
  />
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: undefined,
  },
  placeholder: {
    type: String,
    default: '请选择',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  clearable: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['update:modelValue', 'change']);

const selectedValue = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
});

const options = [
  { label: 'Option A', value: 'a' },
  { label: 'Option B', value: 'b' },
];

function handleChange(value) {
  emit('change', value);
}
</script>
```

### Async Options (API Fetching)

```vue
<script setup>
import { computed } from 'vue';
import { getXxxOptions } from '@/api/module/entity';

const options = computed(() => {
  return async () => {
    const res = await getXxxOptions();
    return res.map(item => ({ label: item.name, value: item.id }));
  };
});
</script>
```

### Custom Option Rendering

```vue
<template>
  <zx-select v-model="selectedValue" :options="options" v-bind="$attrs" @change="handleChange">
    <template #default="{ option }">
      <div class="flex items-center gap-2">
        <el-icon><component :is="option.icon" /></el-icon>
        <span>{{ option.label }}</span>
        <span class="text-xs text-gray-400">{{ option.extra }}</span>
      </div>
    </template>
  </zx-select>
</template>
```

### selector/index.ts Barrel Export

```typescript
export { default as FileTypeSelector } from './FileTypeSelector.vue';
export { default as StatusSelector } from './StatusSelector.vue';
export { default as NodeSelector } from './NodeSelector.vue';
```

### Using Selectors in Forms

```vue
<el-form-item label="文件类型" prop="fileType">
  <FileTypeSelector v-model="form.fileType" clearable />
</el-form-item>

<el-form-item label="节点" prop="nodeId">
  <NodeSelector v-model="form.nodeId" placeholder="请选择节点" />
</el-form-item>
```

---

## 1. ZxGridList — Paginated Table

Core list component. Manages pagination, loading state, and query internally.

### Props

| Prop | Type | Description |
|------|------|-------------|
| `:load-data` | `(params) => Promise<{data, total}>` | Async data loader |
| `:query-transform` | `(query) => query` | Transform query before sending |
| `:show-pagination` | `boolean` | Show pagination (default true, set false for tree tables) |
| `:load-on-mounted` | `boolean` | Auto-load on mount |

### Slots

| Slot | Scope | Purpose |
|------|-------|---------|
| `#form` | `{ query, loading, refresh, updateState }` | Toolbar + filters |
| `#table` | `{ grid }` | Table (`grid.list`, `grid.loading`) |

### Standard Form Bar Structure

```vue
<template #form="{ query, loading, refresh: handleRefresh, updateState }">
  <div class="zx-grid-form-bar">
    <div class="zx-grid-form-bar__left"></div>
    <div class="zx-grid-form-bar__filters"></div>
    <div class="zx-grid-form-bar__right">
      <ZxSearch v-model="query.name" placeholder="搜索..." :loading="loading"
        search-mode="click"
        @search="() => onSearch({ handleRefresh, updateState })"
        @clear="() => onSearch({ handleRefresh, updateState })" />
    </div>
  </div>
</template>
```

### Filter Change Pattern

```javascript
function onFilterChange(field, value, { handleRefresh, updateState }) {
  updateState({ [field]: value });
  handleRefresh();
}

function onSearch({ handleRefresh, updateState }) {
  updateState('pager.page', 1);
  handleRefresh();
}
```

### Refresh from Outside

```javascript
const gridListRef = ref(null);
gridListRef.value?.refresh();
```

---

## 2. ZxDialog — Form Dialog

Used with `useDialog()` composable from `@zxio/zxui`.

### useDialog() Options

```javascript
import { useDialog } from '@zxio/zxui';

const { state, dialogProps, dialogEvents, open, close, setLoading } = useDialog({
  title: (data) => (data?.id ? '修改' : '添加'),
  width: '600px',
  formRef,
  preValidate: true,
  autoScrollToError: true,
  autoResetForm: true,
  defaultData: () => ({ id: undefined, name: '', status: '0' }),
  onOpen: async () => {},
  onConfirm: async (data) => {
    if (data.id) {
      await updateXxx(data);
    } else {
      await addXxx(data);
    }
    emit('success');
  },
});
```
