<template>
  <el-select 
    :model-value="modelValue"
    @update:model-value="handleChange"
    :placeholder="placeholder"
    :style="{ width: '100%', ...customStyle }"
    :disabled="disabled"
    :clearable="clearable"
    :size="size"
  >
    <el-option 
      v-for="option in interfaceTypeOptions" 
      :key="option.value"
      :label="option.label" 
      :value="option.value" 
    />
  </el-select>
</template>

<script setup name="InterfaceTypeSelector">
import { computed } from 'vue'

// Props
const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: '请选择总线类型'
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
    default: () => []
  }
})

// Emits
const emit = defineEmits(['update:modelValue', 'change'])

// 默认总线类型选项
const defaultInterfaceTypeOptions = [
  { label: 'RS422', value: 'RS422' },
  { label: 'RS485', value: 'RS485' },
  { label: 'CAN', value: 'CAN' },
  { label: 'LAN', value: 'LAN' },
  { label: '1553B', value: '1553B' }
]

// 计算最终的选项列表
const interfaceTypeOptions = computed(() => {
  return props.options.length > 0 ? props.options : defaultInterfaceTypeOptions
})

// 处理值变化
const handleChange = (value) => {
  emit('update:modelValue', value)
  emit('change', value)
}
</script>

<style lang="scss" scoped>
// 可以在这里添加自定义样式
</style>