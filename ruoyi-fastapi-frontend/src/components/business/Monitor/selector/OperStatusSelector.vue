<template>
  <zx-select v-model="value" :options="options" :placeholder="placeholder" v-bind="$attrs" />
</template>

<script setup>
const props = defineProps({
  modelValue: [String, Number],
  placeholder: String,
});
const emit = defineEmits(['update:modelValue', 'change']);
const { proxy } = getCurrentInstance();
const { sys_common_status } = proxy.useDict('sys_common_status');
const options = computed(() =>
  (sys_common_status.value || []).map((d) => ({ label: d.label, value: d.value }))
);
const value = computed({
  get: () => props.modelValue,
  set: (v) => {
    emit('update:modelValue', v);
    emit('change', v);
  },
});
</script>
