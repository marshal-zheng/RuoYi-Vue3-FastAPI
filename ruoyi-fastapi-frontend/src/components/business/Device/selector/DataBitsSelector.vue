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
      v-for="option in dataBitsOptions"
      :key="option.value"
      :label="option.label"
      :value="option.value"
    />
  </el-select>
</template>

<script setup name="DataBitsSelector">
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: null
  },
  placeholder: {
    type: String,
    default: '请选择数据位'
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

// 默认数据位选项
const defaultDataBitsOptions = [
  { label: '5', value: 5 },
  { label: '6', value: 6 },
  { label: '7', value: 7 },
  { label: '8', value: 8 }
]

// 计算数据位选项
const dataBitsOptions = computed(() => {
  return props.options || defaultDataBitsOptions
})

function handleChange(value) {
  emit('update:modelValue', value)
  emit('change', value)
}
</script>