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
      v-for="option in positionOptions" 
      :key="option.value"
      :label="option.label" 
      :value="option.value" 
    />
  </el-select>
</template>

<script setup name="PositionSelector">
import { computed } from 'vue'

// Props
const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: '请选择端口位置'
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

// 默认位置选项
const defaultPositionOptions = [
  // { label: '顶部', value: 'top' },
  { label: '左侧', value: 'left' },
  { label: '右侧', value: 'right' }
  // { label: '底部', value: 'bottom' },
]

// 计算最终的选项列表
const positionOptions = computed(() => {
  return props.options.length > 0 ? props.options : defaultPositionOptions
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