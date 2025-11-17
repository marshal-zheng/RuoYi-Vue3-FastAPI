<template>
  <zx-select
    v-model="value"
    :options="interfaceTypeOptions"
    v-bind="$attrs"
  />
</template>

<script setup name="InterfaceTypeSelector">
import { computed, useAttrs } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  }
})
const attrs = useAttrs()

const emit = defineEmits(['update:modelValue'])

// 默认总线类型选项
const defaultInterfaceTypeOptions = [
  { label: 'RS422', value: 'RS422' },
  { label: 'RS485', value: 'RS485' },
  { label: 'CAN', value: 'CAN' },
  { label: 'LAN', value: 'LAN' },
  { label: '1553B', value: '1553B' }
]

const interfaceTypeOptions = computed(() => {
  const opts = attrs.options
  return Array.isArray(opts) && opts.length > 0 ? opts : defaultInterfaceTypeOptions
})

const value = computed({
  get: () => props.modelValue,
  set: (v) => {
    emit('update:modelValue', v)
  }
})
</script>

<style lang="less" scoped>
// 可以在这里添加自定义样式
</style>