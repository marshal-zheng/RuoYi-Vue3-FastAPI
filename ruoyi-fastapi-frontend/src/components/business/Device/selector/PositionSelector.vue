<template>
  <zx-select
    v-model="value"
    :options="positionOptions"
    v-bind="$attrs"
  />
</template>

<script setup name="PositionSelector">
import { computed, useAttrs } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  }
})
const attrs = useAttrs()

const emit = defineEmits(['update:modelValue'])

const defaultPositionOptions = [
  // { label: '顶部', value: 'top' },
  { label: '左侧', value: 'left' },
  { label: '右侧', value: 'right' }
  // { label: '底部', value: 'bottom' },
]

const positionOptions = computed(() => {
  const opts = attrs.options
  return Array.isArray(opts) && opts.length > 0 ? opts : defaultPositionOptions
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