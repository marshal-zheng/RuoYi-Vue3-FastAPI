### src/index.ts
```ts
export { copy, equal } from './json'
export type { Binding, Bindings, CompositeBinding, Json, Values } from './types'
```

### src/types.ts
```ts
import type { Component } from 'vue'

export type Json =
  | null
  | boolean
  | number
  | string
  | Json[]
  | { [key: string]: Json }
export type Values = Record<string, Json>

/** Composite fields opt into messages, edit-state, validation and focus adaptation. */
export interface CompositeBinding {
  component: Component
  composite: true
}
export type Binding = Component | CompositeBinding
export type Bindings = Record<string, Binding>
```

### src/form-create/index.ts
```ts
import '../style.css'

export { default as ZxSchemaForm } from '../SchemaForm.vue'
export { createZxuiBindings, createZxuiDefinitionPolicy } from '../zxui'
export { parseDefinition } from '../definition'
export type {
  ArrayKey,
  BusinessContext,
  DefinitionPolicy,
  FieldPath,
  FormPhase,
  SchemaRule,
  Definition,
  FieldIssue,
  NativeRule,
  RuleFor,
  Save,
  SaveResult,
  SchemaFormInstance,
} from './types'
export type {
  Bindings,
  Binding,
  CompositeBinding,
  Json,
  Values,
} from '../types'
```

### src/form-create/types.ts
```ts
import type { Rule } from '@form-create/element-ui'
import type { Values } from '../types'
import type { FieldPath } from '../fields/types'

export type { Rule as NativeRule } from '@form-create/element-ui'
export type { FieldPath } from '../fields/types'
export type SchemaRule = Rule & { fullWidth?: boolean }
export type RuleFor<T extends object> = Omit<SchemaRule, 'field' | 'value'> & {
  field: Extract<keyof T, string>
  value?: never
}
export interface Definition {
  id: string
  revision: number
  engine: 'form-create@3.3.5'
  contract: 'zxui-schema-form-v1'
  rules: Rule[]
}
/** Import admission is separate from trusted code component registration. */
export type DefinitionPolicy = Record<string, { props: readonly string[] }>
export interface FieldIssue {
  /** Segments address the submitted editing value. Missing/unknown paths are form-level. */
  path?: FieldPath
  message: string
}
export interface ArrayKey {
  /** Path to an array. A numeric segment matches that concrete parent row. */
  path: FieldPath
  /** Stable string/number property on every row; duplicates cannot be safely addressed. */
  key: string
}
export type SaveResult<T extends object = Values> =
  | { ok: true; values?: T }
  | { ok: false; issues: readonly FieldIssue[] }
export type Save<T extends object = Values> = (
  values: T,
  signal: AbortSignal
) => Promise<SaveResult<T>>
export type FormPhase =
  | 'idle'
  | 'validating'
  | 'saving'
  | 'blocked'
  | 'invalid'
  | 'saved'
  | 'error'
export interface BusinessContext<T extends object = Values> {
  read(): T
  /** Record lifetime: reset does not cancel resources initialized once by createRules. */
  signal(): AbortSignal
}
export interface SchemaFormInstance<T extends object = Values> {
  read(): T
  reset(): void
  submit(): Promise<boolean>
  focus(path?: FieldPath): void
  readonly dirty: boolean
  readonly pending: boolean
  readonly fieldPending: boolean
  readonly blocked: boolean
  readonly phase: FormPhase
  readonly status: string
}
```