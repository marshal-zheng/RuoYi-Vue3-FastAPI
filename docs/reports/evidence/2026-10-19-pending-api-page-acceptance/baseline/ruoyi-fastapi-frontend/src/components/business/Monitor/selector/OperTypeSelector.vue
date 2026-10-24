<template>
  <DictSelect
    dict-type="sys_oper_type"
    v-model="value"
    :placeholder="placeholder"
    v-bind="$attrs"
  />
</template>

<script setup>
const props = defineProps({
  modelValue: [String, Number],
  placeholder: String,
});
const emit = defineEmits(['update:modelValue', 'change']);
const value = computed({
  get: () => props.modelValue,
  set: (v) => {
    emit('update:modelValue', v);
    emit('change', v);
  },
});
</script>
