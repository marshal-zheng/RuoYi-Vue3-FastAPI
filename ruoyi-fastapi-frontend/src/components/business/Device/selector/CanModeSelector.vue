<template>
  <el-radio-group
    :model-value="modelValue"
    :disabled="disabled"
    :size="size"
    :style="customStyle"
    @update:model-value="handleChange"
  >
    <el-radio
      v-for="option in canModeOptions"
      :key="option.value"
      :label="option.value"
    >
      {{ option.label }}
    </el-radio>
  </el-radio-group>
</template>

<script setup name="CanModeSelector">
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: null
  },
  disabled: {
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

// 默认CAN工作模式选项
const defaultCanModeOptions = [
  { label: 'A 模式', value: 'A' },
  { label: 'B 模式', value: 'B' }
]

// 计算CAN工作模式选项
const canModeOptions = computed(() => {
  return props.options || defaultCanModeOptions
})

function handleChange(value) {
  emit('update:modelValue', value)
  emit('change', value)
}
</script>