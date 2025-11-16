<template>
  <zx-select v-model="value" :options="options" :placeholder="placeholder" v-bind="$attrs" />
  </template>

<script setup>
const props = defineProps({
  modelValue: [String, Number],
  placeholder: String
})
const emit = defineEmits(['update:modelValue', 'change'])
const { proxy } = getCurrentInstance()
const { sys_oper_type } = proxy.useDict('sys_oper_type')
const options = computed(() => (sys_oper_type.value || []).map(d => ({ label: d.label, value: d.value })))
const value = computed({
  get: () => props.modelValue,
  set: v => {
    emit('update:modelValue', v)
    emit('change', v)
  }
})
</script>