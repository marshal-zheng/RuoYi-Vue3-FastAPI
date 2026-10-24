<script setup lang="ts">
import { computed, ref, useAttrs, useId, useTemplateRef, watch } from 'vue'
import { equal } from '@zxio/schema-form'
import { ZxJsonTextInput, parseJsonText } from '@zxio/schema-form/fields'

import type { Json } from '@zxio/schema-form'
import type {
  FieldEditState,
  FieldMessage,
  JsonTextEdit,
} from '@zxio/schema-form/fields'

defineOptions({ name: 'JsonSettingsField', inheritAttrs: false })
const props = defineProps<{
  modelValue: Json
  disabled?: boolean
  messages?: readonly FieldMessage[]
}>()
const emit = defineEmits<{
  (event: 'update:modelValue', value: Json): void
  (event: 'edit-state', state: FieldEditState): void
}>()
const attrs = useAttrs()
const input = useTemplateRef<{ focus(): void }>('input')
const messagesId = `json-settings-${useId()}`
// The parent owns only canonical JSON. Unfinished text never replaces that value.
const rawText = ref(JSON.stringify(props.modelValue, null, 2))
const parsed = computed(() => parseJsonText(rawText.value))
const blocking = computed<FieldMessage[]>(() =>
  parsed.value.status === 'valid'
    ? []
    : [
        {
          severity: 'error',
          message:
            parsed.value.status === 'empty'
              ? '请输入 JSON；如需空值，请输入 null'
              : '请输入有效的 JSON',
        },
      ]
)
const visibleMessages = computed(() => [
  ...blocking.value,
  ...(props.messages ?? []),
])
const describedBy = computed(
  () =>
    [attrs['aria-describedby'], visibleMessages.value.length ? messagesId : '']
      .filter(Boolean)
      .join(' ') || undefined
)

function report() {
  emit('edit-state', { blocking: blocking.value })
}
function edit({ text }: JsonTextEdit) {
  rawText.value = text
  if (parsed.value.status === 'valid')
    emit('update:modelValue', parsed.value.value)
  report()
}
watch(
  () => props.modelValue,
  (value) => {
    // Parent echoes and unchanged saves preserve the user's valid formatting.
    if (parsed.value.status === 'valid' && equal(parsed.value.value, value))
      return
    rawText.value = JSON.stringify(value, null, 2)
    report()
  }
)
function validate() {
  report()
  return parsed.value.status === 'valid'
}
defineExpose({ focus: () => input.value?.focus(), validate })
</script>

<template>
  <div data-json-settings>
    <ZxJsonTextInput
      ref="input"
      v-bind="$attrs"
      :text="rawText"
      :disabled="disabled"
      :validate-event="false"
      :aria-invalid="
        visibleMessages.some((message) => message.severity === 'error') ||
        undefined
      "
      :aria-describedby="describedBy"
      @edit="edit"
    />
    <ul v-if="visibleMessages.length" :id="messagesId" aria-live="polite">
      <li
        v-for="(message, index) in visibleMessages"
        :key="index"
        :data-severity="message.severity"
      >
        <code v-if="message.path?.length">{{
          JSON.stringify(message.path)
        }}</code>
        {{ message.message }}
      </li>
    </ul>
  </div>
</template>
