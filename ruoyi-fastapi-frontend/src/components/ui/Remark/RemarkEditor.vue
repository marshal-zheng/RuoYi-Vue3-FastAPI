<template>
  <ZxTextEditorField
    ref="field"
    v-bind="$attrs"
    :model-value="editorValue"
    :disabled="disabled"
    :ai="ai"
    ai-purpose="remark"
    :content-limits="REMARK_LIMITS"
    @update:model-value="update"
    @focus="emit('focus', $event)"
    @blur="blur"
    @edit-state="editState"
  />
</template>
<script setup lang="ts">
import { computed, nextTick, ref } from 'vue';
import { useFormDisabled, useFormItem } from 'element-plus';
import { ZxTextEditorField, type ZxTextEditorDocument } from '@zxio/text-editor';
import '@zxio/text-editor/style.css';
import { REMARK_LIMITS, type RemarkValue } from './contract';
import { createRemarkAIAdapter } from './ai';
defineOptions({ inheritAttrs: false });
const props = withDefaults(
  defineProps<{
    modelValue: RemarkValue;
    disabled?: boolean;
  }>(),
  { disabled: undefined }
);
const disabled = useFormDisabled();
const ai = createRemarkAIAdapter();
// The generated schema permits optional/null inline arrays; readRemark admits only canonical library documents.
const editorValue = computed(() => props.modelValue as unknown as ZxTextEditorDocument | null);
type RemarkEditState = {
  pending?: boolean;
  blocking?: readonly {
    severity: 'error' | 'warning' | 'info';
    message: string;
  }[];
};
const emit = defineEmits<{
  'update:modelValue': [RemarkValue];
  focus: [FocusEvent];
  blur: [FocusEvent];
  'edit-state': [RemarkEditState];
}>();
const { formItem } = useFormItem();
const field = ref<InstanceType<typeof ZxTextEditorField>>();
const editPending = ref(false);
function validateInteraction(trigger: 'change' | 'blur') {
  // Pending candidate review still blocks submit through validate(), but is not an invalid edit.
  if (!editPending.value) void formItem?.validate(trigger).catch(() => undefined);
}
function editState(state: RemarkEditState) {
  const wasPending = editPending.value;
  editPending.value = !!state.pending;
  emit('edit-state', state);
  // Discarding a candidate does not emit a new value. Revalidate the settled original to clear
  // any pending-state error raised by an explicit submit, after the parent v-model has updated.
  if (wasPending && !editPending.value) void nextTick(() => validateInteraction('change'));
}
function update(value: ZxTextEditorDocument | null) {
  if (disabled.value) return;
  emit('update:modelValue', value as RemarkValue);
  validateInteraction('change');
}
function blur(event: FocusEvent) {
  emit('blur', event);
  validateInteraction('blur');
}
defineExpose({
  focus: () => field.value?.focus(),
  validate: () => field.value?.validate() ?? false,
  captureEdit: () => field.value?.captureEdit() ?? null,
});
</script>
