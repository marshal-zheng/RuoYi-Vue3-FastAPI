<template>
  <ZxTextEditorField
    ref="field"
    v-bind="$attrs"
    :model-value="editorValue"
    :disabled="disabled"
    :content-limits="REMARK_LIMITS"
    @update:model-value="update"
    @focus="emit('focus', $event)"
    @blur="blur"
    @edit-state="emit('edit-state', $event)"
  />
</template>
<script setup lang="ts">
import { computed, ref } from 'vue';
import { useFormDisabled, useFormItem } from 'element-plus';
import { ZxTextEditorField, type ZxTextEditorDocument } from '@zxio/text-editor';
import '@zxio/text-editor/style.css';
import { REMARK_LIMITS, type RemarkValue } from './contract';
defineOptions({ inheritAttrs: false });
const props = withDefaults(defineProps<{ modelValue: RemarkValue; disabled?: boolean }>(), {
  disabled: undefined,
});
const disabled = useFormDisabled();
// The generated schema permits optional/null inline arrays; readRemark admits only canonical library documents.
const editorValue = computed(() => props.modelValue as unknown as ZxTextEditorDocument | null);
const emit = defineEmits<{
  'update:modelValue': [RemarkValue];
  focus: [FocusEvent];
  blur: [FocusEvent];
  'edit-state': [
    {
      pending?: boolean;
      blocking?: readonly { severity: 'error' | 'warning' | 'info'; message: string }[];
    },
  ];
}>();
const { formItem } = useFormItem();
const field = ref<InstanceType<typeof ZxTextEditorField>>();
function update(value: ZxTextEditorDocument | null) {
  if (disabled.value) return;
  emit('update:modelValue', value as RemarkValue);
  void formItem?.validate('change').catch(() => undefined);
}
function blur(event: FocusEvent) {
  emit('blur', event);
  void formItem?.validate('blur').catch(() => undefined);
}
defineExpose({
  focus: () => field.value?.focus(),
  validate: () => field.value?.validate() ?? false,
  captureEdit: () => field.value?.captureEdit() ?? null,
  restoreEdit: (draft: unknown) => field.value?.restoreEdit(draft),
});
</script>
