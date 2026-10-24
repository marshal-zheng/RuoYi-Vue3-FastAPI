<script setup lang="ts">
import { computed, ref, useId } from 'vue'
import { ZxInput } from '@zxio/zxui/input'
import { ZxSelect } from '@zxio/zxui/select'
import { ZxButton } from '@zxio/zxui/button'
import { copy } from '@zxio/schema-form'

import type { Values } from '@zxio/schema-form'
import type { FieldMessage, FieldPath } from '@zxio/schema-form/fields'

type Field = {
  id: string
  parentId: null
  fieldName: string
  byteCount: number
  dataType: string
  unit: string
  scale: string
  remark: string
}
const dataTypes = ['UINT8', 'UINT16', 'UINT32'].map((value) => ({
  value,
  label: value,
}))
const byteCounts: Record<string, number> = { UINT8: 1, UINT16: 2, UINT32: 4 }
const props = defineProps<{
  modelValue: Values
  disabled?: boolean
  messages?: readonly FieldMessage[]
}>()
const emit = defineEmits<{
  (event: 'update:modelValue', value: Values): void
}>()
const fields = () => (props.modelValue.fields ?? []) as unknown as Field[]
const controls = ref<Record<string, { focus(): void }>>({})
const messagePrefix = useId()
const rowMessages = (index: number) =>
  props.messages?.filter(
    (message) => message.path?.[0] === 'fields' && message.path[1] === index
  ) ?? []
const summary = computed(
  () =>
    props.messages?.filter(
      (message) =>
        message.path?.[0] !== 'fields' ||
        typeof message.path[1] !== 'number' ||
        !fields()[message.path[1]]
    ) ?? []
)
function focus(path: FieldPath = []) {
  const index =
    path[0] === 'fields' && typeof path[1] === 'number' ? path[1] : 0
  const row = fields()[index]
  if (row) controls.value[row.id]?.focus()
}
defineExpose({ focus })
function update(patch: Values) {
  emit('update:modelValue', { ...copy(props.modelValue), ...patch })
}
function edit(id: string, patch: Partial<Field>) {
  update({
    fields: fields().map((row) =>
      row.id === id ? { ...row, ...patch } : { ...row }
    ),
  })
}
function add() {
  update({
    fields: [
      ...fields(),
      {
        id: crypto.randomUUID(),
        parentId: null,
        fieldName: '',
        byteCount: 1,
        dataType: 'UINT8',
        unit: '',
        scale: '1',
        remark: '',
      },
    ],
  })
}
</script>

<template>
  <div class="protocol-config">
    <ul v-if="summary.length" role="alert">
      <li v-for="(message, index) in summary" :key="index">
        {{ message.message }}
      </li>
    </ul>
    <p>RS422 字段配置：保留已有业务的字段名称、字节数和数据类型结构。</p>
    <div v-for="(row, index) in fields()" :key="row.id" class="protocol-row">
      <label
        >信息名称<ZxInput
          :ref="(value: any) => { if (value) controls[row.id] = value; else delete controls[row.id] }"
          :model-value="row.fieldName"
          :aria-label="`字段 ${index + 1} 名称`"
          :aria-invalid="rowMessages(index).length > 0 || undefined"
          :aria-describedby="
            rowMessages(index).length ? `${messagePrefix}-${index}` : undefined
          "
          :disabled="disabled"
          :validate-event="false"
          @update:model-value="
            (value) => edit(row.id, { fieldName: String(value) })
          "
      /></label>
      <p
        v-if="rowMessages(index).length"
        :id="`${messagePrefix}-${index}`"
        role="alert"
      >
        {{
          rowMessages(index)
            .map((message) => message.message)
            .join('；')
        }}
      </p>
      <label
        >数据类型<ZxSelect
          :model-value="row.dataType"
          :options="dataTypes"
          :disabled="disabled"
          :validate-event="false"
          :aria-label="`字段 ${index + 1} 数据类型`"
          @update:model-value="
            (value) =>
              edit(row.id, {
                dataType: String(value),
                byteCount: byteCounts[String(value)],
              })
          "
      /></label>
      <span>{{ row.byteCount }} 字节</span>
      <ZxButton
        :disabled="disabled"
        :aria-label="`删除字段 ${index + 1}`"
        @click="
          update({ fields: fields().filter((item) => item.id !== row.id) })
        "
        >删除</ZxButton
      >
    </div>
    <ZxButton :disabled="disabled" @click="add">添加协议字段</ZxButton>
    <label
      >附注<ZxInput
        :model-value="String(modelValue.notes ?? '')"
        aria-label="协议附注"
        :disabled="disabled"
        :validate-event="false"
        @update:model-value="(value) => update({ notes: String(value) })"
    /></label>
  </div>
</template>
