<script setup lang="ts">
import { computed, ref, useId } from 'vue'
import { ZxInput } from '@zxio/zxui/input'
import { ZxInputNumber } from '@zxio/zxui/input-number'
import { ZxButton } from '@zxio/zxui/button'

import type { Measurement } from './model'
import type { FieldMessage, FieldPath } from '@zxio/schema-form/fields'

defineOptions({ inheritAttrs: false })
const props = defineProps<{
  modelValue: Measurement[]
  disabled?: boolean
  messages?: readonly FieldMessage[]
}>()
const emit = defineEmits<{
  (e: 'update:modelValue', value: Measurement[]): void
}>()
const fields = ref<Record<string, { focus(): void }>>({})
const readingFields = ref<Record<string, { focus(): void }>>({})
const messagePrefix = useId()
const messagesFor = (index: number, key: string) =>
  props.messages?.filter(
    (message) => message.path?.[0] === index && message.path[1] === key
  ) ?? []
const messageId = (index: number, key: string) =>
  `${messagePrefix}-${index}-${key}`
const summary = computed(
  () =>
    props.messages?.filter((message) => {
      const [index, key] = message.path ?? []
      return (
        typeof index !== 'number' ||
        !props.modelValue[index] ||
        (key !== 'name' && key !== 'reading')
      )
    }) ?? []
)
function edit(id: string, patch: Partial<Measurement>) {
  emit(
    'update:modelValue',
    props.modelValue.map((row) =>
      row.id === id ? { ...row, ...patch } : { ...row }
    )
  )
}
function add() {
  emit('update:modelValue', [
    ...props.modelValue,
    { id: crypto.randomUUID(), name: '', reading: null },
  ])
}
function move(index: number) {
  const next = props.modelValue.map((row) => ({ ...row }))
  ;[next[index - 1], next[index]] = [next[index], next[index - 1]]
  emit('update:modelValue', next)
}
function focusRow(id: string) {
  fields.value[id]?.focus()
}
function focus(path: FieldPath = []) {
  const row = props.modelValue[typeof path[0] === 'number' ? path[0] : 0]
  if (!row) return
  ;(path[1] === 'reading' ? readingFields : fields).value[row.id]?.focus()
}
defineExpose({ focus, focusRow })
</script>

<template>
  <div v-bind="$attrs" class="measurements" data-measurements>
    <ul v-if="summary.length" role="alert">
      <li v-for="(message, index) in summary" :key="index">
        {{ message.message }}
      </li>
    </ul>
    <table>
      <caption>
        检查项读数
      </caption>
      <thead>
        <tr>
          <th>检查项</th>
          <th>读数</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(row, index) in modelValue"
          :key="row.id"
          :data-row-id="row.id"
        >
          <td>
            <ZxInput
              :ref="(value: any) => { if (value) fields[row.id] = value; else delete fields[row.id] }"
              :model-value="row.name"
              :disabled="disabled"
              :validate-event="false"
              :aria-label="`检查项 ${index + 1} 名称`"
              :aria-invalid="messagesFor(index, 'name').length > 0 || undefined"
              :aria-describedby="
                messagesFor(index, 'name').length
                  ? messageId(index, 'name')
                  : undefined
              "
              @update:model-value="
                (value) => edit(row.id, { name: String(value) })
              "
            />
            <p
              v-if="messagesFor(index, 'name').length"
              :id="messageId(index, 'name')"
              role="alert"
            >
              {{
                messagesFor(index, 'name')
                  .map((message) => message.message)
                  .join('；')
              }}
            </p>
          </td>
          <td>
            <ZxInputNumber
              :ref="(value: any) => { if (value) readingFields[row.id] = value; else delete readingFields[row.id] }"
              :model-value="row.reading"
              :disabled="disabled"
              :validate-event="false"
              :aria-label="`检查项 ${index + 1} 读数`"
              :aria-invalid="
                messagesFor(index, 'reading').length > 0 || undefined
              "
              :aria-describedby="
                messagesFor(index, 'reading').length
                  ? messageId(index, 'reading')
                  : undefined
              "
              @update:model-value="
                (value) => edit(row.id, { reading: value ?? null })
              "
            />
            <p
              v-if="messagesFor(index, 'reading').length"
              :id="messageId(index, 'reading')"
              role="alert"
            >
              {{
                messagesFor(index, 'reading')
                  .map((message) => message.message)
                  .join('；')
              }}
            </p>
          </td>
          <td class="row-actions">
            <ZxButton
              :disabled="disabled || index === 0"
              :aria-label="`上移 ${row.name || '检查项'}`"
              @click="move(index)"
              >上移</ZxButton
            >
            <ZxButton
              :disabled="disabled"
              :aria-label="`删除 ${row.name || '检查项'}`"
              @click="
                emit(
                  'update:modelValue',
                  modelValue.filter((item) => item.id !== row.id)
                )
              "
              >删除</ZxButton
            >
          </td>
        </tr>
      </tbody>
    </table>
    <ZxButton :disabled="disabled" data-add-row @click="add"
      >添加检查项</ZxButton
    >
  </div>
</template>
