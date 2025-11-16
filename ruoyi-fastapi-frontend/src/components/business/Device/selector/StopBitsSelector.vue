<template>
  <el-select
    :model-value="modelValue"
    :placeholder="placeholder"
    :disabled="disabled"
    :clearable="clearable"
    :size="size"
    :style="customStyle"
    @update:model-value="handleChange"
  >
    <el-option
      v-for="option in stopBitsOptions"
      :key="option.value"
      :label="option.label"
      :value="option.value"
    />
  </el-select>
</template>

<script setup name="StopBitsSelector">
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: null
  },
  placeholder: {
    type: String,
    default: '请选择停止位'
  },
  disabled: {
    type: Boolean,
    default: false
  },
  clearable: {
    type: Boolean,
    default: false
  },
  size: {
    type: String,
    default: 'default'
  },
  customStyle: {
    type: Object,
    default: () => ({})
  },
  options: {
    type: Array,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

// 默认停止位选项
const defaultStopBitsOptions = [
  { label: '1', value: 1 },
  { label: '1.5', value: 1.5 },
  { label: '2', value: 2 }
]

// 计算停止位选项
const stopBitsOptions = computed(() => {
  return props.options || defaultStopBitsOptions
})

function handleChange(value) {
  emit('update:modelValue', value)
  emit('change', value)
}
</script>